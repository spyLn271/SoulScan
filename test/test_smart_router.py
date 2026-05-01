from src.engine.osr import SmartRouter
from src.engine.osr import get_active_metadata, get_active_state
import redis

redis_conn = redis.Redis(decode_responses=True)


metadata = get_active_metadata(redis_connection=redis_conn)
state = get_active_state(redis_connection=redis_conn)

smart_router = SmartRouter(metadata=metadata, state=state)

smart_router.route_expired = 1000000000000000

# So11111111111111111111111111111111111111112/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v


res = smart_router.ExactSwap(
    base_mint="So11111111111111111111111111111111111111112",
    quote_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    delta_amount=1000_000_000_000,
)

print(res)