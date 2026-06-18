#!/usr/bin/env python
"""
KuCoin Spot Order Book Monitor (Batched Connections) – Fixed endpoint scheme

Changes in this revision:
- Added ensure_ws_scheme() to force wss:// (or ws://) for the websocket endpoint returned by bullet.
- Mask token in logs (avoid leaking full token).
- Added debug log showing normalized websocket URL.
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import websockets
import logging
import gzip
import signal
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Set
import redis.asyncio as redis
import contextlib

# Import config for Redis settings
from src.cex.producer.config import get_redis_config, get_heartbeat_key, get_exchange_config, MONITORING_CONFIG
from src.cex.producer.core.socks5_websocket import connect_with_proxy_config
from src.cex.producer.core.proxy_manager import ProxyManager

# ------------------ Configuration ------------------ #
EXCHANGE_NAME = "kucoin"
REDIS_MARKET_DATA_KEY = f"spot-market-data:{EXCHANGE_NAME}"
ACCEPTABLE_QUOTE_ASSETS = ["USDT", "USDC"]  # only track these quote assets
TOPICS_PER_CONNECTION = 50             # batch size target
SYMBOL_REFRESH_INTERVAL = 10           # seconds

REDIS_ACTIVE_SET = f"symbols_status:{EXCHANGE_NAME}:spot:active_symbols"
REDIS_INACTIVE_SET = f"symbols_status:{EXCHANGE_NAME}:spot:inactive_symbols"
STREAM_KEY_TEMPLATE = "stream:orderbook:kucoin:spot:{raw_symbol}"
STREAM_MAXLEN = 10
FLUSH_INTERVAL = 0.1                   # seconds between pipelined Redis flushes

KUCOIN_BULLET_URL_SPOT = "https://www.kucoin.com/_api/bullet-usercenter/v1/bullet-public"
CONNECT_ID = "connect_welcome"

BASE_RECONNECT_DELAY = 1.0  # base delay in seconds
MAX_RECONNECT_DELAY = 60    # maximum delay in seconds
# Keep symbols active + streams through transient reconnects; only mark inactive +
# delete after this many consecutive failures (the engine trades active∧¬inactive).
CLEANUP_AFTER_FAILURES = MONITORING_CONFIG.get('cleanup_after_failures', 3)

SUCCESSFUL_SUFFIX_JSON_FILE = "successful_suffixes.json"

# Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
MAIN_LOG_FILE = "./app_log/kucoin_spot_batched_app.log"
ERROR_LOG_FILEPATH = "./error_log/kucoin_spot_batched_errors.log"

# Error Queue Configuration
ERROR_QUEUE_KEY_TEMPLATE = "watchdog:{exchange_name}:error_queue"

# ------------------ Global State ------------------ #
redis_client: Optional[redis.Redis] = None
stop_event = asyncio.Event()
shutdown_in_progress = False

symbol_suffix_map: Dict[str, str] = {}        # raw_symbol -> _N
symbol_kucoin_name: Dict[str, str] = {}       # raw_symbol -> BASE-QUOTE
established_successful_suffix_map: Dict[str, str] = {}
current_run_successful_details: List[Tuple[str, str]] = []

batch_workers: Dict[str, asyncio.Task] = {}   # batch_id -> task
batch_symbol_lists: Dict[str, List[str]] = {} # batch_id -> list of raw symbols
active_symbols_global: Set[str] = set()       # global set of active symbols
pending_writes: Dict[str, dict] = {}          # raw_symbol -> latest depth fields (collapse-to-latest, flushed via pipeline)
messages_processed: int = 0                   # cumulative depth msgs (supervisor heartbeat)
monitored_count: int = 0                      # symbols currently monitored (supervisor heartbeat)
last_symbol_update_wall: Dict[str, float] = {}  # raw_symbol -> wall clock of last depth write (stale_symbols metric)
proxy_mgr: Optional[ProxyManager] = None      # SOCKS5 proxy rotation; built in main() if configured
STALE_AGE = 120                               # s; active symbol with no update beyond this counts as "stale" (observability)

success_map_lock = asyncio.Lock()

logger = logging.getLogger("kucoin_spot_batched")

# ------------------ Logging Setup ------------------ #
def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)
    logging.getLogger("websockets").setLevel(logging.INFO)

    # The console handler floods the supervisor's terminal — kucoin runs as a supervisor child
    # whose stdout IS the supervisor's tty, so every INFO line spams the tmux pane and makes the
    # process feel "unstoppable". kucoin already logs to files (below) + a Redis log stream, so the
    # console handler is opt-in for genuine standalone debugging only (set KUCOIN_CONSOLE_LOG=1).
    if os.environ.get("KUCOIN_CONSOLE_LOG"):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        root.addHandler(ch)

    try:
        os.makedirs(os.path.dirname(MAIN_LOG_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(ERROR_LOG_FILEPATH), exist_ok=True)

        fh_main = logging.FileHandler(MAIN_LOG_FILE, mode="a", encoding="utf-8")
        fh_main.setLevel(logging.DEBUG)
        fh_main.setFormatter(formatter)
        root.addHandler(fh_main)

        fh_err = logging.FileHandler(ERROR_LOG_FILEPATH, mode="a", encoding="utf-8")
        fh_err.setLevel(logging.ERROR)
        fh_err.setFormatter(formatter)
        root.addHandler(fh_err)
    except Exception as e:
        print(f"Failed to setup file loggers: {e}", file=sys.stderr)

    logger.info("Logging setup completed. Redis error queue enabled.")

# Skip the import-time setup under pytest: it otherwise creates ./app_log + ./error_log in the CWD and
# attaches DEBUG file handlers to the ROOT logger for the whole test session (so every other plugin's +
# the supervisor's errors landed in a file named "kucoin"). The real producer, run via the supervisor
# (not pytest), still configures logging on import. (Legacy path; retired once kucoin migrates to cex_v2.)
if "pytest" not in sys.modules:
    setup_logging()

# ------------------ Helpers ------------------ #
def ensure_ws_scheme(endpoint: str) -> str:
    """
    Force endpoint to ws/wss scheme.
    KuCoin often returns 'https://ws-web-spot.kucoin.com/' for socket.io endpoints.
    We must convert to 'wss://ws-web-spot.kucoin.com/' for websockets.connect.
    """
    endpoint = endpoint.strip()
    if endpoint.startswith("wss://") or endpoint.startswith("ws://"):
        return endpoint
    if endpoint.startswith("https://"):
        return "wss://" + endpoint[len("https://"):]
    if endpoint.startswith("http://"):
        return "ws://" + endpoint[len("http://"):]
    return "wss://" + endpoint.lstrip('/')

def mask_token(token: str, keep: int = 6) -> str:
    if len(token) <= keep * 2:
        return token
    return token[:keep] + "…" + token[-keep:]

# ------------------ Redis Error Queue ------------------ #
async def log_error_to_redis(source_script: str, exchange: str, affected_symbols: List[str], 
                           error_type: str, error_message: str, traceback_str: str = ""):
    """Log error to Redis error queue"""
    try:
        error_entry = {
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "source_script": source_script,
            "exchange": exchange,
            "affected_symbols": affected_symbols,
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback_str
        }
        
        error_queue_key = ERROR_QUEUE_KEY_TEMPLATE.format(exchange_name=exchange)
        # Bounded push: keep only the most recent N entries to avoid Redis bloat.
        pipe = redis_client.pipeline()
        pipe.lpush(error_queue_key, json.dumps(error_entry, separators=(',', ':')))
        pipe.ltrim(error_queue_key, 0, 4999)
        await pipe.execute()
        logger.debug(f"Logged error to Redis queue: {error_type} for symbols {affected_symbols}")
    except Exception as e:
        logger.error(f"Failed to log error to Redis: {e}")

async def cleanup_error_queue_for_symbols(exchange: str, reconnected_symbols: List[str]):
    """Clean up error queue entries for successfully reconnected symbols"""
    try:
        error_queue_key = ERROR_QUEUE_KEY_TEMPLATE.format(exchange_name=exchange)
        
        # Get all error entries
        error_entries = await redis_client.lrange(error_queue_key, 0, -1)
        
        for entry_str in error_entries:
            try:
                entry = json.loads(entry_str)
                affected_symbols = entry.get("affected_symbols", [])
                
                # If all affected symbols are in the reconnected group, remove this entry
                if affected_symbols and all(sym in reconnected_symbols for sym in affected_symbols):
                    await redis_client.lrem(error_queue_key, 1, entry_str)
                    logger.debug(f"Cleaned up error entry for symbols {affected_symbols}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Invalid error entry format, removing: {e}")
                await redis_client.lrem(error_queue_key, 1, entry_str)
                
    except Exception as e:
        logger.error(f"Error during error queue cleanup: {e}")

# ------------------ Utilities ------------------ #
def coerce_levels_to_floats(levels: List) -> List[List[float]]:
    """Normalize every [price, qty, ...] entry to [float, float] so the
    stream matches the canonical shape produced by base_connector. Drops
    any malformed level rather than poisoning a numeric stream."""
    if not levels:
        return []
    out: List[List[float]] = []
    for level in levels:
        try:
            price = float(level[0])
            qty = float(level[1])
        except (TypeError, ValueError, IndexError):
            continue
        out.append([price, qty])
    return out

def count_decimals(v: Any) -> int:
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        s = f"{v:.16f}".rstrip("0").rstrip(".")
    else:
        s = str(v)
    if "." not in s:
        return 0
    return len(s.split(".", 1)[1])

def derive_suffix(best_bid: Any, best_ask: Any, last_price: Any) -> str:
    return f"_{max(count_decimals(best_bid), count_decimals(best_ask), count_decimals(last_price))}"

def convert_raw_symbol_to_kucoin(raw: str) -> Optional[str]:
    for q in ACCEPTABLE_QUOTE_ASSETS:
        if raw.endswith(q):
            base = raw[:-len(q)]
            if base:
                return f"{base}-{q}"
    return None

async def update_inactive_symbols_in_redis(symbols: List[str], action: str, ctx: str = ""):
    if not symbols:
        return
    try:
        if action == "add":
            await redis_client.sadd(REDIS_INACTIVE_SET, *symbols)
            logger.info(f"[inactive:add]{ctx} {symbols}")
        elif action == "remove":
            await redis_client.srem(REDIS_INACTIVE_SET, *symbols)
            logger.info(f"[inactive:remove]{ctx} {symbols}")
    except Exception as e:
        logger.error(f"Inactive set update error: {e}")

async def delete_streams_for_symbols(symbols: List[str], context: str = ""):
    """Delete Redis streams for given symbols to prevent stale data"""
    for raw_symbol in symbols:
        stream_key = STREAM_KEY_TEMPLATE.format(raw_symbol=raw_symbol)
        try:
            await redis_client.delete(stream_key)
            logger.debug(f"Deleted stream{context}: {stream_key}")
        except Exception as e:
            logger.warning(f"Failed to delete stream {stream_key}: {e}")

# ------------------ Persistence ------------------ #
def load_established_suffixes(filename=SUCCESSFUL_SUFFIX_JSON_FILE) -> Dict[str, str]:
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} established suffix mappings.")
            return data
    except Exception as e:
        logger.error(f"Failed loading suffix file: {e}")
        return {}

def save_established_suffixes(filename=SUCCESSFUL_SUFFIX_JSON_FILE):
    global current_run_successful_details, established_successful_suffix_map
    if current_run_successful_details:
        for sym, suf in current_run_successful_details:
            established_successful_suffix_map[sym] = suf
        current_run_successful_details.clear()
    if not established_successful_suffix_map:
        return
    ordered = dict(sorted(established_successful_suffix_map.items()))
    try:
        with open(filename, "w") as f:
            json.dump(ordered, f, indent=4)
        logger.info(f"Saved {len(ordered)} suffix mappings to {filename}.")
    except Exception as e:
        logger.error(f"Error saving suffix mappings: {e}")

# ------------------ Bullet Token ------------------ #
async def fetch_bullet_token(session: aiohttp.ClientSession) -> Tuple[str, str, int, int]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://www.kucoin.com/trade/BTC-USDT",
        "Accept": "application/json",
        "Origin": "https://www.kucoin.com",
    }
    async with session.post(KUCOIN_BULLET_URL_SPOT, headers=headers, json={}, timeout=15) as resp:
        txt = await resp.text()
        data = json.loads(txt)
        if not data.get("success"):
            raise RuntimeError(f"Bullet token fetch failed: {data}")
        token = data["data"]["token"]
        server = next((s for s in data["data"]["instanceServers"] if s.get("protocol") == "socket.io"),
                      data["data"]["instanceServers"][0])
        # The website socket.io server may omit/null these; default sanely so the
        # downstream arithmetic never hits None.
        ping_i = server.get("pingInterval") or 20000
        ping_t = server.get("pingTimeout") or 10000
        endpoint = ensure_ws_scheme(server["endpoint"])
        logger.debug(f"Fetched bullet token (masked={mask_token(token)}) endpoint={endpoint} pingInterval={ping_i} pingTimeout={ping_t}")
        return token, endpoint, ping_i, ping_t

# ------------------ Frame Parser ------------------ #
def split_frames(raw: str) -> List[str]:
    frames = []
    i = 0
    L = len(raw)
    while i < L:
        if raw.startswith("42[", i):
            start = i + 2
            depth = 0
            j = start
            while j < L:
                c = raw[j]
                if c == "[":
                    depth += 1
                elif c == "]":
                    depth -= 1
                    if depth == 0:
                        frames.append(raw[i:j+1])
                        i = j + 1
                        break
                j += 1
            else:
                frames.append(raw[i:])
                i = L
        elif raw.startswith("40", i):
            frames.append("40")
            i += 2
        elif raw.startswith("0{", i):
            depth = 0
            j = i + 1
            while j < L:
                c = raw[j]
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        frames.append(raw[i:j+1])
                        i = j + 1
                        break
                j += 1
            else:
                frames.append(raw[i:])
                i = L
        elif raw[i] in ("0", "1", "2", "3", "4"):
            frames.append(raw[i])
            i += 1
        else:
            i += 1
    return frames

# ------------------ Batch Worker ------------------ #
async def batch_worker(batch_id: str, symbols: List[str], suffixes: Dict[str, str]):
    """
    One websocket connection handling up to TOPICS_PER_CONNECTION symbols.
    Transport: the `websockets` library via connect_with_proxy_config (python_socks),
    so the connection can egress through the rotating SOCKS5 proxy pool. The bullet
    token is fetched on a short-lived direct aiohttp session (tokens are not IP-bound).
    """
    global messages_processed
    consecutive_failures = 0
    last_error: Optional[Exception] = None

    await redis_client.srem(REDIS_ACTIVE_SET, *symbols)
    await update_inactive_symbols_in_redis(symbols, "add", ctx=f"batch:{batch_id}-init")

    try:
        while not stop_event.is_set() and not shutdown_in_progress:
            ws_conn = None
            ping_task: Optional[asyncio.Task] = None
            try:
                consecutive_failures += 1
                # Bullet token over a short-lived DIRECT session — KuCoin website tokens
                # are not IP-bound (verified live); only the websocket egresses via proxy.
                async with aiohttp.ClientSession() as token_session:
                    token, endpoint, ping_interval, ping_timeout = await fetch_bullet_token(token_session)
                base = endpoint.rstrip('/')
                ws_url = (f"{base}/socket.io/?isPublic=true&isKumex=false&token={token}"
                          f"&format=json&acceptUserMessage=false&connectId={CONNECT_ID}&EIO=3&transport=websocket")

                # SOCKS5 proxy (rotating) via the shared python_socks/websockets helper —
                # the same path gateio/htx/bybit/okx use. None => direct.
                proxy_config = await proxy_mgr.get_connection_params() if proxy_mgr else None
                route = proxy_mgr.current_proxy_label() if proxy_mgr else "direct"
                logger.debug(f"[batch {batch_id}] WebSocket URL: {ws_url.replace(token, mask_token(token))}")
                logger.info(f"[batch {batch_id}] Connecting (failure count: {consecutive_failures}) "
                            f"with {len(symbols)} symbols via {route}.")

                ws_conn = await connect_with_proxy_config(
                    ws_url, proxy_config,
                    open_timeout=20,
                    close_timeout=5,
                    ping_interval=None,   # socket.io heartbeat handled manually below
                    compression=None,
                    extra_headers={       # websockets 12.0 uses extra_headers (NOT additional_headers)
                        "User-Agent": "Mozilla/5.0",
                        "Origin": "https://www.kucoin.com",
                        "Referer": "https://www.kucoin.com/trade/BTC-USDT",
                    },
                )

                open_received = False
                sio_connected = False
                subscribed = False
                last_pong = time.time()
                symbol_subscribed: Set[str] = set()
                topic_map: Dict[str, str] = {}

                async def heartbeat():
                    interval_s = max(ping_interval * 0.9 / 1000, 5)
                    while True:
                        try:
                            await ws_conn.send("2")  # client ping
                        except Exception:
                            break
                        await asyncio.sleep(interval_s)

                async def send_subscribe_for_symbol(raw_symbol: str):
                    kucoin_sym = symbol_kucoin_name[raw_symbol]
                    suffix = suffixes[raw_symbol]
                    topic = f"/spotMarket/level2Depth50:{kucoin_sym}{suffix}"
                    payload_obj = {
                        "id": f"_event__subscribe_{int(time.time()*1000)}",
                        "type": "subscribe",
                        "topic": topic,
                        "privateChannel": False,
                        "response": True
                    }
                    arr_frame = ["bullet", json.dumps(payload_obj, separators=(',', ':'))]
                    frame = "42" + json.dumps(arr_frame, separators=(',', ':'))
                    await ws_conn.send(frame)
                    topic_map[topic] = raw_symbol
                    logger.debug(f"[batch {batch_id}] Sent subscribe {raw_symbol} -> {topic}")

                ping_task = asyncio.create_task(heartbeat())

                # --- Receive Loop (websockets yields str/bytes directly) ---
                async for raw_message in ws_conn:
                    # Any frame proves the socket is alive. KuCoin's website socket.io
                    # endpoint sends NO engine.io ping/pong here (verified live), so the
                    # old "stale unless we received a '3' pong" check false-fired ~22s in
                    # and killed healthy connections. Treat the receive timer as a pure
                    # silence detector.
                    last_pong = time.time()

                    if isinstance(raw_message, bytes):
                        if raw_message.startswith(b'\x1f\x8b'):
                            try:
                                raw_message = gzip.decompress(raw_message).decode()
                            except Exception:
                                try:
                                    raw_message = raw_message.decode()
                                except Exception:
                                    continue
                        else:
                            try:
                                raw_message = raw_message.decode()
                            except Exception:
                                continue

                    for frame in split_frames(raw_message):
                        if not frame:
                            continue
                        t = frame[0]

                        if t == '0' and frame.startswith('0{') and not open_received:
                            open_received = True
                            try:
                                _ = json.loads(frame[1:])
                                await ws_conn.send("40")
                            except Exception as e:
                                logger.warning(f"[batch {batch_id}] Open parse error: {e}")

                        elif frame == "40" and not sio_connected:
                            sio_connected = True
                            logger.info(f"[batch {batch_id}] Socket.IO connected.")
                            if not subscribed:
                                for rs in symbols:
                                    await send_subscribe_for_symbol(rs)
                                    await asyncio.sleep(0.01)
                                subscribed = True

                        elif frame.startswith("42"):
                            try:
                                arr = json.loads(frame[2:])
                                if not isinstance(arr, list) or len(arr) < 2:
                                    continue
                                if arr[0] != "bullet":
                                    continue
                                payload = json.loads(arr[1])
                                mtype = payload.get("type")
                                topic = payload.get("topic")
                                
                                # Check for subscription errors
                                if mtype == "error" or (payload.get("error") and payload.get("code")):
                                    error_msg = payload.get("data", {}).get("message", "Unknown subscription error")
                                    error_code = payload.get("code", "unknown")
                                    await log_error_to_redis(
                                        source_script="redis-kuc.py",
                                        exchange=EXCHANGE_NAME,
                                        affected_symbols=symbols,
                                        error_type="SubscriptionError",
                                        error_message=f"Code {error_code}: {error_msg}",
                                        traceback_str=json.dumps(payload, separators=(',', ':'))
                                    )
                                    continue

                                if mtype == "ack":
                                    raw_symbol = topic_map.get(topic)
                                    if raw_symbol and raw_symbol not in symbol_subscribed:
                                        symbol_subscribed.add(raw_symbol)
                                        await redis_client.sadd(REDIS_ACTIVE_SET, raw_symbol)
                                        await update_inactive_symbols_in_redis([raw_symbol], "remove",
                                                                                ctx=f"batch:{batch_id}-ack")
                                        established_successful_suffix_map[raw_symbol] = suffixes[raw_symbol]
                                        active_symbols_global.add(raw_symbol)
                                        # NOTE: do NOT clean the error queue here. It reads the whole
                                        # (capped) queue per symbol; doing that on first data for ~944
                                        # symbols at startup stalled the receive loop and built a multi-
                                        # minute backlog. The queue is bounded by LTRIM, so stale entries
                                        # rotate out on their own.
                                        consecutive_failures = 0

                                elif mtype == "message" and topic and "level2Depth50" in topic:
                                    raw_symbol = topic_map.get(topic)
                                    if not raw_symbol:
                                        continue
                                    if raw_symbol not in symbol_subscribed:
                                        symbol_subscribed.add(raw_symbol)
                                        await redis_client.sadd(REDIS_ACTIVE_SET, raw_symbol)
                                        await update_inactive_symbols_in_redis([raw_symbol], "remove",
                                                                                ctx=f"batch:{batch_id}-data")
                                        active_symbols_global.add(raw_symbol)
                                        # NOTE: error-queue cleanup intentionally NOT done here — see the
                                        # ack branch above (per-symbol full-queue reads stalled startup).
                                        consecutive_failures = 0

                                    data_obj = payload.get("data", {})
                                    bids = coerce_levels_to_floats(data_obj.get("bids", []))
                                    asks = coerce_levels_to_floats(data_obj.get("asks", []))
                                    sequence = data_obj.get("sequence", "")
                                    ts = data_obj.get("timestamp") or int(time.time() * 1000)
                                    kucoin_name = symbol_kucoin_name[raw_symbol]

                                    msg_fields = {
                                        "symbol": kucoin_name,
                                        "timestamp_ms": str(ts),
                                        "update_id": str(sequence),
                                        "bids": json.dumps(bids, separators=(',', ':')),
                                        "asks": json.dumps(asks, separators=(',', ':'))
                                    }
                                    # Collapse-to-latest: update this symbol's pending snapshot
                                    # (non-blocking) instead of awaiting an xadd here. redis_flush_loop
                                    # pipelines the pending snapshots every FLUSH_INTERVAL. This keeps
                                    # the receive loop from blocking on Redis I/O and drops stale
                                    # intermediate snapshots (level2Depth50 is a full snapshot — only
                                    # the newest matters). The old awaited-xadd-per-message capped
                                    # drain throughput to ~the incoming rate, so any hiccup built a
                                    # permanent multi-minute delay (book content minutes behind the
                                    # exchange while still being written fresh).
                                    pending_writes[raw_symbol] = msg_fields
                                    messages_processed += 1  # supervisor heartbeat counter
                                    last_symbol_update_wall[raw_symbol] = time.time()  # stale_symbols metric
                            except Exception as e:
                                logger.error(f"[batch {batch_id}] Event parse error: {e}")

                        elif t == '3':
                            last_pong = time.time()

                        elif t == '2':
                            await ws_conn.send('3')

                        elif t == '1':
                            logger.info(f"[batch {batch_id}] Server close frame.")
                            raise ConnectionError("Server closed connection.")

                    if (time.time() - last_pong) * 1000 > (ping_interval + 2000):
                        raise TimeoutError("Ping timeout exceeded.")

            except asyncio.CancelledError:
                logger.warning(f"[batch {batch_id}] Worker cancelled.")
                break
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)[:200]
                logger.warning(f"[batch {batch_id}] Error ({error_type}): {error_msg}")
                
                # Log error to Redis queue
                await log_error_to_redis(
                    source_script="redis-kuc.py",
                    exchange=EXCHANGE_NAME,
                    affected_symbols=symbols,
                    error_type=error_type,
                    error_message=error_msg
                )
                
                # Keep symbols active + streams intact through transient reconnects; only
                # mark inactive + delete after sustained failure (engine trades active∧¬inactive).
                if consecutive_failures >= CLEANUP_AFTER_FAILURES:
                    await redis_client.srem(REDIS_ACTIVE_SET, *symbols)
                    await update_inactive_symbols_in_redis(symbols, "add", ctx=f"batch:{batch_id}-err")
                    await delete_streams_for_symbols(symbols, context=f" [batch:{batch_id}-err]")

                # Rotate to a different proxy before reconnecting; demote a persistently
                # failing proxy after repeated errors (mirrors base_connector behaviour).
                if proxy_mgr:
                    await proxy_mgr.rotate_on_disconnect()
                    if consecutive_failures >= 3:
                        await proxy_mgr.handle_connection_failure(error_type, None)

                # Progressive backoff delay - never give up reconnecting
                delay = min(BASE_RECONNECT_DELAY * consecutive_failures, MAX_RECONNECT_DELAY)
                logger.info(f"[batch {batch_id}] Retrying in {delay}s (failure #{consecutive_failures})")
                await asyncio.sleep(delay)
            finally:
                if ping_task and not ping_task.done():
                    ping_task.cancel()
                if ws_conn is not None:
                    with contextlib.suppress(Exception):
                        await ws_conn.close()
                    
    finally:
        # Guaranteed stream cleanup on task termination
        logger.info(f"[batch {batch_id}] Performing guaranteed cleanup for {len(symbols)} symbols")
        
        try:
            # 1. Update central Redis state - move symbols to inactive
            if symbols:
                await redis_client.srem(REDIS_ACTIVE_SET, *symbols)
                await redis_client.sadd(REDIS_INACTIVE_SET, *symbols)
                
            # 2. Delete Redis data streams
            await delete_streams_for_symbols(symbols, context=f" [batch:{batch_id}-cleanup]")
                
            # 3. Update internal script state
            for raw_symbol in symbols:
                active_symbols_global.discard(raw_symbol)
                
        except Exception as cleanup_error:
            logger.error(f"[batch {batch_id}] Cleanup error: {cleanup_error}")

        logger.info(f"[batch {batch_id}] Worker terminated. Last error: {type(last_error).__name__ if last_error else 'N/A'}")

# ------------------ Batch Management ------------------ #
def build_batches(symbols: List[str], batch_size: int) -> List[List[str]]:
    return [symbols[i:i+batch_size] for i in range(0, len(symbols), batch_size)]

async def rebuild_batches(all_symbols: List[str]):
    logger.info(f"Rebuilding batches for {len(all_symbols)} symbols...")
    for bid, task in list(batch_workers.items()):
        if not task.done():
            task.cancel()
    await asyncio.gather(*batch_workers.values(), return_exceptions=True)
    batch_workers.clear()
    batch_symbol_lists.clear()

    if not all_symbols:
        logger.info("No symbols to build batches.")
        return

    batches = build_batches(all_symbols, TOPICS_PER_CONNECTION)
    expected_batches = len(batches)
    for idx, sym_list in enumerate(batches):
        batch_id = f"B{idx+1}"
        try:
            batch_symbol_lists[batch_id] = sym_list
            # Use .get() with default suffix '_4' to prevent KeyError if symbol missing from map
            suffixes = {s: symbol_suffix_map.get(s, '_4') for s in sym_list}
            task = asyncio.create_task(batch_worker(batch_id, sym_list, suffixes))
            batch_workers[batch_id] = task
            logger.info(f"Started batch {batch_id} with {len(sym_list)} symbols.")
        except Exception as e:
            logger.error(f"Failed to create batch {batch_id}: {e}")
            # Continue creating other batches instead of stopping

    # Verify all batches were created
    actual_batches = len(batch_workers)
    if actual_batches < expected_batches:
        logger.error(f"Batch creation incomplete: expected {expected_batches}, got {actual_batches}")

def count_dead_workers() -> int:
    """Count workers that have finished (crashed/exited)"""
    return sum(1 for task in batch_workers.values() if task.done())

async def restart_dead_workers() -> bool:
    """Restart any workers that have crashed without triggering full rebuild"""
    dead_batch_ids = [bid for bid, task in batch_workers.items() if task.done()]
    if not dead_batch_ids:
        return False

    logger.warning(f"Found {len(dead_batch_ids)} dead workers: {dead_batch_ids}")

    for batch_id in dead_batch_ids:
        sym_list = batch_symbol_lists.get(batch_id, [])
        if sym_list:
            try:
                # Use default suffix '_4' if symbol not in map
                suffixes = {s: symbol_suffix_map.get(s, '_4') for s in sym_list}
                task = asyncio.create_task(batch_worker(batch_id, sym_list, suffixes))
                batch_workers[batch_id] = task
                logger.info(f"Restarted dead worker {batch_id} with {len(sym_list)} symbols")
            except Exception as e:
                logger.error(f"Failed to restart worker {batch_id}: {e}")
        else:
            logger.warning(f"Cannot restart worker {batch_id}: no symbol list found in batch_symbol_lists")

    return True

# ------------------ Symbol Monitor ------------------ #
async def monitor_symbols_loop():
    global symbol_suffix_map, symbol_kucoin_name, monitored_count
    previous_symbol_set: Set[str] = set()
    previous_suffixes: Dict[str, str] = {}

    while not stop_event.is_set():
        try:
            fields = await redis_client.hgetall(REDIS_MARKET_DATA_KEY)
            if not fields:
                logger.warning(f"Redis hash '{REDIS_MARKET_DATA_KEY}' empty.")
                current_symbols: Set[str] = set()
            else:
                filtered = [s for s in fields.keys() if any(s.endswith(q) for q in ACCEPTABLE_QUOTE_ASSETS)]
                current_symbols = set(filtered)

            added = current_symbols - previous_symbol_set
            removed = previous_symbol_set - current_symbols

            new_suffix_map: Dict[str, str] = {}
            any_suffix_change = False

            for raw_symbol in current_symbols:
                value_json = fields.get(raw_symbol)
                best_bid = best_ask = last_price = None
                if value_json:
                    try:
                        obj = json.loads(value_json)
                        best_bid = obj.get("best_bid")
                        best_ask = obj.get("best_ask")
                        last_price = obj.get("lastPrice")
                    except Exception:
                        pass
                suffix = derive_suffix(best_bid, best_ask, last_price)
                new_suffix_map[raw_symbol] = suffix
                old_suffix = previous_suffixes.get(raw_symbol)
                if old_suffix and old_suffix != suffix:
                    any_suffix_change = True
                if raw_symbol not in symbol_kucoin_name:
                    kc_name = convert_raw_symbol_to_kucoin(raw_symbol)
                    if kc_name:
                        symbol_kucoin_name[raw_symbol] = kc_name
                    else:
                        current_symbols.discard(raw_symbol)

            monitored_count = len(current_symbols)

            if added or removed:
                symbol_suffix_map = new_suffix_map
                previous_suffixes = new_suffix_map.copy()
                previous_symbol_set = current_symbols.copy()
                await rebuild_batches(sorted(list(current_symbols)))
                # Also check for dead workers after rebuild in case rebuild partially failed
                await restart_dead_workers()
            else:
                symbol_suffix_map = new_suffix_map
                previous_suffixes = new_suffix_map.copy()
                previous_symbol_set = current_symbols.copy()

                # Check for dead workers and restart them
                await restart_dead_workers()

            # Periodic health check logging
            alive_count = sum(1 for t in batch_workers.values() if not t.done())
            dead_count = sum(1 for t in batch_workers.values() if t.done())
            if batch_workers:
                logger.info(f"Batch health: {alive_count} alive, {dead_count} dead, {len(batch_symbol_lists)} expected")

        except asyncio.CancelledError:
            logger.info("Symbol monitor cancelled.")
            break
        except Exception as e:
            logger.error(f"Symbol monitor error: {e}", exc_info=True)

        await asyncio.sleep(SYMBOL_REFRESH_INTERVAL)

# ------------------ Graceful Shutdown Handler ------------------ #
async def global_shutdown_cleanup():
    """Centralized cleanup function for graceful shutdown"""
    global shutdown_in_progress
    shutdown_in_progress = True
    
    logger.info("Starting global shutdown cleanup...")
    
    try:
        # 1. Cancel all running batch workers
        for batch_id, task in list(batch_workers.items()):
            if not task.done():
                logger.info(f"Cancelling batch worker: {batch_id}")
                task.cancel()
        
        # Wait for all workers to complete
        if batch_workers:
            await asyncio.gather(*batch_workers.values(), return_exceptions=True)
        
        # 2. Delete all data streams for active symbols
        if active_symbols_global:
            logger.info(f"Deleting {len(active_symbols_global)} active data streams...")
            await delete_streams_for_symbols(list(active_symbols_global), context=" [shutdown]")
        
        # 3. Atomically move all symbols from active to inactive
        if active_symbols_global:
            logger.info(f"Moving {len(active_symbols_global)} symbols to inactive set...")
            for raw_symbol in active_symbols_global:
                await redis_client.smove(REDIS_ACTIVE_SET, REDIS_INACTIVE_SET, raw_symbol)
        
        logger.info("Global shutdown cleanup completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during global shutdown cleanup: {e}")

def signal_handler(signum, frame):
    """Signal handler for graceful shutdown"""
    logger.warning(f"Received signal {signum}. Initiating graceful shutdown...")
    stop_event.set()

# ------------------ Main Loop ------------------ #
def print_summary():
    logger.info("\n" + "=" * 30 + " SUMMARY " + "=" * 30)
    logger.info(f"Active batch workers: {len(batch_workers)}")
    total_symbols = sum(len(v) for v in batch_symbol_lists.values())
    logger.info(f"Total symbols assigned across batches: {total_symbols}")
    logger.info(f"Established suffix map size: {len(established_successful_suffix_map)}")
    logger.info("=" * 70)

async def write_heartbeat_loop():
    """Publish the supervisor heartbeat so cex_supervisor does not treat kucoin as
    dead. The supervisor reads health:kucoin:spot:* via src/cex/health.evaluate_pair
    (ts/msgs/active_symbols); without it the connector was restart-looped."""
    key = get_heartbeat_key(EXCHANGE_NAME, "spot", None)  # health:kucoin:spot:none
    while not stop_event.is_set():
        try:
            now = time.time()
            stale = sum(1 for s in active_symbols_global
                        if now - last_symbol_update_wall.get(s, 0) > STALE_AGE)
            payload = {
                "ts": int(now * 1000),
                "msgs": messages_processed,
                "active_symbols": len(active_symbols_global),
                "monitored_symbols": monitored_count,
                "stale_symbols": stale,
                "monitoring_healthy": True,
                "current_proxy": proxy_mgr.current_proxy_label() if proxy_mgr else "direct",
                "proxy_rotations": proxy_mgr.rotations if proxy_mgr else 0,
                "worker_id": "none",
                "schema_version": 1,
            }
            await redis_client.set(key, json.dumps(payload), ex=60)
        except Exception as e:
            logger.debug(f"heartbeat write failed: {e}")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=15)
            break
        except asyncio.TimeoutError:
            continue


async def redis_flush_loop():
    """Pipeline the latest pending depth snapshot per symbol to Redis every
    FLUSH_INTERVAL. Decouples the websocket receive loops from Redis I/O (so a slow
    Redis moment can never back up the sockets into a permanent lag) and drops stale
    intermediate snapshots (only the newest snapshot per symbol is written)."""
    while not stop_event.is_set():
        try:
            await asyncio.sleep(FLUSH_INTERVAL)
            if not pending_writes:
                continue
            batch = dict(pending_writes)   # atomic snapshot (no await between)
            pending_writes.clear()
            pipe = redis_client.pipeline(transaction=False)
            for raw_symbol, fields in batch.items():
                pipe.xadd(
                    STREAM_KEY_TEMPLATE.format(raw_symbol=raw_symbol),
                    fields, id="*", maxlen=STREAM_MAXLEN, approximate=True,
                )
            await pipe.execute()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Redis flush failed: {e}")


async def main():
    global redis_client, established_successful_suffix_map, proxy_mgr
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("KuCoin Batched Spot Monitor starting up...")

    # Use config-based Redis connection for consistency with other plugins
    redis_config = get_redis_config()
    redis_client = redis.Redis(
        host=redis_config['host'],
        port=redis_config['port'],
        db=redis_config.get('db', 0),
        password=redis_config.get('password'),
        decode_responses=True
    )
    try:
        await redis_client.ping()
        logger.info(f"Connected to Redis at {redis_config['host']}:{redis_config['port']}")
    except Exception as e:
        logger.critical(f"Cannot connect to Redis: {e}")
        return

    established_successful_suffix_map = load_established_suffixes()

    # Build the rotating SOCKS5 proxy manager if kucoin has proxy enabled in config.
    pcfg = (get_exchange_config(EXCHANGE_NAME) or {}).get("proxy", {})
    if pcfg.get("use_proxy"):
        proxy_mgr = ProxyManager(EXCHANGE_NAME, pcfg)
        logger.info(f"KuCoin proxy enabled: mode={pcfg.get('mode')}")
    else:
        logger.info("KuCoin proxy disabled (use_proxy=False); connecting direct.")

    while not stop_event.is_set():
        try:
            with contextlib.suppress(Exception):
                await redis_client.delete(REDIS_ACTIVE_SET)

            monitor_task = asyncio.create_task(monitor_symbols_loop())
            heartbeat_task = asyncio.create_task(write_heartbeat_loop())
            flush_task = asyncio.create_task(redis_flush_loop())
            logger.info("Symbol monitor started.")
            logger.info(f"KuCoin batched monitor active. Batch size={TOPICS_PER_CONNECTION}.")

            # Wait for stop_event to be set (from signal handler or other reasons)
            stop_wait_task = asyncio.create_task(stop_event.wait())

            done, pending = await asyncio.wait(
                [monitor_task, stop_wait_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            logger.warning("Shutdown or monitor exit detected. Initiating cleanup...")

            for p in pending:
                p.cancel()

            if not monitor_task.done():
                monitor_task.cancel()
            heartbeat_task.cancel()
            flush_task.cancel()
            await asyncio.gather(monitor_task, heartbeat_task, flush_task, return_exceptions=True)

            # Perform graceful shutdown cleanup
            await global_shutdown_cleanup()
            
            save_established_suffixes()

            if stop_wait_task in done:
                logger.info("Graceful shutdown completed.")
                break
            else:
                logger.critical("Monitor ended unexpectedly. Restarting in 15s.")
                await asyncio.sleep(15)

            logger.info("Restarting main supervision loop in 5s.")
            await asyncio.sleep(5)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.critical(f"Main loop error: {e}", exc_info=True)
            await asyncio.sleep(10)
    
    # Close Redis connection
    if redis_client:
        await redis_client.close()

# ------------------ Entry Point ------------------ #
def main_entry_point():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.critical(f"FATAL ERROR: {e}", exc_info=True)
    finally:
        print_summary()
        save_established_suffixes()
        logger.info("Execution finished.")


class KucoinSpotConnector:
    """Adapter so the cex supervisor can spawn kucoin the same way it spawns
    BaseExchangeConnector subclasses. This plugin predates the plugin
    architecture and keeps its own WebSocket / Redis lifecycle in main()."""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        self.worker_id = worker_id
        self.num_workers = num_workers

    async def start(self):
        await main()


if __name__ == "__main__":
    main_entry_point()
