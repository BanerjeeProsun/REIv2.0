import numpy as np
import onnxruntime as ort # type: ignore
from pathlib import Path

class VADError(Exception):
    pass

class VoiceActivityDetector:
    """Silero VAD wrapper for precise voice detection (VOI-01)."""

    def __init__(self, model_path: Path, threshold: float = 0.5, sample_rate: int = 16000) -> None:
        if not model_path.exists():
            raise VADError(f"VAD model not found at {model_path}")
            
        self.threshold = threshold
        self.sample_rate = sample_rate
        
        # Initialize ONNX Runtime session
        options = ort.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        
        self.session = ort.InferenceSession(str(model_path), sess_options=options, providers=['CPUExecutionProvider'])
        self.reset()
        
    def reset(self) -> None:
        """Reset the internal RNN state."""
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)

    def process_chunk(self, audio_chunk: np.ndarray) -> bool:
        """Process a chunk of audio and return True if speech is detected.
        
        audio_chunk must be a 1D float32 array normalized between -1 and 1.
        """
        # Ensure correct shape (batch_size, sequence_length)
        input_data = audio_chunk.reshape(1, -1).astype(np.float32)
        
        ort_inputs = {
            'input': input_data,
            'sr': np.array(self.sample_rate, dtype=np.int64),
            'h': self._h,
            'c': self._c
        }
        
        ort_outs = self.session.run(None, ort_inputs)
        out, self._h, self._c = ort_outs
        
        speech_prob = out.squeeze()
        return bool(speech_prob > self.threshold)
