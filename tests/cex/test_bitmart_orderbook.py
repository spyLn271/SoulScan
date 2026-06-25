"""BitMart order-book plugins: spot (stateless, both sides/frame) + futures (stateful, split by way)."""
import asyncio
import gzip
import json
import zlib

from src.cex.plugins.bitmart import BitmartSpotConnector, BitmartFuturesConnector


# ---- SPOT ----
def _spot_frame(symu, bids, asks, ms=1700, compress=None):
    msg = json.dumps({"table": "spot/depth20", "data": [{"bids": bids, "asks": asks, "ms_t": ms, "symbol": symu}]})
    if compress == "deflate":
        co = zlib.compressobj(wbits=-15); return co.compress(msg.encode()) + co.flush()
    if compress == "gzip":
        return gzip.compress(msg.encode())
    return msg


def test_spot_full_snapshot_stateless():
    c = BitmartSpotConnector()
    out = c.parse(_spot_frame("BTC_USDT", [["100", "1"], ["99", "2"]], [["101", "3"], ["102", "4"]]))
    assert out[0].symbol == "BTCUSDT" and out[0].event_ts_ms == 1700
    assert out[0].bids == [["100", "1"], ["99", "2"]] and out[0].asks == [["101", "3"], ["102", "4"]]


def test_spot_handles_compressed_frames():
    c = BitmartSpotConnector()
    for comp in ("deflate", "gzip"):
        out = c.parse(_spot_frame("ETH_USDT", [["10", "1"]], [["11", "1"]], compress=comp))
        assert out[0].symbol == "ETHUSDT", comp


def test_spot_crossed_and_oneside_and_pong():
    c = BitmartSpotConnector()
    assert c.parse(_spot_frame("BTC_USDT", [["105", "1"]], [["104", "1"]])) is None   # crossed
    assert c.parse(_spot_frame("BTC_USDT", [["100", "1"]], [])) is None               # one-sided
    assert c.parse("pong") is None


def test_spot_malformed_and_zero_ms_t():
    c = BitmartSpotConnector()
    bad = c.parse(_spot_frame("BTC_USDT", [["100", "1"]], [["101", "1"]], ms="not-a-ts"))
    assert bad[0].event_ts_ms is None and bad[0].symbol == "BTCUSDT"   # bad ts -> None, book still emitted
    zero = c.parse(_spot_frame("BTC_USDT", [["100", "1"]], [["101", "1"]], ms=0))
    assert zero[0].event_ts_ms == 0                                    # legit 0 preserved (not dropped as falsy)


def test_spot_subscribe_op_and_underscore():
    c = BitmartSpotConnector(); sent = []

    class _WS:
        async def send(self, m): sent.append(json.loads(m))
    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "ETHUSDT"]))
    args = [a for m in sent for a in m["args"]]
    assert all(m["op"] == "subscribe" for m in sent)
    assert args == ["spot/depth20:BTC_USDT", "spot/depth20:ETH_USDT"]
    assert asyncio.run(c.ping_message()) == "ping"


# ---- FUTURES ----
def _fut_frame(sym, way, levels, ms=1800):
    return json.dumps({"group": f"futures/depth20:{sym}",
                       "data": [{"symbol": sym, "way": way, "ms_t": ms,
                                 "depths": [{"price": p, "vol": v} for p, v in levels]}]})


def test_futures_stateful_combines_both_sides():
    c = BitmartFuturesConnector()
    # way=1 bids only -> not enough yet
    assert c.parse(_fut_frame("BTCUSDT", 1, [["100", "5"], ["99", "3"]])) is None
    # way=2 asks -> now emit
    out = c.parse(_fut_frame("BTCUSDT", 2, [["101", "7"], ["102", "2"]]))
    assert out[0].symbol == "BTCUSDT"
    assert out[0].bids == [["100", "5"], ["99", "3"]] and out[0].asks == [["101", "7"], ["102", "2"]]


def test_futures_sizes_scaled_by_contract_size():
    c = BitmartFuturesConnector()
    c._mult["BTCUSDT"] = 0.001                                 # 1 contract = 0.001 BTC
    c.parse(_fut_frame("BTCUSDT", 1, [["100", "5"], ["99", "10"]]))
    out = c.parse(_fut_frame("BTCUSDT", 2, [["101", "3"]]))
    assert out[0].bids[0][0] == "100" and abs(out[0].bids[0][1] - 0.005) < 1e-12   # 5 contracts -> 0.005 BTC
    assert abs(out[0].bids[1][1] - 0.010) < 1e-12
    assert abs(out[0].asks[0][1] - 0.003) < 1e-12


def test_futures_sizes_raw_when_no_multiplier():
    c = BitmartFuturesConnector()                             # no _mult loaded -> raw (mult defaults 1.0)
    c.parse(_fut_frame("BTCUSDT", 1, [["100", "5"]]))
    out = c.parse(_fut_frame("BTCUSDT", 2, [["101", "3"]]))
    assert out[0].bids[0] == ["100", "5"] and out[0].asks[0] == ["101", "3"]   # strings, untouched


def test_futures_malformed_ms_t_still_emits():
    c = BitmartFuturesConnector()
    c.parse(_fut_frame("BTCUSDT", 1, [["100", "5"]], ms="bad"))
    out = c.parse(_fut_frame("BTCUSDT", 2, [["101", "7"]], ms="bad"))
    assert out[0].symbol == "BTCUSDT" and out[0].event_ts_ms is None   # bad ts -> None, both-sides book emitted


def test_futures_sub_reject_with_data_does_not_pollute_book():
    c = BitmartFuturesConnector()
    # a rejection ACK that ALSO carries a data field must be dropped BEFORE it seeds book state
    msg = json.dumps({"action": "subscribe", "success": False,
                      "data": [{"symbol": "BTCUSDT", "way": 1, "depths": [{"price": "1", "vol": "1"}]}]})
    assert c.parse(msg) is None
    assert "BTCUSDT" not in c._book


def test_futures_pong_and_ack_ignored():
    c = BitmartFuturesConnector()
    assert c.parse(json.dumps({"group": "System", "data": "pong"})) is None
    assert c.parse(json.dumps({"action": "subscribe", "group": "futures/depth20:BTCUSDT", "success": True})) is None


def test_futures_subscribe_action_and_ping():
    c = BitmartFuturesConnector(); sent = []

    async def _noload(syms):   # isolate from redis/md (contract_size loading has its own test)
        pass
    c._load_mult = _noload

    class _WS:
        async def send(self, m): sent.append(json.loads(m))
    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "ETHUSDT"]))
    args = [a for m in sent for a in m["args"]]
    assert all(m["action"] == "subscribe" for m in sent)
    assert args == ["futures/depth20:BTCUSDT", "futures/depth20:ETHUSDT"]
    assert json.loads(asyncio.run(c.ping_message())) == {"action": "ping"}


def test_futures_ws_urls():
    assert asyncio.run(BitmartSpotConnector().ws_url()).startswith("wss://ws-manager-compress.bitmart.com")
    assert asyncio.run(BitmartFuturesConnector().ws_url()).startswith("wss://openapi-ws-v2.bitmart.com")


# ---- bounded-connection registry / volume-ordered bin-packing ----
class _FakeRedis:
    def __init__(self, h): self._h = h
    async def hgetall(self, key): return self._h
    async def hmget(self, key, *syms): return [self._h.get(s) for s in syms]


class _WS:
    def __init__(self): self.sent = []
    async def send(self, m): self.sent.append(json.loads(m))


def test_get_symbols_volume_ordered():
    c = BitmartSpotConnector()
    c.redis = _FakeRedis({
        "BTCUSDT": json.dumps({"24h_volume_usdt": 1000}),
        "ETHUSDT": json.dumps({"24h_volume_usdt": 5000}),
        "DOGEUSDT": json.dumps({"24h_volume_usdt": 50}),
        "BADUSDT": "not json",      # malformed -> vol 0 -> sorts last, still kept
        "_version": "123",          # meta -> excluded
    })
    assert asyncio.run(c.get_symbols()) == ["ETHUSDT", "BTCUSDT", "DOGEUSDT", "BADUSDT"]


def test_batches_build_registry_same_objects():
    c = BitmartSpotConnector(); c.symbols_per_connection = 2
    batches = c._batches(["A", "B", "C", "D", "E"])
    assert [len(b) for b in batches] == [2, 2, 1] and len(c._conns) == 3
    for i, b in enumerate(batches):
        assert c._conns[f"b{i}"]["symbols"] is b      # IDENTITY: registry holds the exact list objects


def test_subscribe_captures_ws():
    c = BitmartSpotConnector(); c.symbols_per_connection = 100
    lst = c._batches(["BTCUSDT", "ETHUSDT"])[0]
    ws1 = _WS(); asyncio.run(c.subscribe(ws1, lst))
    assert c._conns["b0"]["ws"] is ws1
    ws2 = _WS(); asyncio.run(c.subscribe(ws2, lst))   # reconnect updates the live ws (reconnects now tracked in core)
    assert c._conns["b0"]["ws"] is ws2


def test_pack_new_fills_existing_no_new_connection():
    c = BitmartSpotConnector(); c.symbols_per_connection = 5
    c._batches(["A", "B"]); e = c._conns["b0"]; e["ws"] = _WS()
    asyncio.run(c._pack_new(["C"]))
    assert e["symbols"] == ["A", "B", "C"]            # appended in place
    assert len(c._conns) == 1 and len(c._conn_tasks) == 0   # NO new connection/task
    assert e["ws"].sent and e["ws"].sent[0]["op"] == "subscribe"   # live subscribe was sent on the existing ws


def test_pack_new_many_within_capacity_spawns_zero_tasks():   # the storm-guard
    c = BitmartSpotConnector(); c.symbols_per_connection = 100
    c._batches(["A"]); c._conns["b0"]["ws"] = _WS()
    asyncio.run(c._pack_new([f"S{i}" for i in range(50)]))
    assert len(c._conns) == 1 and len(c._conn_tasks) == 0
    assert len(c._conns["b0"]["symbols"]) == 51


def test_pack_new_grows_one_when_full():
    c = BitmartSpotConnector(); c.symbols_per_connection = 2
    async def _noop(cid, syms): pass
    c._connection_loop = _noop                         # avoid a real connection task in the test
    c._batches(["A", "B"]); c._conns["b0"]["ws"] = _WS()
    asyncio.run(c._pack_new(["C"]))
    assert len(c._conns) == 2 and c._conns["b0"]["symbols"] == ["A", "B"]   # head untouched
    newcid = next(k for k in c._conns if k != "b0")
    assert c._conns[newcid]["symbols"] == ["C"] and newcid in c._conn_tasks


def test_prune_from_registry_cleans_list_and_futures_state():
    c = BitmartFuturesConnector(); c.symbols_per_connection = 5
    c._batches(["AUSDT", "BUSDT", "CUSDT"])
    c._book["BUSDT"] = {"b": [], "a": []}; c._mult["BUSDT"] = 0.1
    c._prune_from_registry(["BUSDT"])
    assert c._conns["b0"]["symbols"] == ["AUSDT", "CUSDT"]   # removed in place (object identity kept)
    assert "BUSDT" not in c._book and "BUSDT" not in c._mult


def test_mutable_list_reconnect_resubscribes_grown_set():
    c = BitmartSpotConnector(); c.symbols_per_connection = 100
    lst = c._batches(["BTCUSDT"])[0]; ws = _WS()
    asyncio.run(c.subscribe(ws, lst))      # first: BTC only
    lst.append("ETHUSDT")                   # live-add mutates the SAME list object
    ws.sent.clear()
    asyncio.run(c.subscribe(ws, lst))       # reconnect re-subscribes the grown set
    args = [a for m in ws.sent for a in m["args"]]
    assert "spot/depth20:BTC_USDT" in args and "spot/depth20:ETH_USDT" in args


def test_live_pack_defaults_on():
    assert BitmartSpotConnector()._live_pack is True and BitmartFuturesConnector()._max_conns == 20


def test_load_mult_rejects_nonpositive_contract_size(monkeypatch):
    import src.cex.plugins.bitmart as bm
    async def _fast(_): pass
    monkeypatch.setattr(bm.asyncio, "sleep", _fast)   # don't actually wait the cold-start retries
    c = BitmartFuturesConnector()
    c.redis = _FakeRedis({"GOODUSDT": json.dumps({"contract_size": 0.1}),
                          "ZEROUSDT": json.dumps({"contract_size": 0})})   # invalid: would zero every size
    asyncio.run(c._load_mult(["GOODUSDT", "ZEROUSDT"]))
    assert c._mult.get("GOODUSDT") == 0.1
    assert "ZEROUSDT" not in c._mult and "ZEROUSDT" in c._mult_failed     # -> raw (mult 1.0), not 0


def test_grow_cid_monotonic_collision_proof():
    c = BitmartSpotConnector(); c.symbols_per_connection = 1
    async def _noop(cid, syms): pass
    c._connection_loop = _noop
    c._batches(["A"])                       # b0 full (1/1)
    asyncio.run(c._pack_new(["B", "C"]))    # each grows a new connection
    gcids = [k for k in c._conns if k.startswith("g")]
    assert gcids == ["g1", "g2"]            # monotonic, distinct (independent of registry size)
