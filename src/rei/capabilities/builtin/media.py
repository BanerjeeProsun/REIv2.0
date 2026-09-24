from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from rei.capabilities.spec import CapabilitySpec, RiskTier, DataClass, RateLimit
from rei.policy.schemas import PrivacyMode


class SetVolumeArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    level: int = Field(..., ge=0, le=100)


media_set_volume_spec = CapabilitySpec(
    id="media.set_volume",
    version=1,
    summary="Set system volume",
    tier=RiskTier.R1,
    args_model=SetVolumeArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="Set volume to {level}%",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=20, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def media_set_volume_handler(args: SetVolumeArgs) -> dict[str, str | int]:
    # Mocking Core Audio API interaction
    print(f"Mock setting volume to: {args.level}")
    return {"status": "success", "volume": args.level}


MediaAction = Literal["play", "pause", "next", "prev"]


class MediaControlArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: MediaAction


media_control_spec = CapabilitySpec(
    id="media.control",
    version=1,
    summary="Control media playback",
    tier=RiskTier.R1,
    args_model=MediaControlArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="Media control: {action}",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=30, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def media_control_handler(args: MediaControlArgs) -> dict[str, str]:
    # Mocking SMTC API interaction
    print(f"Mock media control: {args.action}")
    return {"status": "success", "action": args.action}
