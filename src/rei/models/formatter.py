import asyncio
import json
import re
from typing import Any, Protocol

from rei.core.cancellation import CancelToken
from rei.egress.anonymizer import SPAN_TYPES


class FormatterError(Exception):
    pass


class JsonModel(Protocol):
    async def generate_json(
        self,
        system: str | None,
        user: str,
        schema: dict[str, Any],
        cancel_token: CancelToken,
        deadline_ms: int = ...,
        max_tokens: int = ...,
    ) -> str: ...


SPAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "spans": {
            "type": "array",
            "maxItems": 12,
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "type": {"type": "string", "enum": list(SPAN_TYPES)},
                },
                "required": ["text", "type"],
            },
        }
    },
    "required": ["spans"],
}

SYSTEM_PROMPT = (
    "You are a privacy filter. You never answer or rephrase the user. "
    "List every piece of sensitive data in the text exactly as written: "
    "person names (NAME), street addresses (ADDRESS), company or organisation "
    "names tied to the user (ORG), account, customer or ID numbers (ID), and "
    "passwords, API keys or tokens (SECRET). Text in [BRACKETS] or <ANGLES> is "
    "already redacted; ignore it. Cities, countries and famous public topics are "
    "not sensitive. If nothing is sensitive, return an empty list.\n\n"
    "Example: Tell John Smith at [EMAIL_1] that invoice 88213 is paid\n"
    '{"spans": [{"text": "John Smith", "type": "NAME"}, {"text": "88213", "type": "ID"}]}\n'
    "Example: what's the capital of France?\n"
    '{"spans": []}\n'
    "Example: my sister Priya lives at 12 Baker Street\n"
    '{"spans": [{"text": "Priya", "type": "NAME"}, {"text": "12 Baker Street", "type": "ADDRESS"}]}'
)


class LocalFormatter:
    """On-device formatter in front of the cloud planner.

    The local model only *detects* sensitive spans; replacement is done
    deterministically by the Anonymizer. Any failure raises FormatterError so
    the caller can fail closed (plan locally instead of sending to the cloud).
    """

    def __init__(self, model: JsonModel, deadline_ms: int = 8000) -> None:
        self.model = model
        self.deadline_ms = deadline_ms

    MAX_SENTENCES = 4

    async def detect_spans(self, text: str, cancel_token: CancelToken) -> list[tuple[str, str]]:
        """Detect sensitive spans, one short sentence at a time.

        Small models are far more accurate on short inputs, and implausible
        spans (common phrases flagged as names, etc.) are discarded so the
        cloud planner still receives a usable request.
        """
        sentences = [p.strip() for p in re.split(r"(?<=[.!?;])\s+", text) if p.strip()]
        if len(sentences) > self.MAX_SENTENCES:
            sentences = sentences[: self.MAX_SENTENCES - 1] + [" ".join(sentences[self.MAX_SENTENCES - 1:])]

        found: list[tuple[str, str]] = []
        for sentence in sentences:
            for span in await self._detect_one(sentence, cancel_token):
                if span not in found and _plausible(span[0], span[1], sentence):
                    found.append(span)
        return found

    async def _detect_one(self, text: str, cancel_token: CancelToken) -> list[tuple[str, str]]:
        try:
            raw = await self.model.generate_json(
                system=SYSTEM_PROMPT,
                user=f"Text: {text}",
                schema=SPAN_SCHEMA,
                cancel_token=cancel_token,
                deadline_ms=self.deadline_ms,
                max_tokens=160,
            )
            data = json.loads(raw)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise FormatterError(f"Local formatter failed: {e}") from e

        spans = data.get("spans") if isinstance(data, dict) else None
        if not isinstance(spans, list):
            raise FormatterError("Local formatter returned no span list")

        result: list[tuple[str, str]] = []
        for item in spans:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                result.append((item["text"].strip(), str(item.get("type", "ID"))))
        return result


def _plausible(span: str, span_type: str, source: str) -> bool:
    """Reject spans a 1B model commonly hallucinates."""
    if len(span) < 2 or span not in source or "[" in span or "<" in span:
        return False
    words = span.split()
    has_digit = any(c.isdigit() for c in span)
    if span_type in ("NAME", "ORG"):
        if len(words) > 4 or has_digit:
            return False
        if any(w.lower() in _COMMON_WORDS for w in words):
            return False
        # Real names are capitalised unless the user typed everything lowercase
        return source.islower() or all(w[0].isupper() for w in words)
    if span_type in ("ADDRESS", "ID"):
        return has_digit
    if span_type == "SECRET":
        return len(span) >= 6 and " " not in span
    return False


_COMMON_WORDS = frozenset("""
a an the i me my mine you your he him his she her they them their we us our it its
is am are was be to of in on at by for with from and or but not no yes hi hello hey
name names greet say says said tell call reach email mail message text colleague
friend mom dad mother father sister brother boss also please thanks thank today
tomorrow yesterday morning evening night good great nice warm warmly research work
""".split())
