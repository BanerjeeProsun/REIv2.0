import asyncio
from typing import Any

import pytest

from rei.confirm.broker import UIClientWired
from rei.confirm.voice import VoiceConfirmer, parse_answer
from rei.intents.schemas import IntentProposal


@pytest.mark.parametrize("text, strict, expected", [
    ("Yes.", False, True),
    ("yeah go ahead", False, True),
    ("okay", False, True),
    ("no thanks", False, False),
    ("yes... no, cancel", False, False),   # "no" wins
    ("I don't know", False, False),         # "don't" is a no
    ("what's the weather", False, None),    # not an answer
    ("yesterday was fun", False, None),     # whole words only
    ("yes", True, None),                    # strict needs "confirm"
    ("confirm", True, True),
    ("Confirm, send it.", True, True),
    ("no", True, False),
])
def test_parse_answer(text: str, strict: bool, expected: Any) -> None:
    assert parse_answer(text, strict) is expected


class FakeSignal:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def emit(self, *args: Any) -> None:
        self.calls.append(args)


class FakeBackend:
    def __init__(self) -> None:
        self.confirmationRequested = FakeSignal()
        self.confirmationHint = FakeSignal()
        self.confirmationClosed = FakeSignal()
        self.response_callback: Any = None


def _intent() -> IntentProposal:
    return IntentProposal(type="intent", capability="system.type_text", capability_version=1,
                          args={"text": "hi"}, rationale="type")


def _client(backend: FakeBackend, confirmer: VoiceConfirmer, spoken: list[str], mic: bool = True,
            window: float = 0.5) -> UIClientWired:
    async def say(text: str) -> None:
        spoken.append(text)

    return UIClientWired(backend, confirmer=confirmer, say=say, describe=lambda i: "Type text: hi",
                         mic_active=lambda: mic, voice_window_s=window, click_window_s=window)


@pytest.mark.asyncio
async def test_spoken_yes_approves_after_read_back() -> None:
    backend, confirmer = FakeBackend(), VoiceConfirmer()
    spoken: list[str] = []
    client = _client(backend, confirmer, spoken)
    task = asyncio.ensure_future(client.prompt_voice_or_click(_intent()))
    await asyncio.sleep(0.05)
    assert spoken and "Type text: hi" in spoken[0]
    assert confirmer.pending and not confirmer.strict
    assert confirmer.offer("yes please")
    assert await task is True
    assert backend.confirmationClosed.calls and not confirmer.pending


@pytest.mark.asyncio
async def test_high_risk_needs_the_word_confirm() -> None:
    backend, confirmer = FakeBackend(), VoiceConfirmer()
    spoken: list[str] = []
    client = _client(backend, confirmer, spoken)
    task = asyncio.ensure_future(client.prompt_click(_intent()))
    await asyncio.sleep(0.05)
    assert confirmer.strict
    assert not confirmer.offer("yeah")        # not enough for a high-risk action
    assert confirmer.offer("confirm")
    assert await task is True


@pytest.mark.asyncio
async def test_click_answers_and_silence_times_out() -> None:
    backend, confirmer = FakeBackend(), VoiceConfirmer()
    spoken: list[str] = []
    client = _client(backend, confirmer, spoken)
    task = asyncio.ensure_future(client.prompt_voice_or_click(_intent()))
    await asyncio.sleep(0.05)
    intent_id = backend.confirmationRequested.calls[0][2]
    backend.response_callback(intent_id, False)
    assert await task is False

    task = asyncio.ensure_future(client.prompt_voice_or_click(_intent()))
    assert await asyncio.wait_for(task, 2) is False   # nobody answered


@pytest.mark.asyncio
async def test_without_a_mic_only_clicks_count() -> None:
    backend, confirmer = FakeBackend(), VoiceConfirmer()
    spoken: list[str] = []
    client = _client(backend, confirmer, spoken, mic=False)
    task = asyncio.ensure_future(client.prompt_voice_or_click(_intent()))
    await asyncio.sleep(0.05)
    assert not confirmer.pending
    backend.response_callback(backend.confirmationRequested.calls[0][2], True)
    assert await task is True
