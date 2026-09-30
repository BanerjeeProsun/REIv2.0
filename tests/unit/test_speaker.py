import asyncio
from typing import Any

import numpy as np
import pytest

import rei.voice.tts as tts_module
from rei.core.cancellation import CancelToken
from rei.voice.aec import EchoCanceller
from rei.voice.speaker import Speaker
from rei.voice.tts import TextToSpeech, amplitude_envelope


class FakeSD:
    """sounddevice stand-in whose playback never reports completion."""

    def __init__(self) -> None:
        self.played: list[int] = []
        self.stops = 0

    def play(self, audio: Any, sample_rate: int) -> None:
        self.played.append(len(audio))

    def stop(self) -> None:
        self.stops += 1

    def wait(self) -> None:  # pragma: no cover - must never be called
        raise AssertionError("sd.wait() must not be used")


class FakeKokoro:
    def __init__(self, seconds: float = 0.2) -> None:
        self.seconds = seconds

    def create(self, text: str, voice: str, speed: float, lang: str) -> tuple[np.ndarray, int]:
        n = int(24000 * self.seconds)
        return np.sin(np.linspace(0, 400, n)).astype(np.float32), 24000


@pytest.fixture
def fake_sd(monkeypatch: pytest.MonkeyPatch) -> FakeSD:
    sd = FakeSD()
    monkeypatch.setattr(tts_module, "sd", sd)
    return sd


def _tts(seconds: float = 0.2) -> TextToSpeech:
    tts = TextToSpeech(None)
    tts.kokoro = FakeKokoro(seconds)  # type: ignore[assignment]
    return tts


def test_amplitude_envelope_is_normalised() -> None:
    audio = np.concatenate([np.zeros(2400), np.ones(2400) * 0.2]).astype(np.float32)
    env = amplitude_envelope(audio, 24000)
    assert env.max() == pytest.approx(1.0)
    assert env[0] == 0.0


@pytest.mark.asyncio
async def test_playback_terminates_without_device_completion(fake_sd: FakeSD) -> None:
    levels: list[float] = []
    aec = EchoCanceller()
    speaker = Speaker(_tts(0.2), aec, on_level=levels.append, echo_tail_s=0.01)
    started: list[bool] = []

    await asyncio.wait_for(speaker.say("hello", on_start=lambda: started.append(aec.should_suppress())), timeout=3)

    assert started == [True]          # AEC active while speaking
    assert not aec.should_suppress()  # and released afterwards
    assert fake_sd.played and fake_sd.stops >= 1
    assert max(levels) > 0.5 and levels[-1] == 0.0
    assert not speaker.is_speaking


@pytest.mark.asyncio
async def test_new_say_interrupts_current_one(fake_sd: FakeSD) -> None:
    speaker = Speaker(_tts(5.0), EchoCanceller(), echo_tail_s=0.01)
    first = asyncio.ensure_future(speaker.say("a long reply"))
    await asyncio.sleep(0.3)
    assert speaker.is_speaking

    await asyncio.wait_for(speaker.say("new reply"), timeout=8)
    await asyncio.wait_for(first, timeout=1)
    assert len(fake_sd.played) == 2


@pytest.mark.asyncio
async def test_tts_failure_does_not_raise(fake_sd: FakeSD) -> None:
    class Broken(FakeKokoro):
        def create(self, *a: Any, **k: Any) -> tuple[np.ndarray, int]:
            raise RuntimeError("boom")

    tts = TextToSpeech(None)
    tts.kokoro = Broken()  # type: ignore[assignment]
    aec = EchoCanceller()
    speaker = Speaker(tts, aec, echo_tail_s=0.01)
    await speaker.say("hi")
    assert not aec.should_suppress()


@pytest.mark.asyncio
async def test_cancel_token_stops_playback(fake_sd: FakeSD) -> None:
    tts = _tts(5.0)
    token = CancelToken()
    task = asyncio.ensure_future(tts.speak("long", token))
    await asyncio.sleep(0.2)
    token.cancel()
    await asyncio.wait_for(task, timeout=1)
    assert fake_sd.stops >= 1
