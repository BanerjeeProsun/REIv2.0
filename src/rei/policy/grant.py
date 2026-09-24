from pydantic import BaseModel, ConfigDict


class GrantToken(BaseModel):
    model_config = ConfigDict(frozen=True)

    grant_id: str
    turn_id: str
    capability: str
    capability_version: int
    args_sha256: str
    tier: str
    confirmed_by: str
    taint: list[str]
    issued_at: float
    expires_at: float
    nonce: str
