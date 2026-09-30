import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from rei.egress.redactor import SECRET_PATTERNS

# PII that may be restored in the final on-device reply (placeholder kind, pattern)
REVERSIBLE_PII_PATTERNS = [
    ("EMAIL", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b"),
    ("PHONE", r"(?<![\w\[])(?:\+?\d{1,3}[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}(?![\w\]])"),
]

# Data that must never be restored or leave the device, even as a mapping
IRREVERSIBLE_PII_PATTERNS = [
    (r"\b(?:\d[ -]*?){13,16}\b", "<REDACTED_CARD>"),
]

# Span types the local formatter may report; SECRET spans are dropped irreversibly
SPAN_TYPES = ("NAME", "ADDRESS", "ORG", "ID", "SECRET")

_PLACEHOLDER_RE = re.compile(r"\[([A-Z]+(?:_[A-Z0-9]+)*)\]")


@dataclass
class Vault:
    """Per-turn, in-memory placeholder map. Never logged, persisted or sent.

    Only reversible PII is stored here. Secrets are replaced with fixed
    <REDACTED_*> markers and have no entry, so they can never be restored.
    """

    _by_original: dict[str, str] = field(default_factory=dict)
    _by_placeholder: dict[str, str] = field(default_factory=dict)
    _counters: dict[str, int] = field(default_factory=dict)

    def placeholder_for(self, original: str, kind: str, fixed: str | None = None) -> str:
        key = original.casefold()
        if key in self._by_original:
            return self._by_original[key]
        if fixed:
            placeholder = f"[{fixed}]"
        else:
            self._counters[kind] = self._counters.get(kind, 0) + 1
            placeholder = f"[{kind}_{self._counters[kind]}]"
        self._by_original[key] = placeholder
        self._by_placeholder.setdefault(placeholder, original)
        return placeholder

    def rehydrate(self, text: str) -> str:
        def _sub(m: re.Match[str]) -> str:
            return self._by_placeholder.get(m.group(0), m.group(0))
        return _PLACEHOLDER_RE.sub(_sub, text)

    def rehydrate_obj(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self.rehydrate(obj)
        if isinstance(obj, dict):
            return {k: self.rehydrate_obj(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.rehydrate_obj(v) for v in obj]
        return obj

    def __len__(self) -> int:
        return len(self._by_placeholder)


@dataclass
class ScrubStats:
    secrets_removed: int = 0
    spans_replaced: int = 0


class Anonymizer:
    """Deterministic, model-free scrubbing applied before any cloud call.

    known_entities maps a fixed placeholder name to a value the device already
    knows is personal, e.g. {"USER_NAME": "Ada Lovelace"} from the user profile.
    """

    def __init__(self, known_entities: dict[str, str] | None = None) -> None:
        self._known: list[tuple[str, str, re.Pattern[str]]] = []
        for fixed, value in (known_entities or {}).items():
            value = value.strip()
            if not value:
                continue
            # Full value first, then each word of it (first name alone, etc.)
            parts = [value] + [p for p in value.split() if len(p) >= 3 and p != value]
            for part in parts:
                pattern = re.compile(rf"(?<!\w){re.escape(part)}(?!\w)", re.IGNORECASE)
                self._known.append((fixed, value, pattern))
        self.stats = ScrubStats()

    def scrub(self, text: str, vault: Vault) -> str:
        for secret_re, marker in SECRET_PATTERNS:
            text, n = re.subn(secret_re, marker, text)
            self.stats.secrets_removed += n

        for pii_re, marker in IRREVERSIBLE_PII_PATTERNS:
            text = re.sub(pii_re, marker, text)

        for fixed, value, known_re in self._known:
            placeholder = vault.placeholder_for(value, fixed, fixed=fixed)
            text = known_re.sub(placeholder, text)

        for kind, reversible_re in REVERSIBLE_PII_PATTERNS:
            def _vaulted(m: re.Match[str], kind: str = kind) -> str:
                return vault.placeholder_for(m.group(0), kind)
            text = re.sub(reversible_re, _vaulted, text)

        return text

    def apply_spans(self, text: str, spans: Iterable[tuple[str, str]], vault: Vault) -> str:
        """Replace spans reported by the local formatter.

        Only spans that occur verbatim in the text are replaced, so the model
        can flag data but can never rewrite, answer or drop the utterance.
        """
        for span_text, span_type in spans:
            span_text = span_text.strip()
            if len(span_text) < 2 or "[" in span_text or "<REDACTED" in span_text:
                continue
            if span_type not in SPAN_TYPES:
                span_type = "ID"
            pattern = re.compile(rf"(?<!\w){re.escape(span_text)}(?!\w)")
            if not pattern.search(text):
                continue
            if span_type == "SECRET":
                replacement = "<REDACTED_SECRET>"
                self.stats.secrets_removed += 1
            else:
                replacement = vault.placeholder_for(span_text, span_type)
            text = pattern.sub(replacement, text)
            self.stats.spans_replaced += 1
        return text
