import pydantic
import fastapi
import enum
import json

import redis.asyncio as redis


redis_conn_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,
    decode_responses=True,
)

class AsyncRedisConnectionPool:
    def __init__(self):
        self.redis_conn: redis.Redis | None = None

    async def __aenter__(self):
        if self.redis_conn is None:
            self.redis_conn = await redis.Redis(connection_pool=redis_conn_pool)
        return self.redis_conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.redis_conn is not None:
            await self.redis_conn.close()

class Network(str, enum.Enum):
    solana = "solana"
    eth = "eth"
    arbitrum = "arbitrum"
    base = "base"
    bsc = "bsc"

app = fastapi.FastAPI()

api = fastapi.APIRouter(prefix="/api")

@app.get("/")
async def root():
    return "Hello World"

@api.get("/v1/metadata/{network}")
async def metadata(network: Network):
    async with AsyncRedisConnectionPool() as conn:
        pipe = conn.pipeline()

        if network is Network.solana:
            await pipe.get(f"snapshot:metadata:{network.value}:orca:clmm")
            await pipe.get(f"snapshot:metadata:{network.value}:raydium:clmm")
            await pipe.get(f"snapshot:metadata:{network.value}:raydium:amm")
            await pipe.get(f"snapshot:metadata:{network.value}:meteora:dlmm")

        else:
            await pipe.get(f"snapshot:metadata:{network.value}:uniswap:v2")
            await pipe.get(f"snapshot:metadata:{network.value}:uniswap:v3")
            await pipe.get(f"snapshot:metadata:{network.value}:uniswap:v4")

        try:
            raw_data = await pipe.execute()

        except Exception as e:
            raise fastapi.HTTPException(status_code=400, detail=str(e))

    result = {}

    for rd in raw_data:
        if rd is not None:
            result |= json.loads(rd)


    return result


@api.get("/v1/tokens/{network}")
async def token(network: Network):
    async with AsyncRedisConnectionPool() as conn:
        raw_data = await conn.get(f"snapshot:addresses:{network.value}")

        if raw_data is None:
            raise fastapi.HTTPException(status_code=400, detail="Tokens not found")

        return json.loads(raw_data)

app.include_router(api)