import asyncio
import numpy as np
import sounddevice as sd # type: ignore
from pathlib import Path
from typing import Any
from rei.core.cancellation import CancelToken

class TTSError(Exception):
    pass

class TextToSpeech:
    """Local Text-to-Speech (VOI-01, VOI-05)."""

    def __init__(self, model_path: Path | None = None, voice: str = "af_heart", sample_rate: int = 24000) -> None:
        self.model_path = model_path
        self.voice = voice
        self.sample_rate = sample_rate
        self.stream: sd.OutputStream | None = None
        self._playback_task: asyncio.Future[Any] | None = None

        if model_path:
            # Here we would initialize the real Kokoro ONNX model
            # For the current phase demo, we just stub it unless weights are provided
            pass

    async def speak(self, text: str, cancel_token: CancelToken) -> None:
        """Synthesize and play audio for the given text."""
        cancel_token.raise_if_cancelled()
        
        # 1. Synthesize audio (mocked for now to avoid large model downloads in CI)
        # In a real run, this calls the Kokoro model.
        audio = self._synthesize(text)
        
        # 2. Play audio
        cancel_token.raise_if_cancelled()
        await self._play_audio(audio, cancel_token)

    def _synthesize(self, text: str) -> np.ndarray:
        """Mock synthesis: generates a simple 440Hz beep scaled by text length."""
        duration = min(len(text) * 0.05, 3.0) # 50ms per character, max 3 seconds
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # A simple beep
        note = np.sin(440 * 2 * np.pi * t)
        
        # Envelope to avoid clicks
        fade_len = int(0.05 * self.sample_rate)
        if len(note) > fade_len * 2:
            fade_in = np.linspace(0, 1, fade_len)
            fade_out = np.linspace(1, 0, fade_len)
            note[:fade_len] *= fade_in
            note[-fade_len:] *= fade_out
            
        return note.astype(np.float32)

    async def _play_audio(self, audio: np.ndarray, cancel_token: CancelToken) -> None:
        """Plays audio using sounddevice, allowing barge-in cancellation."""
        loop = asyncio.get_running_loop()
        
        def _callback(outdata: np.ndarray, frames: int, time: dict[str, Any], status: sd.CallbackFlags) -> None:
            if status:
                print(f"TTS playback warning: {status}")
            
            # This is a simplification. A real implementation needs a ring buffer.
            # For now we use sd.play which is easier but blocking, so we'll run it in an executor.
            pass

        def _play_sync() -> None:
            sd.play(audio, self.sample_rate)
            sd.wait() # Blocking wait

        self._playback_task = loop.run_in_executor(None, _play_sync)
        
        try:
            # Wait for playback to finish, or cancellation
            done, pending = await asyncio.wait(
                [self._playback_task],
                timeout=None,
                return_when=asyncio.FIRST_COMPLETED
            )
        except asyncio.CancelledError:
            self.stop_immediately()
            raise
        finally:
            self._playback_task = None

    def stop_immediately(self) -> None:
        """Hard stop for barge-in (VOI-05)."""
        sd.stop()
