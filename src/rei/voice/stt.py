import asyncio
import numpy as np
import os
import site
from pathlib import Path

# Add pip-installed NVIDIA DLLs to PATH for CTranslate2 GPU support
try:
    for sp in site.getsitepackages():
        nvidia_base = Path(sp) / "nvidia"
        cublas_path = nvidia_base / "cublas" / "bin"
        cudnn_path = nvidia_base / "cudnn" / "bin"
        if cublas_path.exists() and cudnn_path.exists():
            os.environ["PATH"] = f"{cublas_path};{cudnn_path};{os.environ.get('PATH', '')}"
            break
except Exception:
    pass

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
            
            # Filter common Whisper hallucinations
            clean_text = text.strip()
            hallucinations = ["Thank you.", "I didn't quite catch that.", "Bye.", "Thanks for watching!", "Amara.org", "You", "Thank you", ".", ". . . ."]
            if clean_text in hallucinations:
                return ""
            
            return clean_text
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise STTError(f"Transcription failed: {e}")
