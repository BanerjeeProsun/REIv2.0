from dataclasses import dataclass
from typing import Any
from rei.policy.schemas import Origin, PrivacyMode


@dataclass(frozen=True)
class PolicyContext:
    session_id: str
    turn_id: str
    origin: Origin
    privacy_mode: PrivacyMode
    taint: frozenset[Any]
    settings: Any
    recent: Any
