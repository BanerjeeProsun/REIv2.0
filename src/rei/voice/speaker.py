import asyncio
from typing import Callable

from rei.core.cancellation import CancelToken
from rei.voice.aec import EchoCanceller
from rei.voice.tts import TextToSpeech


class Speaker:
    """Single owner of speech output for every path (voice, typed, greeting).

    - Serialises playback so two replies never fight over the audio device.
    - Marks the shared EchoCanceller active so the mic ignores Rei's own voice,
      whichever path triggered the speech.
    - A new say() interrupts the current one (barge-in).
    - Never raises TTS errors to the caller: a failed utterance is logged and
      the turn still completes, so the UI can always leave "Speaking...".
    """

    def __init__(
        self,
        tts: TextToSpeech,
        aec: EchoCanceller,
        on_level: Callable[[float], None] = lambda level: None,
        echo_tail_s: float = 0.4,
    ) -> None:
        self.tts = tts
        self.aec = aec
        self.on_level = on_level
        self.echo_tail_s = echo_tail_s
        self._lock = asyncio.Lock()
        self._current: CancelToken | None = None

    @property
    def is_speaking(self) -> bool:
        return self._current is not None

    def stop(self) -> None:
        if self._current is not None:
            self._current.cancel()
            self.tts.stop_immediately()

    async def say(
        self,
        text: str,
        cancel_token: CancelToken | None = None,
        on_start: Callable[[], None] | None = None,
    ) -> None:
        if not text.strip():
            return
        self.stop()
        token = cancel_token or CancelToken()
        async with self._lock:
            if token.is_cancelled:
                return
            self._current = token
            self.aec.mark_playback_active(True)
            try:
                if on_start:
                    on_start()
                await self.tts.speak(text, token, self.on_level)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"TTS output failed: {e}")
            finally:
                self._current = None
                self.on_level(0.0)
                try:
                    # Give physical speakers time to stop echoing into the mic
                    await asyncio.sleep(self.echo_tail_s)
                finally:
                    self.aec.mark_playback_active(False)
