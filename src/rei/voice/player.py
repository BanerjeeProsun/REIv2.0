"""In-app music player: streams audio (e.g. from YouTube) and plays it inside
Rei, with no browser or app window.

A decoder thread turns the stream into 48 kHz stereo float frames and fills a
small buffer; a sounddevice output callback drains it. This stream is separate
from the TTS output, so Rei can talk over music (which is ducked meanwhile).
"""
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

RATE = 48000
CHANNELS = 2
BLOCK = 1024


@dataclass
class Track:
    title: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    source: str = "youtube"


class MusicPlayer:
    def __init__(
        self,
        opener: Callable[[str, dict[str, str]], Any],
        on_change: Callable[[], None] = lambda: None,
        output_factory: Optional[Callable[..., Any]] = None,
    ) -> None:
        """opener(url, headers) returns a PyAV container (see egress/stream.py)."""
        self.opener = opener
        self.on_change = on_change
        self._output_factory = output_factory
        self.track: Optional[Track] = None
        self.volume = 0.8
        self._duck = 1.0
        self._duck_target = 1.0
        self._paused = False
        self._buffer: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=int(3 * RATE / BLOCK))
        self._pending = np.zeros((0, CHANNELS), dtype=np.float32)
        self._stop = threading.Event()
        self._finished = threading.Event()
        self._decoder: Optional[threading.Thread] = None
        self._stream: Any = None
        self._ending = False
        self.error = ""

    # --- state ---

    @property
    def active(self) -> bool:
        return self.track is not None

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def title(self) -> str:
        return self.track.title if self.track else ""

    # --- control ---

    def play(self, track: Track) -> None:
        self.stop(notify=False)
        self.track = track
        self.error = ""
        self._paused = False
        self._stop = threading.Event()
        self._finished = threading.Event()
        self._ending = False
        self._decoder = threading.Thread(target=self._decode, args=(track, self._stop), daemon=True)
        self._decoder.start()
        self._open_output()
        self.on_change()

    def pause(self) -> None:
        if self.active:
            self._paused = True
            self.on_change()

    def resume(self) -> None:
        if self.active:
            self._paused = False
            self.on_change()

    def toggle(self) -> None:
        self.resume() if self._paused else self.pause()

    def stop(self, notify: bool = True) -> None:
        self._stop.set()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"[player] closing output: {e}")
            self._stream = None
        self._drain()
        was_active = self.track is not None
        self.track = None
        self._paused = False
        if notify and was_active:
            self.on_change()

    def duck(self, on: bool) -> None:
        """Lower the music while Rei listens or speaks."""
        self._duck_target = 0.25 if on else 1.0

    def set_volume(self, level: float) -> None:
        self.volume = max(0.0, min(1.0, level))

    # --- internals ---

    def _drain(self) -> None:
        while not self._buffer.empty():
            try:
                self._buffer.get_nowait()
            except queue.Empty:
                break
        self._pending = np.zeros((0, CHANNELS), dtype=np.float32)

    def _open_output(self) -> None:
        factory = self._output_factory
        if factory is None:
            import sounddevice as sd  # type: ignore
            factory = sd.OutputStream
        self._stream = factory(samplerate=RATE, channels=CHANNELS, dtype="float32",
                               blocksize=BLOCK, callback=self._callback)
        self._stream.start()

    def _decode(self, track: Track, stop: threading.Event) -> None:
        try:
            import av
            container = self.opener(track.url, track.headers)
            try:
                stream = next(s for s in container.streams if s.type == "audio")
                resampler = av.AudioResampler(format="flt", layout="stereo", rate=RATE)
                for packet in container.demux(stream):
                    if stop.is_set():
                        return
                    for frame in packet.decode():
                        for out in resampler.resample(frame):
                            pcm = out.to_ndarray().reshape(-1, CHANNELS).astype(np.float32)
                            self._put(pcm, stop)
                for out in resampler.resample(None):
                    self._put(out.to_ndarray().reshape(-1, CHANNELS).astype(np.float32), stop)
            finally:
                container.close()
        except Exception as e:
            if not stop.is_set():
                self.error = f"Playback failed: {e}"
                print(f"[player] {self.error}")
        finally:
            self._finished.set()

    def _put(self, pcm: np.ndarray, stop: threading.Event) -> None:
        while not stop.is_set():
            try:
                self._buffer.put(pcm, timeout=0.2)
                return
            except queue.Full:
                continue

    def _callback(self, outdata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        # Smoothly approach the duck target (~100 ms) to avoid clicks
        self._duck += (self._duck_target - self._duck) * 0.3
        if self._paused:
            outdata.fill(0)
            return
        out = self._pending
        while len(out) < frames:
            try:
                out = np.concatenate([out, self._buffer.get_nowait()])
            except queue.Empty:
                break
        n = min(frames, len(out))
        outdata[:n] = out[:n] * (self.volume * self._duck)
        outdata[n:] = 0
        self._pending = out[n:]
        if n == 0 and not self._ending and self._finished.is_set() and self._buffer.empty():
            self._ending = True
            # Track ended: stop from outside the audio thread
            threading.Thread(target=self._ended, daemon=True).start()

    def _ended(self) -> None:
        time.sleep(0.05)
        if self.track is not None and self._finished.is_set() and self._buffer.empty():
            self.stop()
