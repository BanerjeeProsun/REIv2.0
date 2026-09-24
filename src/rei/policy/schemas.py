from enum import Enum
from dataclasses import dataclass
from typing import Optional


class Origin(Enum):
    USER_VOICE = "USER_VOICE"
    USER_TYPED = "USER_TYPED"
    WORKER = "WORKER"
    SYSTEM = "SYSTEM"


class PrivacyMode(Enum):
    LOCAL_ONLY = "LOCAL_ONLY"
    LOCAL_PLUS_WEB = "LOCAL_PLUS_WEB"
    CLOUD_ASSISTED = "CLOUD_ASSISTED"


class Verdict(Enum):
    ALLOW = 1
    CONFIRM = 2
    DENY = 3


class ConfirmLevel(Enum):
    VOICE_OR_CLICK = "VOICE_OR_CLICK"
    CLICK = "CLICK"
    CLICK_WITH_REVIEW = "CLICK_WITH_REVIEW"


@dataclass(frozen=True)
class PolicyDecision:
    verdict: Verdict
    confirm_level: Optional[ConfirmLevel]
    reasons: tuple[str, ...]
    policy_version: str
