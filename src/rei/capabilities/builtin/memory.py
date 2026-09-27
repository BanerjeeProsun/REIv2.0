from pydantic import BaseModel, ConfigDict, Field
from rei.capabilities.spec import CapabilitySpec, RiskTier, DataClass, RateLimit
from rei.policy.schemas import PrivacyMode


class RememberArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    key: str = Field(..., max_length=100)
    value: str = Field(..., max_length=1000)


memory_remember_spec = CapabilitySpec(
    id="memory.remember",
    version=1,
    summary="Save a piece of information to long-term memory",
    tier=RiskTier.R1,
    args_model=RememberArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=False,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="Remember {key}",
    timeout_s=5.0,
    rate_limit=RateLimit(limit=50, period_s=60),
    modes=frozenset([PrivacyMode.LOCAL_ONLY, PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED]),
)

# Global store reference to be injected at startup
_store = None

def set_memory_store(store) -> None:
    global _store
    _store = store

def memory_remember_handler(args: RememberArgs) -> dict[str, str]:
    if not _store:
        raise ValueError("MemoryStore not initialized")
    _store.set(args.key, args.value)
    return {"status": "success", "key": args.key}
