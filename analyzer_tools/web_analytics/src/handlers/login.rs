use axum::{
    extract::{FromRequestParts, State},
    http::{request::Parts, StatusCode},
    response::{IntoResponse, Response},
    routing::post,
    Json, RequestPartsExt, Router,
};
use axum_extra::{
    headers::{authorization::Bearer, Authorization},
    TypedHeader,
};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::sync::LazyLock;
use crate::{
    AppState,
    errors::WebErrors
};


static KEYS: LazyLock<Keys> = LazyLock::new(|| {
    let secret = std::env::var("JWT_SECRET").expect("JWT_SECRET must be set");
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
            .as_secs() as usize + 7200usize
    };

    let token = encode(
        &Header::default(),
        &claims,
        &KEYS.encoding
    ).map_err(|_| WebErrors::TokenCreation)?;


    Ok(AuthBody::new(token))
}



struct Keys {
    encoding: EncodingKey,
    decoding: DecodingKey,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    sub: String,
    exp: usize,
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
        (StatusCode::FOUND, Json(self)).into_response()
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

        Ok(token.claims)
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