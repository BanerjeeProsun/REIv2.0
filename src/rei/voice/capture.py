import asyncio
import sounddevice as sd # type: ignore
import numpy as np
from typing import Any

class AudioCaptureError(Exception):
    pass

class AudioCapture:
    """Captures raw audio from the microphone into an asyncio queue."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 480) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.queue: asyncio.Queue[np.ndarray] = asyncio.Queue(maxsize=100) # Bounded queue (CON-01)
        self.stream: sd.InputStream | None = None
        self.loop = asyncio.get_running_loop()

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: dict[str, Any], status: sd.CallbackFlags
    ) -> None:
        if status and status.input_overflow:
            pass # ignore expected overflow
        elif status:
            print(f"Audio capture warning: {status}")
            
        def _safe_put():
            try:
                self.queue.put_nowait(indata.copy())
            except asyncio.QueueFull:
                pass
                
        self.loop.call_soon_threadsafe(_safe_put)

    def clear(self) -> None:
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def start(self) -> None:
        if self.stream is not None:
            return

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self.stream.start()
        except Exception as e:
            raise AudioCaptureError(f"Failed to start microphone: {e}")

    async def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    async def get_chunk(self) -> np.ndarray:
        return await self.queue.get()
