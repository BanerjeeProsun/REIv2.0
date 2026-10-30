import pytest

from rei.voice.wake import is_echo, is_stop_command


@pytest.mark.parametrize("text", [
    "stop", "Stop.", "Rei, stop.", "hey rei stop", "okay that's enough", "that’s enough",
    "never mind", "be quiet", "cancel", "stop talking", "Ray, stop please",
])
def test_stop_commands(text: str) -> None:
    assert is_stop_command(text)


@pytest.mark.parametrize("text", [
    "", "stop the music and play jazz", "I'll stop now", "don't stop", "can you stop the timer",
    "stop stop stop stop stop", "what's the weather",
])
def test_not_stop_commands(text: str) -> None:
    assert not is_stop_command(text)


def test_echo_is_a_fragment_of_what_rei_said() -> None:
    spoken = "Okay, I'll stop the music. Anything else?"
    assert is_echo("stop the music", spoken)
    assert is_echo("Anything else?", spoken)
    assert not is_echo("stop", "I'll pause it for you.")
    assert not is_echo("stop", "")
    # Whole words only: "stop" is not part of "stopwatch"
    assert not is_echo("stop", "Starting the stopwatch now.")


def _gate(text: str, **state: object) -> str:
    from rei.voice.wake import gate_voice
    defaults = {"rei_talking": False, "turn_active": False, "confirm_pending": False, "spoken": ""}
    defaults.update(state)
    return gate_voice(text, **defaults)  # type: ignore[arg-type]


def test_noise_while_thinking_is_dropped() -> None:
    assert _gate("thank you for", turn_active=True) == "drop"
    assert _gate("what time is it", turn_active=True) == "drop"


def test_stop_interrupts_while_thinking_or_speaking() -> None:
    assert _gate("stop", turn_active=True) == "interrupt"
    assert _gate("Rei, stop.", rei_talking=True, turn_active=True, spoken="Here is a long answer.") == "interrupt"


def test_rei_hearing_itself_never_interrupts_or_answers() -> None:
    assert _gate("stop", rei_talking=True, spoken="Okay, stop. Got it.") == "drop"
    # Rei reading back a confirmation must not approve it by echo
    assert _gate("yes", rei_talking=True, confirm_pending=True, spoken="Should I? Say yes or no.") == "drop"


def test_confirmation_answers_still_route_during_a_turn() -> None:
    assert _gate("yes", turn_active=True, confirm_pending=True) == "route"
    assert _gate("confirm", turn_active=True, confirm_pending=True) == "route"


def test_idle_rei_stop_still_reaches_the_media_shortcut() -> None:
    # Idle (music may be playing): routed normally -> wake word -> "stop" shortcut
    assert _gate("Rei, stop") == "route"
    assert _gate("open notepad") == "route"
