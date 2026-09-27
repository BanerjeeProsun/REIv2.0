import asyncio
import numpy as np
from faster_whisper import WhisperModel # type: ignore
from rei.core.cancellation import CancelToken

class STTError(Exception):
    pass

class SpeechToText:
    """Local Speech-to-Text using faster-whisper (VOI-01)."""

    def __init__(self, model_size: str = "base") -> None:
        try:
            print("Loading Whisper on GPU (CUDA)...")
            self.model = WhisperModel(model_size, device="cuda", compute_type="float16")
            # Pre-warm the model
            dummy_audio = np.zeros(16000, dtype=np.float32)
            self.model.transcribe(dummy_audio, beam_size=1)
            print("Whisper GPU Active.")
        except Exception as e:
            print(f"GPU fallback triggered: {e}. Falling back to CPU...")
            try:
                self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
                # Pre-warm the model
                dummy_audio = np.zeros(16000, dtype=np.float32)
                self.model.transcribe(dummy_audio, beam_size=1)
                print("Whisper CPU Active.")
            except Exception as e2:
                raise STTError(f"Failed to load Whisper model: {e2}")

    async def transcribe(self, audio: np.ndarray, cancel_token: CancelToken) -> str:
        """Transcribe an audio chunk. Audio must be 16kHz float32."""
        cancel_token.raise_if_cancelled()
        
        # Run transcription in a thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        
        def _transcribe_sync() -> str:
            segments, _ = self.model.transcribe(audio, beam_size=5)
            text = "".join(segment.text for segment in segments)
            return text.strip()

        try:
            text = await loop.run_in_executor(None, _transcribe_sync)
            cancel_token.raise_if_cancelled()
            return text
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise STTError(f"Transcription failed: {e}")
