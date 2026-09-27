import numpy as np
import webrtcvad # type: ignore
from pathlib import Path

class VADError(Exception):
    pass

class VoiceActivityDetector:
    """WebRTC VAD wrapper for precise voice detection (VOI-01)."""

    def __init__(self, model_path: Path | None = None, threshold: float = 2, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(int(threshold))
        self._last_prob = 0.0 # dummy for debug prints
        
    def reset(self) -> None:
        pass

    def process_chunk(self, audio_chunk: np.ndarray) -> bool:
        # Convert float32 [-1.0, 1.0] to int16 PCM for WebRTC
        pcm = (audio_chunk.flatten() * 32767).astype(np.int16).tobytes()
        
        try:
            return self.vad.is_speech(pcm, self.sample_rate)
        except Exception:
            return False
