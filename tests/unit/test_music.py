import base64
import hashlib
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np
import pytest

from rei.connectors import ConnectorError
from rei.connectors import spotify as spotify_mod
from rei.connectors.music import MusicHub, PlayMusicArgs
from rei.connectors.spotify import SpotifyConnector, authorize_url, pkce_pair
from rei.connectors.youtube import YouTubeConnector
from rei.egress import spotify_http, yt
from rei.egress.gate import EgressGate
from rei.egress.socket_guard import EgressBlockedError
from rei.policy.config import load_policy_config
from rei.policy.schemas import PrivacyMode
from rei.voice.player import CHANNELS, MusicPlayer, Track
from rei.voice.wake import strip_wake_word

POLICY = Path(__file__).resolve().parents[2] / "src" / "rei" / "policy" / "policy.toml"


# --- wake word ---

@pytest.mark.parametrize("text, expected", [
    ("Hey Rei, pause the music", "pause the music"),
    ("rei stop", "stop"),
    ("Ray. Next song", "Next song"),
    ("rainy days and mondays", None),          # lyrics, not a command
    ("I said hey there", None),
    ("hey rei", "hello"),
])
def test_wake_word(text: str, expected: Any) -> None:
    assert strip_wake_word(text) == expected


# --- gate suffix hosts ---

def test_gate_allows_stream_subdomains_only_for_suffix_entries() -> None:
    gate = EgressGate(load_policy_config(str(POLICY)), PrivacyMode.LOCAL_PLUS_WEB,
                      connector_hosts=lambda: {".googlevideo.com", "www.youtube.com"})
    gate.check_host("rr3---sn-abc.googlevideo.com", "music")
    gate.check_host("www.youtube.com", "music")
    for bad in ("evilgooglevideo.com", "youtube.com.evil.net", "api.youtube.com"):
        with pytest.raises(EgressBlockedError):
            gate.check_host(bad, "music")


# --- player (real PyAV frames through the real resampler) ---

class FakeContainer:
    def __init__(self, seconds: float = 0.5, rate: int = 44100) -> None:
        import av
        n = int(seconds * rate)
        tone = (0.5 * np.sin(np.linspace(0, 2 * np.pi * 440 * seconds, n))).astype(np.float32)
        frame = av.AudioFrame.from_ndarray(np.stack([tone, tone]), format="fltp", layout="stereo")
        frame.sample_rate = rate
        self.frames = [frame]
        self.streams = [type("S", (), {"type": "audio"})()]
        self.closed = False

    def demux(self, stream: Any) -> Any:
        frames = self.frames
        yield type("P", (), {"decode": lambda self: frames})()

    def close(self) -> None:
        self.closed = True


class FakeOutput:
    instances: list["FakeOutput"] = []

    def __init__(self, **kw: Any) -> None:
        self.callback = kw["callback"]
        self.started = self.stopped = False
        FakeOutput.instances.append(self)

    def start(self) -> None: self.started = True
    def stop(self) -> None: self.stopped = True
    def close(self) -> None: ...

    def pull(self, frames: int = 1024) -> np.ndarray:
        out = np.zeros((frames, CHANNELS), dtype=np.float32)
        self.callback(out, frames, None, None)
        return out


def _player(container: Any) -> tuple[MusicPlayer, list[int]]:
    changes: list[int] = []
    player = MusicPlayer(opener=lambda url, headers: container, on_change=lambda: changes.append(1),
                         output_factory=FakeOutput)
    return player, changes


def test_player_plays_pauses_ducks_and_stops() -> None:
    container = FakeContainer()
    player, changes = _player(container)
    player.play(Track(title="Lofi", url="https://x.googlevideo.com/a"))
    out = FakeOutput.instances[-1]
    deadline = time.monotonic() + 3
    loud = 0.0
    while time.monotonic() < deadline and loud == 0.0:
        loud = float(np.abs(out.pull()).max())
        time.sleep(0.01)
    assert loud > 0.1 and player.active and player.title == "Lofi"

    player.pause()
    assert float(np.abs(out.pull()).max()) == 0.0
    player.resume()

    player.duck(True)
    for _ in range(20):
        ducked = float(np.abs(out.pull()).max())
    assert ducked < loud * 0.6

    player.stop()
    assert not player.active and out.stopped and changes


def test_player_reports_decoder_errors() -> None:
    def broken(url: str, headers: dict[str, str]) -> Any:
        raise RuntimeError("403 Forbidden")

    player = MusicPlayer(opener=broken, output_factory=FakeOutput)
    player.play(Track(title="x", url="https://x.googlevideo.com/a"))
    time.sleep(0.3)
    assert "403" in player.error
    player.stop()


# --- hub + connectors ---

class FakeProvider:
    def __init__(self, pid: str, available: bool = True) -> None:
        self.id, self._available = pid, available
        self.played: list[str] = []
        self.controls: list[str] = []

    @property
    def available(self) -> bool:
        return self._available

    def play(self, query: str) -> str:
        self.played.append(query)
        return f"{query} ({self.id})"

    def control(self, action: str) -> bool:
        self.controls.append(action)
        return True


def test_hub_prefers_spotify_honours_source_and_routes_controls() -> None:
    hub = MusicHub()
    youtube, spotify = FakeProvider("youtube"), FakeProvider("spotify")
    hub.add(youtube)
    hub.add(spotify)
    result = hub.play(PlayMusicArgs(query="lofi", source=None))
    assert spotify.played == ["lofi"] and result["spoken"] == "Playing lofi on Spotify."
    hub.play(PlayMusicArgs(query="jazz", source="youtube"))
    assert youtube.played == ["jazz"] and spotify.controls == ["stop"]   # switching sources stops the other
    assert hub.control("pause") and youtube.controls == ["pause"]


def test_hub_explains_when_nothing_is_connected() -> None:
    hub = MusicHub()
    hub.add(FakeProvider("youtube", available=False))
    with pytest.raises(ConnectorError, match="Connectors page"):
        hub.play(PlayMusicArgs(query="lofi", source=None))
    assert hub.control("pause") is False


def test_youtube_connector_streams_search_result(monkeypatch: pytest.MonkeyPatch) -> None:
    gate = EgressGate(load_policy_config(str(POLICY)), PrivacyMode.LOCAL_PLUS_WEB)
    monkeypatch.setattr(yt, "search_audio", lambda g, q: yt.AudioResult(
        title="Lofi Girl - beats", url="https://rr1.googlevideo.com/x", headers={"User-Agent": "x"},
        duration_s=300, webpage=""))
    played: list[Track] = []
    player = type("P", (), {"play": lambda self, t: played.append(t), "active": True})()
    hub = MusicHub()
    connector = YouTubeConnector(gate, hub, player)
    connector.state.connected = True
    assert hub.play(PlayMusicArgs(query="lofi", source=None))["title"] == "Lofi Girl - beats"
    assert played[0].url.startswith("https://rr1.googlevideo.com") and played[0].headers == {"User-Agent": "x"}


# --- Spotify ---

def test_pkce_and_authorize_url() -> None:
    verifier, challenge = pkce_pair()
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert challenge == expected and 43 <= len(verifier) <= 128
    q = parse_qs(urlparse(authorize_url("cid123", challenge, "st")).query)
    assert q["code_challenge_method"] == ["S256"] and q["redirect_uri"] == [spotify_mod.REDIRECT_URI]


class MemorySecrets:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def get_secret(self, key: str) -> str | None: return self.data.get(key)
    def set_secret(self, key: str, value: str) -> None: self.data[key] = value
    def delete_secret(self, key: str) -> None: self.data.pop(key, None)


def test_spotify_refreshes_token_wakes_app_and_plays(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    devices: list[dict[str, Any]] = []

    def fake_token(gate: Any, form: dict[str, str]) -> dict[str, Any]:
        assert form["grant_type"] == "refresh_token" and form["refresh_token"] == "r1"  # noqa: S105
        return {"access_token": "a1", "expires_in": 3600}

    def fake_api(gate: Any, token: str, method: str, path: str, params: Any = None, body: Any = None) -> Any:
        calls.append((method, path))
        if path == "/search":
            return {"tracks": {"items": [{"name": "Blinding Lights", "uri": "spotify:track:1",
                                          "artists": [{"name": "The Weeknd"}]}]}}
        if path == "/me/player/devices":
            return {"devices": devices}
        return None

    monkeypatch.setattr(spotify_http, "token", fake_token)
    monkeypatch.setattr(spotify_http, "api", fake_api)
    monkeypatch.setattr("rei.connectors.spotify.time.sleep", lambda s: devices.append({"id": "pc", "is_active": False}))
    secrets_store = MemorySecrets()
    secrets_store.set_secret(spotify_mod.REFRESH_ENTRY, "r1")
    hub = MusicHub()
    connector = SpotifyConnector(EgressGate(load_policy_config(str(POLICY)), PrivacyMode.LOCAL_PLUS_WEB),
                                 secrets_store, hub)
    woke: list[bool] = []
    monkeypatch.setattr(connector, "_wake_desktop_app", lambda: woke.append(True))
    connector.state.connected = True
    connector.state.config = {"client_id": "c" * 32}

    result = hub.play(PlayMusicArgs(query="blinding lights", source="spotify"))
    assert result["title"] == "Blinding Lights by The Weeknd"
    assert woke == [True] and ("PUT", "/me/player/play") in calls


def test_spotify_premium_error_is_explained(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_api(*a: Any, **k: Any) -> Any:
        raise spotify_http.SpotifyHTTPError(403, "Player command failed", "PREMIUM_REQUIRED")

    monkeypatch.setattr(spotify_http, "api", fake_api)
    connector = SpotifyConnector(EgressGate(load_policy_config(str(POLICY)), PrivacyMode.LOCAL_PLUS_WEB),
                                 MemorySecrets(), MusicHub())
    connector._access, connector._expires = "a", time.monotonic() + 100
    with pytest.raises(ConnectorError, match="Premium"):
        connector.control("pause")


@pytest.mark.parametrize("title, spoken", [
    ("1 A.M Study Session 📚 [lofi hip hop]", "1 A.M Study Session"),
    ("The Weeknd - Blinding Lights (Official Video)", "The Weeknd - Blinding Lights"),
    ("Blinding Lights by The Weeknd", "Blinding Lights by The Weeknd"),
])
def test_speakable_titles(title: str, spoken: str) -> None:
    from rei.connectors.music import speakable
    assert speakable(title) == spoken
