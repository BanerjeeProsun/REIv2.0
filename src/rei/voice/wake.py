"""Wake-word gate used while music is playing.

Without real echo cancellation the mic hears the song, and Whisper happily
transcribes lyrics. While music plays, voice input therefore only counts if it
starts with "Rei" / "Hey Rei" (plus the ways Whisper tends to spell it).
"""

WAKE_WORDS = ("hey rei", "hey ray", "hey rey", "hey re", "hi rei", "rei", "ray", "rey")


def strip_wake_word(text: str) -> str | None:
    """Return the command after the wake word, or None if there isn't one."""
    stripped = text.lstrip()
    lowered = stripped.lower()
    for word in WAKE_WORDS:
        if lowered.startswith(word) and (len(lowered) == len(word) or not lowered[len(word)].isalnum()):
            return stripped[len(word):].lstrip(" ,.!?:;-") or "hello"
    return None
