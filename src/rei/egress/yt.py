"""YouTube search + audio stream resolution via yt-dlp (for in-app playback).

Lives under rei.egress so the socket guard allows yt-dlp's requests, and each
lookup is checked by the EgressGate first. Nothing is downloaded to disk: we
only resolve the audio stream URL, which the player then streams.

Note: extracting streams this way is against YouTube's terms of service; it is
meant for personal use and may break when YouTube changes.
"""
from dataclasses import dataclass
from typing import Any

from rei.egress.gate import EgressGate

HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "music.youtube.com",
         ".googlevideo.com", ".ytimg.com", ".youtube.com"}


class YouTubeError(Exception):
    pass


@dataclass
class AudioResult:
    title: str
    url: str
    headers: dict[str, str]
    duration_s: int
    webpage: str


def search_audio(gate: EgressGate, query: str) -> AudioResult:
    gate.check_host("www.youtube.com", "music")
    try:
        import yt_dlp  # type: ignore
    except ImportError as e:
        raise YouTubeError("yt-dlp isn't installed (uv add yt-dlp).") from e

    options: dict[str, Any] = {
        "format": "bestaudio[acodec=opus]/bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "default_search": "ytsearch1",
        "socket_timeout": 15,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
    except Exception as e:
        raise YouTubeError(f"YouTube lookup failed: {e}") from e
    entries = (info or {}).get("entries") or []
    if not entries:
        raise YouTubeError(f"Nothing found on YouTube for {query!r}.")
    entry = entries[0]
    url = entry.get("url")
    if not url:
        raise YouTubeError("YouTube didn't return a playable audio stream.")
    return AudioResult(
        title=str(entry.get("title") or query),
        url=str(url),
        headers={k: str(v) for k, v in (entry.get("http_headers") or {}).items()},
        duration_s=int(entry.get("duration") or 0),
        webpage=str(entry.get("webpage_url") or ""),
    )
