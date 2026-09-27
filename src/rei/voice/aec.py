class EchoCanceller:
    """Simple echo cancellation stub (VOI-02).
    
    Marks frames during TTS playback so VAD ignores them.
    """
    def __init__(self) -> None:
        self._playback_active = False

    def mark_playback_active(self, active: bool) -> None:
        self._playback_active = active

    def should_suppress(self) -> bool:
        return self._playback_active
