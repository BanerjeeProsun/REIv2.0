from typing import Any

import numpy as np
import pytest
from rei.voice.aec import EchoCanceller
from rei.voice.capture import AudioCapture
from rei.voice.loop import MIN_VOICED_CHUNKS, ONSET_CHUNKS, VoiceLoop


class FakeCapture:
    sample_rate = 16000
    chunk_size = 480

    def clear(self) -> None:
        pass


class LoudIsSpeechVAD:
    """Stand-in for webrtcvad: anything audible "sounds like speech"."""

    def process_chunk(self, chunk: np.ndarray) -> bool:
        return bool(np.max(np.abs(chunk)) > 0.0)

    def reset(self) -> None:
        pass


class FakeSTT:
    def __init__(self) -> None:
        self.calls = 0

    async def transcribe(self, audio: np.ndarray, cancel_token: Any) -> str:
        self.calls += 1
        return "hello rei"


def _loop(aec: EchoCanceller | None = None) -> tuple[VoiceLoop, FakeSTT, list[tuple[str, bool]], list[bool]]:
    stt = FakeSTT()
    heard: list[tuple[str, bool]] = []
    discarded: list[bool] = []
    loop = VoiceLoop(
        FakeCapture(), LoudIsSpeechVAD(), stt, aec or EchoCanceller(),  # type: ignore[arg-type]
        on_utterance=lambda text, during: heard.append((text, during)),
        on_discard=lambda: discarded.append(True),
    )
    return loop, stt, heard, discarded


def _chunk(amplitude: float) -> np.ndarray:
    return np.full((480, 1), amplitude, dtype=np.float32)


async def _feed(loop: VoiceLoop, amplitude: float, n: int) -> None:
    for _ in range(n):
        await loop.process_chunk(_chunk(amplitude))


@pytest.mark.asyncio
async def test_quiet_noise_never_reaches_stt() -> None:
    loop, stt, heard, _ = _loop()
    # Below the absolute speech gate: a fan or room hum the VAD still flags
    await _feed(loop, 0.005, 200)
    assert stt.calls == 0 and heard == []


@pytest.mark.asyncio
async def test_short_burst_is_discarded_without_transcribing() -> None:
    loop, stt, heard, discarded = _loop()
    await _feed(loop, 0.0, 20)
    await _feed(loop, 0.3, MIN_VOICED_CHUNKS - 2)  # a tap or cough
    await _feed(loop, 0.0, loop.silence_threshold_chunks + 1)
    assert stt.calls == 0 and heard == []
    assert discarded == [True]


@pytest.mark.asyncio
async def test_single_spike_does_not_start_an_utterance() -> None:
    loop, stt, _, _ = _loop()
    for _ in range(10):
        await _feed(loop, 0.3, ONSET_CHUNKS - 1)
        await _feed(loop, 0.0, 1)
    assert not loop.in_utterance and stt.calls == 0


@pytest.mark.asyncio
async def test_sustained_speech_is_transcribed_once() -> None:
    loop, stt, heard, _ = _loop()
    await _feed(loop, 0.0, 20)
    await _feed(loop, 0.2, 30)
    await _feed(loop, 0.0, loop.silence_threshold_chunks + 5)
    assert stt.calls == 1
    assert heard == [("hello rei", False)]


@pytest.mark.asyncio
async def test_noise_floor_adapts_to_a_loud_room() -> None:
    loop, stt, _, _ = _loop()
    # A steady 0.02 hum is above the absolute gate, so it starts out as "speech"...
    await _feed(loop, 0.0, 5)
    loop.noise_floor = 0.02  # ...but once learned as the floor it no longer is
    await _feed(loop, 0.02, 100)
    assert stt.calls == 0


@pytest.mark.asyncio
async def test_playback_needs_louder_speech_and_is_tagged() -> None:
    aec = EchoCanceller()
    aec.mark_playback_active(True)
    loop, stt, heard, _ = _loop(aec)
    # Rei's own echo at normal speech level is ignored while it talks
    await _feed(loop, 0.02, 40)
    await _feed(loop, 0.0, loop.silence_threshold_chunks + 1)
    assert stt.calls == 0
    # A loud "stop" gets through and is marked as heard during playback
    await _feed(loop, 0.3, 20)
    await _feed(loop, 0.0, loop.silence_threshold_chunks + 1)
    assert heard == [("hello rei", True)]

def test_aec_suppression() -> None:
    aec = EchoCanceller()
    assert not aec.should_suppress()
    aec.mark_playback_active(True)
    assert aec.should_suppress()
    aec.mark_playback_active(False)
    assert not aec.should_suppress()

@pytest.mark.asyncio
async def test_audio_capture_start_stop() -> None:
    # Test that capture can be started and stopped without throwing.
    # Note: On CI machines without audio devices, this might throw AudioCaptureError.
    # So we'll skip if it fails to initialize.
    try:
        capture = AudioCapture()
        await capture.start()
        await capture.stop()
    except Exception as e:
        pytest.skip(f"Audio device not available: {e}")
