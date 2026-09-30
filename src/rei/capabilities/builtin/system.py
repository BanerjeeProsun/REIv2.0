from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
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
    import ctypes
    ctypes.windll.user32.LockWorkStation()
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
    import os
    if args.action == "shutdown":
        os.system("shutdown /s /t 1")
    elif args.action == "restart":
        os.system("shutdown /r /t 1")
    return {"status": "success", "action": args.action}

class TypeTextArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(..., max_length=1000)

system_type_text_spec = CapabilitySpec(
    id="system.type_text",
    version=1,
    summary="Type text as if using the keyboard. Useful for writing messages or documents.",
    tier=RiskTier.R2,
    args_model=TypeTextArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=False,
    allow_when_tainted=True,
    confirm_template="Type text: {text}",
    timeout_s=10.0,
    rate_limit=RateLimit(limit=50, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)

def system_type_text_handler(args: TypeTextArgs) -> dict[str, str]:
    from rei.capabilities.builtin import _win_input as win

    # Type into the user's window, never Rei's own: the app opened earlier in
    # this request if there is one, else the window used before Rei.
    hwnd = win.target_window(prefer_pid=win.recent_launch_pid())
    if hwnd is None:
        raise RuntimeError("No window to type into. Open or click the app first.")
    if not win.focus(hwnd):
        raise RuntimeError("Windows didn't let me focus that window.")
    win.wait_responsive(hwnd)  # a just-launched app may still be starting up
    win.insert_text(args.text)
    return {"status": "success", "text_typed": args.text}
