from types import SimpleNamespace

import pytest

pytest.importorskip("faster_whisper")
from rei.voice.stt import is_hallucination, keep_segment  # noqa: E402


@pytest.mark.parametrize("text", [
    "", " ", ".", ". . . .", "Thank you.", "thank you", "Thanks for watching!", "You", "you.",
    "Bye.", "Subtitles by the Amara.org community", "Hmm.",
])
def test_whisper_phantoms_are_dropped(text: str) -> None:
    assert is_hallucination(text)


@pytest.mark.parametrize("text", [
    "Open Spotify", "yes", "okay", "confirm", "stop", "Thank you, now play some jazz",
])
def test_real_requests_are_kept(text: str) -> None:
    assert not is_hallucination(text)


def test_segment_confidence_filter() -> None:
    assert keep_segment(SimpleNamespace(text=" open notepad", no_speech_prob=0.05, avg_logprob=-0.3))
    assert not keep_segment(SimpleNamespace(text=" you", no_speech_prob=0.9, avg_logprob=-0.3))
    assert not keep_segment(SimpleNamespace(text=" uh", no_speech_prob=0.1, avg_logprob=-1.6))
    # Segments without the fields (other backends) are kept
    assert keep_segment(SimpleNamespace(text=" hi"))
