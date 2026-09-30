import asyncio
import re
from typing import Optional

# Whole-word / whole-phrase matches only, so "know" isn't "no" and "yesterday" isn't "yes"
_YES = re.compile(r"\b(yes|yeah|yep|yup|sure|ok|okay|do it|go ahead|go for it|please do|confirm(ed)?)\b")
_CONFIRM = re.compile(r"\bconfirm(ed)?\b")
_NO = re.compile(r"\b(no|nope|nah|cancel|stop|don't|do not|never mind|nevermind|abort)\b")


def parse_answer(text: str, strict: bool) -> Optional[bool]:
    """Interpret a spoken or typed confirmation.

    Returns True (approve), False (reject) or None (not an answer; keep waiting).
    strict=True is used for high-risk actions: only the word "confirm" approves,
    so a casual "yeah" (or a voice on TV) can't send an email.
    A "no" always wins if both appear.
    """
    t = text.lower().replace("’", "'").strip()
    if not t:
        return None
    if _NO.search(t):
        return False
    if strict:
        return True if _CONFIRM.search(t) else None
    return True if _YES.search(t) else None


class VoiceConfirmer:
    """Holds at most one pending confirmation that the next utterance can answer."""

    def __init__(self) -> None:
        self._future: Optional[asyncio.Future[bool]] = None
        self._strict = False

    @property
    def pending(self) -> bool:
        return self._future is not None and not self._future.done()

    @property
    def strict(self) -> bool:
        return self._strict

    def expect(self, strict: bool) -> "asyncio.Future[bool]":
        self.cancel()
        self._strict = strict
        self._future = asyncio.get_running_loop().create_future()
        return self._future

    def offer(self, text: str) -> bool:
        """Feed an utterance. Returns True if it answered the pending question."""
        if not self.pending:
            return False
        answer = parse_answer(text, self._strict)
        if answer is None:
            return False
        if self._future is None:
            return False
        self._future.set_result(answer)
        return True

    def cancel(self) -> None:
        if self._future is not None and not self._future.done():
            self._future.cancel()
        self._future = None
