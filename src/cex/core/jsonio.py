import json as _json

try:
    import orjson

    HAVE_ORJSON = True

    def dumps(obj) -> str:
        return orjson.dumps(obj).decode()

    def loads(s):
        return orjson.loads(s)
except ImportError:
    HAVE_ORJSON = False

    def dumps(obj) -> str:
        return _json.dumps(obj, separators=(",", ":"))

    def loads(s):
        return _json.loads(s)
