import asyncio
from collections import deque
import numpy as np
from typing import Callable

from rei.voice.capture import AudioCapture
from rei.voice.vad import VoiceActivityDetector
from rei.voice.stt import SpeechToText
from rei.voice.aec import EchoCanceller
from rei.core.cancellation import CancelToken

# Noise rejection tunables. webrtcvad alone fires on keyboards, fans and taps,
# so a chunk only counts as speech when it is also clearly louder than the
# room's adaptive noise floor.
NOISE_FLOOR_INIT = 0.005     # starting RMS estimate of the room
NOISE_FLOOR_ALPHA = 0.05     # EMA weight per non-speech chunk
NOISE_FLOOR_MAX = 0.1        # never let a loud room disable voice entirely
SPEECH_FLOOR_RATIO = 3.0     # speech must be this many times the floor...
SPEECH_MIN_RMS = 0.01        # ...and at least this loud
# While Rei is speaking the mic hears its own voice (no real AEC), so only
# speech clearly louder than the echo gets through (e.g. a spoken "stop").
PLAYBACK_FLOOR_RATIO = 6.0
PLAYBACK_MIN_RMS = 0.03
ONSET_CHUNKS = 3             # consecutive speech chunks (~90 ms) to start
PREROLL_CHUNKS = 10          # audio kept before onset so words aren't clipped
MIN_VOICED_CHUNKS = 8        # ~240 ms of speech, or it was a noise burst
END_SILENCE_S = 0.6          # pause that ends an utterance
MAX_UTTERANCE_S = 30.0


def chunk_rms(chunk: np.ndarray) -> float:
    samples = np.asarray(chunk, dtype=np.float32).reshape(-1)
    return float(np.sqrt(np.mean(samples ** 2))) if samples.size else 0.0


class VoiceLoop:
    """Manages the voice input pipeline (Capture -> VAD -> STT -> turn runner).

    Speech output is owned by the shared Speaker (rei.voice.speaker), which
    marks the same EchoCanceller for voice, typed and greeting replies.
    """

    def __init__(
        self,
        capture: AudioCapture,
        vad: VoiceActivityDetector,
        stt: SpeechToText,
        aec: EchoCanceller,
        on_utterance: Callable[[str, bool], None],
        on_volume: Callable[[float], None] = lambda v: None,
        on_transcribing: Callable[[], None] = lambda: None,
        on_discard: Callable[[], None] = lambda: None,
    ) -> None:
        self.capture = capture
        self.vad = vad
        self.stt = stt
        self.aec = aec
        self.on_utterance = on_utterance
        self.on_volume = on_volume
        self.on_transcribing = on_transcribing
        self.on_discard = on_discard
        self._running = False

        self.noise_floor = NOISE_FLOOR_INIT
        self._preroll: deque[np.ndarray] = deque(maxlen=PREROLL_CHUNKS)
        self._speech_buffer: list[np.ndarray] = []
        self._onset = 0
        self._voiced = 0
        self._silence_frames = 0
        self._during_playback = False

        chunks_per_s = capture.sample_rate / capture.chunk_size
        self.silence_threshold_chunks = max(1, int(END_SILENCE_S * chunks_per_s))
        self.max_utterance_chunks = int(MAX_UTTERANCE_S * chunks_per_s)

    @property
    def in_utterance(self) -> bool:
        return len(self._speech_buffer) > 0

    async def start(self) -> None:
        self._running = True
        await self.capture.start()

        print("Voice loop started. Listening...")

        while self._running:
            try:
                # Get raw audio chunk from microphone
                chunk = await self.capture.get_chunk()
                self.on_volume(float(np.max(np.abs(chunk))))
                await self.process_chunk(chunk)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Voice loop error: {e}")

        await self.capture.stop()

    def stop(self) -> None:
        self._running = False

    def _is_speech(self, chunk: np.ndarray, rms: float, playback: bool) -> bool:
        if playback:
            gate = max(self.noise_floor * PLAYBACK_FLOOR_RATIO, PLAYBACK_MIN_RMS)
        else:
            gate = max(self.noise_floor * SPEECH_FLOOR_RATIO, SPEECH_MIN_RMS)
        # Cheap energy gate first; the VAD only judges chunks loud enough to matter
        return rms > gate and self.vad.process_chunk(chunk)

    async def process_chunk(self, chunk: np.ndarray) -> None:
        playback = self.aec.should_suppress()
        rms = chunk_rms(chunk)
        is_speech = self._is_speech(chunk, rms, playback)

        if not self.in_utterance:
            self._preroll.append(chunk)
            if is_speech:
                self._onset += 1
                if self._onset >= ONSET_CHUNKS:
                    print("Speech started...")
                    self._speech_buffer = list(self._preroll)
                    self._voiced = self._onset
                    self._silence_frames = 0
                    self._during_playback = playback
                    self._preroll.clear()
            else:
                self._onset = 0
                # Learn the room only from quiet, non-playback audio
                if not playback:
                    self.noise_floor = min(
                        NOISE_FLOOR_MAX,
                        (1 - NOISE_FLOOR_ALPHA) * self.noise_floor + NOISE_FLOOR_ALPHA * rms,
                    )
            return

        self._speech_buffer.append(chunk)
        self._during_playback = self._during_playback or playback
        if is_speech:
            self._voiced += 1
            self._silence_frames = 0
        else:
            self._silence_frames += 1

        if (self._silence_frames >= self.silence_threshold_chunks
                or len(self._speech_buffer) >= self.max_utterance_chunks):
            print("Speech ended, processing...")
            await self._handle_utterance()

    def _reset_vad(self) -> None:
        self._speech_buffer = []
        self._preroll.clear()
        self._onset = 0
        self._voiced = 0
        self._silence_frames = 0
        self._during_playback = False
        self.vad.reset()

    async def _handle_utterance(self) -> None:
        if not self._speech_buffer:
            return

        voiced = self._voiced
        during_playback = self._during_playback
        # Concatenate buffered chunks into a single 1D array
        full_audio = np.concatenate(self._speech_buffer).flatten()
        self._reset_vad()

        if voiced < MIN_VOICED_CHUNKS:
            # A tap, cough or click: never worth a transcription
            self.on_discard()
            return

        # STT
        cancel_token = CancelToken()
        try:
            print("Transcribing...")
            self.on_transcribing()
            text = await self.stt.transcribe(full_audio, cancel_token)
            if not text.strip():
                # Nothing usable was heard: return the UI to its rest state
                self.on_discard()
                return

            print(f"Heard: {text}")

            # Hand off without waiting: the turn runs in the background and the
            # mic goes straight back to listening (e.g. for a spoken "yes" or
            # "stop"). during_playback tells the router Rei was talking.
            self.on_utterance(text, during_playback)

        except asyncio.CancelledError:
            print("Voice turn cancelled.")
        except Exception as e:
            print(f"Failed to process utterance: {e}")
            self.on_discard()
        finally:
            self.capture.clear()
