from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Type
from rei.policy.schemas import PrivacyMode


class RiskTier(Enum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


class DataClass(Enum):
    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


class RateLimit(BaseModel):
    limit: int
    period_s: int


class CapabilitySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    version: int
    summary: str
    tier: RiskTier
    args_model: Type[BaseModel]
    reads: frozenset[DataClass]
    returns: DataClass
    network: bool
    reversible: bool
    allow_when_tainted: bool
    confirm_template: str
    timeout_s: float
    rate_limit: RateLimit
    modes: frozenset[PrivacyMode]
