#!/usr/bin/env python3
"""
Decode a captured (binary) WebSocket frame into human-readable JSON.

Exchanges compress their WS payloads differently — bybit realtime_w = gzip (1f8b...), OKX =
permessage-deflate, others use zlib / brotli / zstd. When you grab a frame from the browser
DevTools (Network -> WS -> Messages), a binary frame shows as a hex blob; paste it here and this
auto-detects the compression and pretty-prints the JSON.

  # hex pasted from DevTools (spaces / 0x / commas / newlines are tolerated)
  .venv/bin/python analyzer_tools/decode_frame.py '1f8b0800...'
  echo '1f 8b 08 00 ...' | .venv/bin/python analyzer_tools/decode_frame.py
  .venv/bin/python analyzer_tools/decode_frame.py --in b64 'H4sIAAAA...'
  .venv/bin/python analyzer_tools/decode_frame.py --file frame.bin          # raw bytes on disk
  cat frame.bin | .venv/bin/python analyzer_tools/decode_frame.py           # raw bytes piped

Input is auto-sniffed as hex / base64 / raw bytes (override with --in). Compression is auto-detected
by magic bytes with a fallback that tries every codec. Already-plain JSON is just pretty-printed, so
this doubles as a JSON formatter for the text frames you paste too. A one-line summary of what was
detected goes to stderr (so stdout stays pipe-clean); use --quiet to silence it.
"""
import argparse
import binascii
import gzip
import json
import re
import sys
import zlib

# --- optional codecs: degrade gracefully, never crash if a lib is absent ---
try:
    import brotli as _brotli
except ImportError:
    try:
        import brotlicffi as _brotli   # drop-in alternative
    except ImportError:
        _brotli = None
try:
    import zstandard as _zstd
except ImportError:
    _zstd = None
try:
    import msgpack as _msgpack
except ImportError:
    _msgpack = None


# ----------------------------------------------------------------- input -> bytes
def _clean(s: str) -> str:
    """Strip the cosmetics DevTools / pasted dumps add: 0x prefixes, commas, whitespace."""
    return re.sub(r"0x", "", s, flags=re.I).translate({ord(c): None for c in " \t\r\n,;:"})


_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_B64_RE = re.compile(r"^[A-Za-z0-9+/=]+$")


def to_bytes(data, mode: str) -> bytes:
    """Interpret the raw input (str or bytes) as bytes per `mode` (auto|hex|b64|raw)."""
    if isinstance(data, bytes):
        # a file/stdin gave us bytes: it might still be a TEXT hex/base64 dump
        if mode == "raw":
            return data
        try:
            text = data.decode("ascii")
        except UnicodeDecodeError:
            return data                      # genuinely binary -> use as-is
        data = text                          # fall through to string handling
    s = data
    if mode == "hex":
        return binascii.unhexlify(_clean(s))
    if mode == "b64":
        import base64
        return base64.b64decode(_clean(s))
    if mode == "raw":
        return s.encode("utf-8", "replace")
    # auto-sniff
    c = _clean(s)
    if c and len(c) % 2 == 0 and _HEX_RE.match(c):
        return binascii.unhexlify(c)
    if c and len(c) % 4 == 0 and _B64_RE.match(c) and not _looks_like_json(s):
        import base64
        try:
            return base64.b64decode(c)
        except binascii.Error:
            pass
    return s.encode("utf-8", "replace")      # already text (e.g. a plain JSON frame)


def _looks_like_json(s: str) -> bool:
    t = s.strip()
    return t.startswith(("{", "[")) and t.endswith(("}", "]"))


# ----------------------------------------------------------------- decompression
def _decompressors():
    """Ordered (name, fn) codec attempts. zlib(47) auto-detects gzip+zlib; (-15) is raw deflate
    (what permessage-deflate uses); identity passes bytes through unchanged."""
    d = [
        ("gzip", gzip.decompress),
        ("zlib", lambda b: zlib.decompress(b)),
        ("zlib/auto", lambda b: zlib.decompress(b, 47)),
        ("deflate-raw", lambda b: zlib.decompress(b, -15)),
    ]
    if _brotli:
        d.append(("brotli", _brotli.decompress))
    if _zstd:
        d.append(("zstd", lambda b: _zstd.ZstdDecompressor().decompress(b)))
    d.append(("none", lambda b: b))
    return d


def _magic_first(b: bytes):
    """Codec name suggested by leading magic bytes, or None."""
    if b[:2] == b"\x1f\x8b":
        return "gzip"
    if b[:1] == b"\x78" and b[1:2] in (b"\x01", b"\x9c", b"\xda", b"\x5e"):
        return "zlib"
    if b[:4] == b"\x28\xb5\x2f\xfd":
        return "zstd"
    return None


def decode(b: bytes):
    """Return (codec_name, rendered_text, kind). Prefers the codec whose output parses as JSON."""
    order = _decompressors()
    pref = _magic_first(b)
    if pref:
        order.sort(key=lambda kv: 0 if kv[0].startswith(pref) else 1)
    first_text = None
    for name, fn in order:
        try:
            out = fn(b)
        except Exception:
            continue
        rendered, kind = _render(out)
        if kind == "json":
            return name, rendered, kind            # best: real JSON
        if kind in ("text", "msgpack") and first_text is None:
            first_text = (name, rendered, kind)
    if first_text:
        return first_text
    return "none", _hexdump(b), "binary"


# ----------------------------------------------------------------- rendering
def _parse_json_stream(text: str):
    """Parse one OR MANY concatenated JSON values (captures often paste {..}{..} back-to-back)."""
    dec = json.JSONDecoder()
    objs, i, n = [], 0, len(text)
    while i < n:
        while i < n and text[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        try:
            obj, end = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            return None
        objs.append(obj)
        i = end
    return objs or None


def _render(out: bytes):
    """(rendered_text, kind) where kind in {json, text, msgpack, binary}."""
    try:
        text = out.decode("utf-8")
        objs = _parse_json_stream(text)
        if objs is not None:
            body = "\n".join(json.dumps(o, indent=2, ensure_ascii=False) for o in objs)
            return body, "json"
        if text.isprintable() or "\n" in text:
            return text, "text"
    except UnicodeDecodeError:
        pass
    if _msgpack is not None:
        try:
            obj = _msgpack.unpackb(out, raw=False)
            return json.dumps(obj, indent=2, ensure_ascii=False, default=str), "msgpack"
        except Exception:
            pass
    return _hexdump(out), "binary"


def _hexdump(b: bytes, limit: int = 512) -> str:
    rows = []
    for off in range(0, min(len(b), limit), 16):
        chunk = b[off:off + 16]
        hexs = " ".join(f"{x:02x}" for x in chunk)
        text = "".join(chr(x) if 32 <= x < 127 else "." for x in chunk)
        rows.append(f"{off:08x}  {hexs:<47}  {text}")
    if len(b) > limit:
        rows.append(f"... ({len(b)} bytes total)")
    return "\n".join(rows)


# ----------------------------------------------------------------- cli
def main() -> int:
    ap = argparse.ArgumentParser(description="Decode a binary/compressed WS frame to human-readable JSON.")
    ap.add_argument("data", nargs="?", help="frame as hex/base64/text (omit to read stdin)")
    ap.add_argument("--file", help="read the frame bytes from a file")
    ap.add_argument("--in", dest="mode", choices=["auto", "hex", "b64", "raw"], default="auto",
                    help="how to interpret the input (default: auto-sniff)")
    ap.add_argument("--compact", action="store_true", help="one-line JSON instead of indented")
    ap.add_argument("--quiet", action="store_true", help="suppress the stderr detection summary")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "rb") as fh:
            raw = fh.read()
    elif args.data is not None:
        raw = args.data
    elif not sys.stdin.isatty():
        raw = sys.stdin.buffer.read()
    else:
        ap.error("no input: pass a frame as an argument, --file, or via stdin")

    try:
        b = to_bytes(raw, args.mode)
    except (binascii.Error, ValueError) as e:
        print(f"input decode failed ({args.mode}): {e}", file=sys.stderr)
        return 2

    codec, rendered, kind = decode(b)

    if kind == "json" and args.compact:
        objs = _parse_json_stream(rendered)
        rendered = "\n".join(json.dumps(o, ensure_ascii=False, separators=(",", ":")) for o in (objs or []))

    if not args.quiet:
        nbytes = len(b)
        hint = ""
        if kind == "binary" and not (_brotli and _zstd and _msgpack):
            missing = [n for n, m in (("brotli", _brotli), ("zstd", _zstd), ("msgpack", _msgpack)) if not m]
            hint = f"  (couldn't decode; if this feed uses one, install: pip install {' '.join(missing)})"
        print(f"# {nbytes} B in -> codec={codec} -> {kind}{hint}", file=sys.stderr)

    print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
