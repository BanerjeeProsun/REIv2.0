"""Open remote audio streams for in-app music playback.

PyAV/ffmpeg opens its own network connections (outside Python's socket module,
so the socket guard can't see them). That is why every stream URL is checked
against the EgressGate here, before anything is opened.
"""
from typing import Any
from urllib.parse import urlparse

from rei.egress.gate import EgressGate
from rei.egress.socket_guard import EgressBlockedError


def open_audio(gate: EgressGate, url: str, headers: dict[str, str] | None = None) -> Any:
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise EgressBlockedError(f"Refusing to stream from {url[:60]}")
    gate.check_host(parsed.hostname, "music")
    import av  # PyAV (bundled ffmpeg)

    options = {
        "reconnect": "1",
        "reconnect_streamed": "1",
        "reconnect_delay_max": "5",
        "rw_timeout": "15000000",  # microseconds
    }
    if headers:
        options["headers"] = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
    return av.open(url, options=options, timeout=15)
