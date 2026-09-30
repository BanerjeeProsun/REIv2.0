import numpy as np
import webrtcvad  # type: ignore


class VADError(Exception):
    pass


class VoiceActivityDetector:
    """WebRTC VAD wrapper for precise voice detection (VOI-01)."""

    def __init__(self, threshold: int = 3, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        # Ensure threshold is 0, 1, 2, or 3 for WebRTC
        level = max(0, min(3, int(round(threshold))))
        self.vad = webrtcvad.Vad(level)
        
    def reset(self) -> None:
        pass

    def process_chunk(self, audio_chunk: np.ndarray) -> bool:
        # Convert float32 [-1.0, 1.0] to int16 PCM for WebRTC
        pcm = (audio_chunk.flatten() * 32767).astype(np.int16).tobytes()
        
        try:
            return self.vad.is_speech(pcm, self.sample_rate)
        except Exception:
            return False
