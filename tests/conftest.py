"""Shared pytest fixtures for the SoulScan CEX test suite.

- `fake_redis`: in-memory async Redis (fakeredis), the default for fast/isolated tests.
- `real_redis`: a real Redis on db=15 (flushed on teardown), only when CEX_TEST_REDIS=1.
- live tests (marker `live`) are skipped unless CEX_LIVE_TESTS=1.
"""
import os
import pytest
import pytest_asyncio


def pytest_configure(config):
    """Make `pytest tests/cex` work with no pytest.ini on this CEX-only branch:
    enable auto asyncio mode and register the custom markers so async tests run
    and `live`/`integration` don't warn."""
    # asyncio_mode=auto: plain `async def test_*` run without per-test decorators.
    try:
        config.inicfg.setdefault("asyncio_mode", "auto")
    except Exception:
        pass
    try:
        config.option.asyncio_mode = "auto"
    except Exception:
        pass
    config.addinivalue_line(
        "markers",
        "live: tests that connect to real exchanges (via proxy); skipped unless CEX_LIVE_TESTS=1",
    )
    config.addinivalue_line(
        "markers",
        "integration: tests that need a real Redis (db=15); skipped unless CEX_TEST_REDIS=1",
    )


@pytest_asyncio.fixture
async def fake_redis():
    import fakeredis.aioredis
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture
async def real_redis():
    if os.getenv("CEX_TEST_REDIS") != "1":
        pytest.skip("real Redis test; set CEX_TEST_REDIS=1 to run")
    import redis.asyncio as redis
    host = os.getenv("REDIS__HOST", os.getenv("REDIS_HOST", "localhost"))
    port = int(os.getenv("REDIS__PORT", os.getenv("REDIS_PORT", "6379")))
    client = redis.Redis(host=host, port=port, db=15, decode_responses=True)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


def pytest_collection_modifyitems(config, items):
    run_live = os.getenv("CEX_LIVE_TESTS") == "1"
    skip_live = pytest.mark.skip(reason="live exchange test; set CEX_LIVE_TESTS=1 to run")
    for item in items:
        if "live" in item.keywords and not run_live:
            item.add_marker(skip_live)
