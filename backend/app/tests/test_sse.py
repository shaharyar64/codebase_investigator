"""SSE encoding tests."""

import json

from app.utils.sse import encode_sse


def test_encode_sse_roundtrip() -> None:
    raw = encode_sse("message", {"content": "hello"})
    text = raw.decode()
    assert text.startswith("event: message\n")
    assert "data:" in text
    payload_line = [ln for ln in text.split("\n") if ln.startswith("data: ")][0]
    data = json.loads(payload_line.removeprefix("data: "))
    assert data == {"content": "hello"}
