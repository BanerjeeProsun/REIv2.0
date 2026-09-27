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
        self._state = np.zeros((2, 1, 128), dtype=np.float32)

    def process_chunk(self, audio_chunk: np.ndarray) -> bool:
        """Process a chunk of audio and return True if speech is detected.
        
        audio_chunk must be a 1D float32 array normalized between -1 and 1.
        """
        # Ensure correct shape (batch_size, sequence_length)
        input_data = audio_chunk.reshape(1, -1).astype(np.float32)
        
        ort_inputs = {
            'input': input_data,
            'sr': np.array(self.sample_rate, dtype=np.int64),
            'state': self._state
        }
        
        try:
            ort_outs = self.session.run(None, ort_inputs)
            out, self._state = ort_outs[0], ort_outs[1]
        except Exception as e:
            # Fallback if somehow using v3
            print(f"VAD session run error: {e}")
            return False
        
        speech_prob = out.squeeze()
        self._last_prob = float(speech_prob)
        
        return bool(speech_prob > self.threshold)
