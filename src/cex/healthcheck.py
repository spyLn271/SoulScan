#!/usr/bin/env python3
"""CEX feed health probe: `python -m src.cex.healthcheck [--json] [--quiet]`.
Exit 0 if every enabled pair has a fresh heartbeat and is not degraded."""
import argparse
import json
import sys
import redis

from src.cex.producer.config import get_redis_config, MONITORING_CONFIG
from src.cex.health import scan_all


def _redis_client():
    cfg = get_redis_config()
    return redis.Redis(host=cfg["host"], port=cfg["port"], db=cfg.get("db", 0),
                       password=cfg.get("password"), decode_responses=True,
                       socket_connect_timeout=5, socket_timeout=5)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CEX feed health probe")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--hung-timeout", type=float,
                    default=MONITORING_CONFIG.get("hung_worker_timeout", 120))
    args = ap.parse_args(argv)
    try:
        client = _redis_client(); client.ping()
    except Exception as e:
        if not args.quiet:
            print(f"UNHEALTHY: cannot reach Redis: {e}", file=sys.stderr)
        return 2
    results = scan_all(client, hung_timeout=args.hung_timeout)
    unhealthy = [r for r in results if not r.healthy]
    if args.json:
        if not args.quiet:
            print(json.dumps([{
                "exchange": r.exchange, "market_type": r.market_type, "healthy": r.healthy,
                "heartbeats": r.heartbeats, "fresh_heartbeats": r.fresh_heartbeats,
                "max_age_s": round(r.max_age_s, 1) if r.max_age_s is not None else None,
                "active_symbols": r.active_symbols, "total_msgs": r.total_msgs,
                "backpressured": r.backpressured, "monitoring_healthy": r.monitoring_healthy,
                "proxy_rotations": r.proxy_rotations,
            } for r in results], indent=2))
    elif not args.quiet:
        print(f"{'PAIR':<22} {'OK':<4} {'HB':<4} {'AGE(s)':<8} {'SYMS':<6} {'MSGS':<10} NOTES")
        for r in sorted(results, key=lambda x: (not x.healthy, x.exchange)):
            note = []
            if r.heartbeats == 0: note.append("no-heartbeat")
            if r.backpressured: note.append("redis-backpressure")
            if not r.monitoring_healthy: note.append("monitor-unhealthy")
            if r.heartbeats and r.fresh_heartbeats == 0: note.append("stale")
            age = f"{r.max_age_s:.1f}" if r.max_age_s is not None else "-"
            print(f"{r.exchange + ':' + r.market_type:<22} {'yes' if r.healthy else 'NO':<4} "
                  f"{r.heartbeats:<4} {age:<8} {r.active_symbols:<6} {r.total_msgs:<10} {','.join(note)}")
        print(f"\n{len(results) - len(unhealthy)}/{len(results)} pairs healthy")
    return 0 if not unhealthy else 1


if __name__ == "__main__":
    sys.exit(main())
