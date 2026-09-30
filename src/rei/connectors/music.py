from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field

from rei.capabilities.spec import CapabilitySpec, DataClass, RateLimit, RiskTier
from rei.connectors.base import ConnectorError
from rei.policy.schemas import PrivacyMode


class PlayMusicArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(..., min_length=1, max_length=200)
    source: Optional[Literal["youtube", "spotify"]] = None


music_play_spec = CapabilitySpec(
    id="music.play",
    version=1,
    summary="Play music: a song, artist, album, genre or playlist (on YouTube or Spotify)",
    tier=RiskTier.R1,
    args_model=PlayMusicArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=True,
    reversible=True,
    allow_when_tainted=False,
    confirm_template='Play "{query}"',
    timeout_s=45.0,
    rate_limit=RateLimit(limit=20, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


class MusicProvider(Protocol):
    id: str

    @property
    def available(self) -> bool: ...
    def play(self, query: str) -> str: ...          # returns the title now playing
    def control(self, action: str) -> bool: ...     # pause/play/next/prev/stop


class MusicHub:
    """Routes "play ..." to the connected music source and remembers which one
    is playing so "pause" / "next" go to the right place."""

    def __init__(self) -> None:
        self.providers: dict[str, MusicProvider] = {}
        self.current: Optional[str] = None
        self.now_playing = ""

    def add(self, provider: MusicProvider) -> None:
        self.providers[provider.id] = provider

    def _pick(self, source: Optional[str]) -> MusicProvider:
        if source:
            provider = self.providers.get(source)
            if provider is None or not provider.available:
                raise ConnectorError(f"{source.capitalize()} isn't connected. Connect it on the Connectors page.")
            return provider
        for sid in ("spotify", "youtube"):  # prefer Spotify when both are connected
            provider = self.providers.get(sid)
            if provider is not None and provider.available:
                return provider
        raise ConnectorError("No music service is connected. Connect YouTube or Spotify on the Connectors page.")

    def play(self, args: PlayMusicArgs) -> dict[str, Any]:
        provider = self._pick(args.source)
        if self.current and self.current != provider.id:
            self.control("stop")
        title = provider.play(args.query)
        self.current, self.now_playing = provider.id, title
        where = "on Spotify" if provider.id == "spotify" else ""
        return {"status": "success", "title": title, "source": provider.id,
                "spoken": f"Playing {speakable(title)} {where}".strip() + "."}

    def control(self, action: str) -> bool:
        """Handle media keys for Rei's own music. False if nothing of ours is playing."""
        provider = self.providers.get(self.current or "")
        if provider is None:
            return False
        handled = provider.control(action)
        if handled and action == "stop":
            self.current, self.now_playing = None, ""
        return handled


def speakable(title: str) -> str:
    """'1 A.M Study Session 📚 [lofi hip hop]' -> '1 A.M Study Session' for TTS."""
    import re
    cleaned = re.sub(r"\s*[\[(【].*?[\])】]", "", title)                 # [Official Video], (lyrics)
    cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch in " .,'&-:!?")  # emoji, symbols
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -:|")
    return cleaned or title
