from typing import Any, Callable

from rei.capabilities.spec import CapabilitySpec
from rei.connectors.base import Connector, ConnectorError
from rei.connectors.music import MusicHub, music_play_spec
from rei.egress import yt
from rei.egress.gate import EgressGate
from rei.voice.player import MusicPlayer, Track


class YouTubeConnector(Connector):
    """Plays YouTube audio inside Rei (no browser) via yt-dlp."""

    id = "youtube"
    name = "YouTube Music"
    description = "Play songs, artists and mixes from YouTube, right inside Rei."
    fields = ()
    note = ("Uses yt-dlp to stream audio. This goes against YouTube's terms of service: "
            "personal use only, and it may stop working when YouTube changes.")

    def __init__(self, gate: EgressGate, hub: MusicHub, player: MusicPlayer) -> None:
        super().__init__()
        self.gate = gate
        self.hub = hub
        self.player = player
        hub.add(self)

    @property
    def available(self) -> bool:
        return self.state.connected

    def connect(self, params: dict[str, str]) -> None:
        try:
            import yt_dlp  # type: ignore  # noqa: F401
        except ImportError as e:
            raise ConnectorError("yt-dlp isn't installed yet. Run: uv add yt-dlp") from e
        self.state.config = {"detail": "Streams inside Rei"}
        self.state.detail = "Streams inside Rei"

    def disconnect(self) -> None:
        if self.hub.current == self.id:
            self.hub.control("stop")
        self.state.config = {}

    def egress_hosts(self) -> set[str]:
        return set(yt.HOSTS)

    def capabilities(self) -> list[tuple[CapabilitySpec, Callable[..., Any]]]:
        return [(music_play_spec, self.hub.play)]

    # --- MusicProvider ---

    def play(self, query: str) -> str:
        try:
            result = yt.search_audio(self.gate, query)
        except yt.YouTubeError as e:
            raise ConnectorError(str(e)) from e
        self.player.play(Track(title=result.title, url=result.url, headers=result.headers, source=self.id))
        return result.title

    def control(self, action: str) -> bool:
        if not self.player.active:
            return False
        if action == "pause":
            self.player.pause()
        elif action == "play":
            self.player.resume()
        elif action == "stop":
            self.player.stop()
        else:
            return False  # next/prev: no queue for YouTube yet
        return True
