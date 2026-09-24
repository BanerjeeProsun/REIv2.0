from typing import Literal
from pydantic import BaseModel, ConfigDict
from rei.capabilities.spec import CapabilitySpec, RiskTier, DataClass, RateLimit
from rei.policy.schemas import PrivacyMode


class SystemLockArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


system_lock_spec = CapabilitySpec(
    id="system.lock",
    version=1,
    summary="Lock the system",
    tier=RiskTier.R1,
    args_model=SystemLockArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="Lock system",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=5, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def system_lock_handler(args: SystemLockArgs) -> dict[str, str]:
    print("Mock locking system")
    return {"status": "success", "action": "lock"}


SystemPowerAction = Literal["shutdown", "restart"]


class SystemPowerArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: SystemPowerAction


system_power_spec = CapabilitySpec(
    id="system.power",
    version=1,
    summary="Shutdown or restart system",
    tier=RiskTier.R3,
    args_model=SystemPowerArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=False,
    allow_when_tainted=True,
    confirm_template="{action} system",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=2, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def system_power_handler(args: SystemPowerArgs) -> dict[str, str]:
    print(f"Mock system power action: {args.action}")
    return {"status": "success", "action": args.action}
