"""Gate.io wsbridge plugin: stateless full-snapshot parse (v3 spot depth.update / v4 futures.order_book),
nested-array batched spot subscribe + per-contract futures subscribe, native-tick merge, BTC_USDT<->BTCUSDT,
and futures CONTRACT->base scaling (x quanto_multiplier)."""
import asyncio
import json

from src.cex.plugins.gateio import GateioSpotConnector, GateioFuturesConnector


class _WS:
    def __init__(self):
        self.sent = []

    async def send(self, m):
        self.sent.append(m)


def _spot():
    c = GateioSpotConnector(); c.depth_level = 30; c.sub_delay = 0; return c


def _fut():
    c = GateioFuturesConnector(); c.depth_level = 30; c.sub_delay = 0; return c


def test_normalize_and_wire():
    c = _spot()
    assert c.normalize_symbol("BTC_USDT") == "BTCUSDT"
    assert c.normalize_symbol("BTCUSDT") == "BTCUSDT"
    assert c._wire("BTCUSDT") == "BTC_USDT"
    assert c._wire("1000SHIBUSDT") == "1000SHIB_USDT"
    assert c._wire("ETHUSDC") == "ETH_USDC"


def test_spot_subscribe_nested_batch_with_native_tick():
    c = _spot(); ws = _WS()
    c._tick = {"BTCUSDT": "0.1", "DOGEUSDT": "0.00001"}
    asyncio.run(c.subscribe(ws, ["BTCUSDT", "DOGEUSDT", "NOTICKUSDT"]))
    assert len(ws.sent) == 1                                 # ONE nested-array depth.subscribe (batched)
    msg = json.loads(ws.sent[0])
    assert msg["method"] == "depth.subscribe"
    assert msg["params"] == [["BTC_USDT", 30, "0.1"], ["DOGE_USDT", 30, "0.00001"]]  # NOTICK skipped


def test_futures_subscribe_per_contract_native_tick():
    c = _fut(); ws = _WS()
    c._tick = {"BTCUSDT": "0.1"}
    asyncio.run(c.subscribe(ws, ["BTCUSDT", "NOTICKUSDT"]))
    assert len(ws.sent) == 1                                 # one subscribe per contract; NOTICK skipped
    msg = json.loads(ws.sent[0])
    assert msg["channel"] == "futures.order_book" and msg["event"] == "subscribe"
    assert msg["payload"] == ["BTC_USDT", "30", "0.1"]


def test_spot_parse_full_snapshot_base_asset():
    c = _spot()
    frame = {"method": "depth.update", "params": [True,
             {"bids": [["100", "5"], ["99", "3"]], "asks": [["101", "4"], ["102", "1"]], "update": 1781861561.033},
             "BTC_USDT"]}
    b = c.parse(json.dumps(frame))[0]
    assert b.symbol == "BTCUSDT" and b.event_ts_ms == 1781861561033
    assert b.bids[0] == ["100", "5"] and b.asks[0] == ["101", "4"]   # base-asset, unchanged, ordered


def test_futures_parse_scales_contracts_by_quanto():
    c = _fut(); c._mult = {"BTCUSDT": 0.0001}
    frame = {"channel": "futures.order_book", "event": "all",
             "result": {"contract": "BTC_USDT", "t": 123,
                        "bids": [{"p": "100", "s": 39968}], "asks": [{"p": "101", "s": 14}]}}
    b = c.parse(json.dumps(frame))[0]
    assert b.symbol == "BTCUSDT" and b.event_ts_ms == 123
    assert b.bids[0] == ["100", 39968 * 0.0001] and b.asks[0] == ["101", 14 * 0.0001]


def test_futures_parse_raw_when_no_mult():
    c = _fut()
    frame = {"channel": "futures.order_book", "event": "all",
             "result": {"contract": "ETH_USDT", "bids": [{"p": "3000", "s": 10}], "asks": [{"p": "3001", "s": 5}]}}
    b = c.parse(json.dumps(frame))[0]
    assert b.bids[0] == ["3000", 10] and b.asks[0] == ["3001", 5]


def test_topn_orders_and_drops_bad():
    c = _spot()
    frame = {"method": "depth.update", "params": [True,
             {"bids": [["99", "3"], ["100", "5"], ["x", "9"]], "asks": [["102", "1"], ["101", "4"]]},
             "BTC_USDT"]}
    b = c.parse(json.dumps(frame))[0]
    assert b.bids[0] == ["100", "5"]    # highest first despite input order; non-numeric "x" dropped
    assert b.asks[0] == ["101", "4"]    # lowest first


def test_parse_rejects_crossed_acks_and_wrong_envelope():
    c = _spot()
    crossed = {"method": "depth.update", "params": [True, {"bids": [["101", "1"]], "asks": [["100", "1"]]}, "BTC_USDT"]}
    assert c.parse(json.dumps(crossed)) is None
    assert c.parse(json.dumps({"method": "server.pong", "id": 1})) is None
    assert c.parse(json.dumps({"channel": "futures.order_book", "event": "all", "result": {"contract": "BTC_USDT"}})) is None
    f = _fut()
    assert f.parse(json.dumps({"method": "depth.update", "params": [True, {"bids": [["1", "1"]], "asks": [["2", "1"]]}, "BTC_USDT"]})) is None


def test_depth_level_slice():
    c = _spot(); c.depth_level = 1
    frame = {"method": "depth.update", "params": [True,
             {"bids": [["100", "5"], ["99", "3"]], "asks": [["101", "4"], ["102", "1"]]}, "BTC_USDT"]}
    b = c.parse(json.dumps(frame))[0]
    assert len(b.bids) == 1 and len(b.asks) == 1


def test_topn_survives_non_list_row():
    c = _spot()   # a non-list element (None/int) must drop only that row, NOT crash + lose the whole frame
    frame = {"method": "depth.update", "params": [True,
             {"bids": [None, ["100", "5"], 123], "asks": [["101", "4"]]}, "BTC_USDT"]}
    b = c.parse(json.dumps(frame))[0]
    assert b.bids[0] == ["100", "5"] and b.asks[0] == ["101", "4"]


def test_parse_rejects_clean_false_diff():
    c = _spot()   # clean=false would be an incremental diff; must not be applied as a full snapshot
    diff = {"method": "depth.update", "params": [False,
            {"bids": [["100", "5"]], "asks": [["101", "4"]]}, "BTC_USDT"]}
    assert c.parse(json.dumps(diff)) is None


def test_send_subscribe_resubscribes_when_tick_resolves():
    c = _spot(); ws = _WS()
    c._tick = {"BTCUSDT": "0.1"}                       # ETH tick not yet published
    n1 = asyncio.run(c._send_subscribe(ws, ["BTCUSDT", "ETHUSDT"]))
    assert n1 == 1 and json.loads(ws.sent[0])["params"] == [["BTC_USDT", 30, "0.1"]]   # ETH skipped, not dropped
    c._tick["ETHUSDT"] = "0.01"                        # tick publishes later
    n2 = asyncio.run(c._send_subscribe(ws, ["BTCUSDT", "ETHUSDT"]))   # ping-loop retry path re-sends full set
    assert n2 == 2 and json.loads(ws.sent[1])["params"] == [["BTC_USDT", 30, "0.1"], ["ETH_USDT", 30, "0.01"]]


def test_ping_loop_drives_late_tick_resubscribe_then_cleans_up():
    """END-TO-END drive of the ACTUAL _ping_loop retry path (not just the helper): a symbol with no tick at
    subscribe is skipped; once its tick appears, the running ping loop must re-resolve + re-send the full
    nested subscribe; on disconnect (task cancel, as the core does on reconnect) the per-conn state is freed."""
    c = _spot(); c.ping_interval = 100   # interval floors to 5s; only the first (pre-sleep) iteration matters

    async def _noload(syms):             # bypass redis; drive self._tick directly
        return None
    c._load_spec = _noload
    ws = _WS()

    async def run():
        c._tick = {"BTCUSDT": "0.1"}                      # ETH tick unknown at subscribe time
        await c.subscribe(ws, ["BTCUSDT", "ETHUSDT"])
        assert json.loads(ws.sent[0])["params"] == [["BTC_USDT", 30, "0.1"]]      # ETH skipped
        assert c._conn_syms[id(ws)] == ["BTCUSDT", "ETHUSDT"] and c._conn_sent[id(ws)] == 1

        c._tick["ETHUSDT"] = "0.01"                       # tick publishes AFTER connect
        task = asyncio.create_task(c._ping_loop(ws))
        await asyncio.sleep(0.05)                         # let the first iteration (ping + retry) run

        resubs = [json.loads(m) for m in ws.sent if json.loads(m).get("method") == "depth.subscribe"]
        assert resubs[-1]["params"] == [["BTC_USDT", 30, "0.1"], ["ETH_USDT", 30, "0.01"]]  # ETH now subscribed
        assert c._conn_sent[id(ws)] == 2

        task.cancel()                                     # core cancels ping_task on reconnect
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert id(ws) not in c._conn_syms and id(ws) not in c._conn_sent   # cleaned up in finally

    asyncio.run(run())
