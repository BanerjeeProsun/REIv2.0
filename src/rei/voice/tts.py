import asyncio
import math
import numpy as np
import sounddevice as sd # type: ignore
from pathlib import Path
from typing import Callable
from rei.core.cancellation import CancelToken

LevelCallback = Callable[[float], None]

# Envelope / UI update resolution for the speaking animation
FRAME_S = 0.05
# Extra time after the clip's nominal duration before playback is force-stopped
PLAYBACK_TAIL_S = 0.25


class TTSError(Exception):
    pass


def amplitude_envelope(audio: np.ndarray, sample_rate: int, frame_s: float = FRAME_S) -> np.ndarray:
    """Normalised 0..1 RMS envelope, one value per frame_s of audio."""
    samples = np.asarray(audio, dtype=np.float32).reshape(-1)
    frame = max(1, int(sample_rate * frame_s))
    n_frames = max(1, math.ceil(len(samples) / frame))
    padded = np.zeros(n_frames * frame, dtype=np.float32)
    padded[: len(samples)] = samples
    rms = np.sqrt(np.mean(padded.reshape(n_frames, frame) ** 2, axis=1))
    peak = float(rms.max()) if rms.size else 0.0
    if peak <= 1e-6:
        return np.zeros(n_frames, dtype=np.float32)
    return np.clip(rms / peak, 0.0, 1.0).astype(np.float32)


class TextToSpeech:
    """Local Text-to-Speech (VOI-01, VOI-05)."""

    def __init__(self, model_path: Path | None = None, voice: str = "af_maple", sample_rate: int = 24000) -> None:
        self.model_path = model_path
        self.voice = voice
        self.sample_rate = sample_rate

        self.kokoro = None
        if model_path and model_path.exists():
            try:
                from kokoro_onnx import Kokoro
                # Need voices.bin in the same dir as the model or specified
                voices_path = model_path.parent / "voices.bin"

                self.kokoro = Kokoro(str(model_path), str(voices_path))
                print("Loaded Kokoro TTS.")
            except Exception as e:
                print(f"Failed to load Kokoro: {e}")

    async def speak(
        self,
        text: str,
        cancel_token: CancelToken,
        on_level: LevelCallback = lambda level: None,
    ) -> None:
        cancel_token.raise_if_cancelled()
        if self.kokoro:
            audio, sample_rate = await self.synthesize(text)
            cancel_token.raise_if_cancelled()
            await self.play(audio, sample_rate, cancel_token, on_level)
        else:
            await self._speak_sapi(text, cancel_token, on_level)

    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        if not self.kokoro:
            raise TTSError("Kokoro is not loaded")
        kokoro = self.kokoro

        def _synth() -> tuple[np.ndarray, int]:
            samples, sample_rate = kokoro.create(text, voice=self.voice, speed=1.0, lang="en-us")
            return samples, int(sample_rate)

        try:
            return await asyncio.get_running_loop().run_in_executor(None, _synth)
        except Exception as e:
            raise TTSError(f"Kokoro synthesis failed: {e}")

    async def play(
        self,
        audio: np.ndarray,
        sample_rate: int,
        cancel_token: CancelToken,
        on_level: LevelCallback = lambda level: None,
    ) -> None:
        """Plays audio without blocking the event loop or any worker thread.

        sd.play() is non-blocking; instead of sd.wait() (which can hang when
        another stream replaces the global one) we wait out the clip's known
        duration on the event loop, feed the amplitude envelope to on_level,
        and always sd.stop() at the end. Playback therefore always terminates.
        """
        envelope = amplitude_envelope(audio, sample_rate)
        duration = len(np.asarray(audio).reshape(-1)) / float(sample_rate)
        loop = asyncio.get_running_loop()

        try:
            sd.play(audio, sample_rate)
        except Exception as e:
            raise TTSError(f"Audio output failed: {e}")

        start = loop.time()
        try:
            while not cancel_token.is_cancelled:
                elapsed = loop.time() - start
                if elapsed >= duration + PLAYBACK_TAIL_S:
                    break
                idx = int(elapsed / FRAME_S)
                on_level(float(envelope[idx]) if idx < len(envelope) else 0.0)
                await asyncio.sleep(FRAME_S)
        finally:
            self.stop_immediately()
            on_level(0.0)

    async def _speak_sapi(self, text: str, cancel_token: CancelToken, on_level: LevelCallback) -> None:
        """Fallback to pyttsx3 (SAPI5).

        init/say/runAndWait all run in the same worker thread: SAPI's COM
        objects are apartment-bound and silently fail if used across threads.
        """
        def _speak_sync() -> None:
            import pyttsx3 # type: ignore
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(None, _speak_sync)
        timeout = len(text) * 0.08 + 5.0
        start = loop.time()
        try:
            while not task.done():
                if cancel_token.is_cancelled or loop.time() - start > timeout:
                    break
                # No waveform available: synthetic pulse keeps the orb alive
                on_level(0.35 + 0.25 * math.sin((loop.time() - start) * 9.0))
                await asyncio.sleep(FRAME_S)
        finally:
            on_level(0.0)

    def stop_immediately(self) -> None:
        """Hard stop for barge-in (VOI-05)."""
        try:
            sd.stop()
        except Exception as e:
            print(f"Audio stop failed: {e}")
