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

    def __init__(self, model_path: Path | None = None, voice: str = "af_maple", sample_rate: int = 24000) -> None:
        self.model_path = model_path
        self.voice = voice
        self.sample_rate = sample_rate
        self._playback_task: asyncio.Future[Any] | None = None
        
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

    async def speak(self, text: str, cancel_token: CancelToken) -> None:
        cancel_token.raise_if_cancelled()
        
        loop = asyncio.get_running_loop()
        
        if self.kokoro:
            # 1. Synthesize audio
            def _synth() -> np.ndarray:
                samples, _ = self.kokoro.create(text, voice=self.voice, speed=1.0, lang="en-us")
                return samples
            
            try:
                audio = await loop.run_in_executor(None, _synth)
            except Exception as e:
                raise TTSError(f"Kokoro synthesis failed: {e}")
                
            cancel_token.raise_if_cancelled()
            await self._play_audio(audio, cancel_token)
        else:
            # Fallback to pyttsx3 (SAPI5)
            import pyttsx3 # type: ignore
            engine = pyttsx3.init()
            # Run blocking speak in executor
            def _speak_sync() -> None:
                engine.say(text)
                engine.runAndWait()
            self._playback_task = loop.run_in_executor(None, _speak_sync)
            try:
                await asyncio.wait([self._playback_task], return_when=asyncio.FIRST_COMPLETED)
            except asyncio.CancelledError:
                engine.stop()
                raise
            finally:
                self._playback_task = None


    async def _play_audio(self, audio: np.ndarray, cancel_token: CancelToken) -> None:
        """Plays audio using sounddevice, allowing barge-in cancellation."""
        loop = asyncio.get_running_loop()

        def _play_sync() -> None:
            sd.play(audio, self.sample_rate)
            sd.wait() # Blocking wait

        self._playback_task = loop.run_in_executor(None, _play_sync)
        
        try:
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
