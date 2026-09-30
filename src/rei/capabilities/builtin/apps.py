from typing import Literal
from pydantic import BaseModel, ConfigDict
from rei.capabilities.spec import CapabilitySpec, RiskTier, DataClass, RateLimit
from rei.policy.schemas import PrivacyMode

# AppId allowlist - this would normally be generated or dynamic based on installed apps
AppId = Literal["notepad", "calculator", "browser"]

APP_PATHS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "browser": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Example absolute path
}


class OpenAppArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    app: AppId


apps_open_spec = CapabilitySpec(
    id="apps.open",
    version=1,
    summary="Open an application",
    tier=RiskTier.R1,
    args_model=OpenAppArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=False,
    allow_when_tainted=True,
    confirm_template="Open app: {app}",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=10, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def apps_open_handler(args: OpenAppArgs) -> dict[str, str]:
    import subprocess
    path = APP_PATHS.get(args.app)
    if not path:
        raise ValueError(f"App {args.app} not found in allowlist")

    try:
        proc = subprocess.Popen(path)
        print(f"Launched: {path}")
        # Let a following "type ..." in the same request target this app
        from rei.capabilities.builtin import _win_input
        _win_input.note_launch(proc.pid)
        return {"status": "success", "app": args.app}
    except Exception as e:
        raise ValueError(f"Failed to launch {args.app}: {e}")


class CloseAppArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    app: AppId


apps_close_spec = CapabilitySpec(
    id="apps.close",
    version=1,
    summary="Close an application",
    tier=RiskTier.R2,
    args_model=CloseAppArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=False,
    allow_when_tainted=True,
    confirm_template="Close app: {app}",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=10, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)


def apps_close_handler(args: CloseAppArgs) -> dict[str, str]:
    # In a real implementation we would track handles of launched processes
    # and only close those, or verify the signature.
    return {"status": "success", "app": args.app, "action": "mock_close"}
