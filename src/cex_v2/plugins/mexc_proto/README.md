# mexc_proto — vendored MEXC protobuf schema

MEXC's official WebSocket `.proto` files (from github.com/mexcdevelop/websocket-proto) plus the
generated `*_pb2.py` modules. The plugin (`../mexc.py`) decodes the protobuf order-book frames with
these.

**Do NOT add an `__init__.py` here.** The generated `*_pb2.py` use *flat* imports (e.g.
`import PublicLimitDepthsV3Api_pb2`), and the plugin loads them by inserting this directory onto
`sys.path` and importing `PushDataV3ApiWrapper_pb2` flat. If this becomes a package, the same generated
module could be imported via two names (flat *and* `src.cex_v2.plugins.mexc_proto.X_pb2`), which makes
protobuf raise `"… already exists in the descriptor pool"` (double registration).

**Regenerating** (only needed if MEXC changes the schema; runtime needs only `protobuf`):

```
pip install grpcio-tools
python -m grpc_tools.protoc -I. --python_out=. *.proto
```
