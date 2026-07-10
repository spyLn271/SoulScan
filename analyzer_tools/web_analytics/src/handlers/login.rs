use axum::{
    extract::{FromRequestParts, State},
    http::{request::Parts, StatusCode, Request},
    response::{IntoResponse, Response},
    routing::post,
    Json, RequestPartsExt, Router,
    body::Body
};
use axum_extra::{
    headers::{authorization::Bearer, Authorization},
    TypedHeader,
};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::sync::LazyLock;
use std::task::{Context, Poll};
use futures_util::future::BoxFuture;
use tower::{Layer, Service};
use crate::{
    AppState,
    errors::WebErrors
};


static KEYS: LazyLock<Keys> = LazyLock::new(|| {
    let secret = "123abc";
    Keys::new(secret.as_bytes())
});

// for tests
const ADMIN: &str = "fuckable";
const SECRET: &str = "not_fuckable";

pub fn routes(app_state: AppState) -> Router {
    Router::new()
        .route("/auth", post(authorize))
        .with_state(app_state)
}

pub async fn authorize(
    State(app_state): State<AppState>,
    Json(payload): Json<AuthPayload>
) -> Result<AuthBody, WebErrors> {
    if payload.name.is_empty() || payload.secret.is_empty() {
        return Err(WebErrors::MissingCredentials)
    };

    // replace with database
    if payload.name != ADMIN || payload.secret != SECRET {
        return Err(WebErrors::WrongCredentials)
    }

    let claims = Claims {
        sub: "admin".to_string(),
        exp: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs() + 7200
    };

    let token = encode(
        &Header::default(),
        &claims,
        &KEYS.encoding
    ).map_err(|_| WebErrors::TokenCreation)?;


    Ok(AuthBody::new(token))
}

#[derive(Clone)]
pub struct AuthLayer {}

#[derive(Clone)]
pub struct AuthService<S> {
    inner: S,
}


struct Keys {
    encoding: EncodingKey,
    decoding: DecodingKey,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: u64,
}

#[derive(Debug, Deserialize)]
pub struct AuthPayload {
    name: String,
    secret: String,
}

#[derive(Debug, Serialize)]
pub struct AuthBody {
    token: String,
    token_type: String,
}


impl IntoResponse for AuthBody{
    fn into_response(self) -> Response {
        (StatusCode::OK, Json(self)).into_response()
    }
}

impl AuthBody {
    pub fn new(token: String) -> AuthBody {
        Self {
            token,
            token_type: "Bearer".to_string()
        }
    }
}


impl<S> Service<Request<Body>> for AuthService<S>
where
    S: Service<Request<Body>, Response = Response> + Clone + Send + 'static,
    S::Future: Send + 'static,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = BoxFuture<'static, Result<Self::Response, Self::Error>>;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, mut req: Request<Body>) -> Self::Future {
        let mut inner = self.inner.clone();

        Box::pin(async move {
            let (mut parts, body) = req.into_parts();

            let Ok(TypedHeader(Authorization(bearer))) = parts
                .extract::<TypedHeader<Authorization<Bearer>>>()
                .await
            else {
                return Ok(WebErrors::InvalidToken.into_response())
            };

            let Ok(token) = decode::<Claims>(
                bearer.token(),
                &KEYS.decoding,
                &Validation::default()
            ) else {
                return Ok(WebErrors::InvalidToken.into_response())
            };

            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs();

            if token.claims.exp < now {
                return Ok(WebErrors::ExpiredToken.into_response())
            }

            let req = Request::from_parts(parts, body);

            inner
                .call(req)
                .await
        })
    }
}

impl<S> Layer<S> for AuthLayer {
    type Service = AuthService<S>;

    fn layer(&self, service: S) -> Self::Service {
        AuthService { inner: service }
    }
}

impl AuthLayer {
    pub fn new() -> Self {
        Self {}
    }
}

impl<S> FromRequestParts<S> for Claims
where
    S: Send + Sync {
    type Rejection = WebErrors;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let TypedHeader(Authorization(bearer)) = parts
            .extract::<TypedHeader<Authorization<Bearer>>>()
            .await
            .map_err(|_| WebErrors::InvalidToken)?;

        let token = decode::<Claims>(bearer.token(), &KEYS.decoding, &Validation::default())
            .map_err(|_| WebErrors::InvalidToken)?;
        
        let claims = token.claims;
        
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        if now > claims.exp {
            return Err(WebErrors::InvalidToken)
        }

        Ok(claims)
    }
}

impl Keys {
    fn new(secret: &[u8]) -> Self {
        Self {
            encoding: EncodingKey::from_secret(secret),
            decoding: DecodingKey::from_secret(secret),
        }
    }
}