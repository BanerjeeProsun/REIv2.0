"""Wake-word gate used while music is playing, and the spoken "stop" command.

Without real echo cancellation the mic hears the song, and Whisper happily
transcribes lyrics. While music plays, voice input therefore only counts if it
starts with "Rei" / "Hey Rei" (plus the ways Whisper tends to spell it).
"""
import re

WAKE_WORDS = ("hey rei", "hey ray", "hey rey", "hey re", "hi rei", "rei", "ray", "rey")

# The whole utterance must be a short interruption, so "stop the music and play
# jazz" or a sentence from Rei's own reply never counts as one.
_STOP = re.compile(
    r"^(?:(?:hey |hi )?(?:rei|ray|rey|re) )?(?:okay |ok |please )?"
    r"(?:stop|stop it|stop talking|cancel|quiet|be quiet|shut up|enough|that's enough|that is enough"
    r"|never mind|nevermind)(?: please| now)?$"
)


def _normalise(text: str) -> str:
    return " ".join(re.sub(r"[^a-z' ]+", " ", text.lower().replace("’", "'")).split())


def is_stop_command(text: str) -> bool:
    """True when the utterance is just a request to stop ("Rei, stop.", "that's enough")."""
    norm = _normalise(text)
    return bool(norm) and len(norm.split()) <= 4 and _STOP.match(norm) is not None


def is_echo(heard: str, spoken: str) -> bool:
    """True when what the mic heard is a fragment of what Rei is saying."""
    h, s = _normalise(heard), _normalise(spoken)
    return bool(h) and bool(s) and f" {h} " in f" {s} "


def gate_voice(text: str, *, rei_talking: bool, turn_active: bool,
               confirm_pending: bool, spoken: str) -> str:
    """Decide what a transcribed utterance may do.

    "interrupt": stop the running turn. "drop": ignore it. "route": handle it
    normally (new turn, confirmation answer, music wake word...).
    """
    if rei_talking:
        # Without real echo cancellation only a short "stop" counts while Rei
        # talks, and never Rei's own words coming back through the mic.
        # Confirmations are never answered from this window either.
        return "interrupt" if is_stop_command(text) and not is_echo(text, spoken) else "drop"
    if turn_active and not confirm_pending:
        # Rei is thinking: background noise and chatter must not start turns
        return "interrupt" if is_stop_command(text) else "drop"
    return "route"


def strip_wake_word(text: str) -> str | None:
    """Return the command after the wake word, or None if there isn't one."""
    stripped = text.lstrip()
    lowered = stripped.lower()
    for word in WAKE_WORDS:
        if lowered.startswith(word) and (len(lowered) == len(word) or not lowered[len(word)].isalnum()):
            return stripped[len(word):].lstrip(" ,.!?:;-") or "hello"
    return None
