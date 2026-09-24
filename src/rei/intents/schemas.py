from pydantic import BaseModel, ConfigDict
from typing import Any


class IntentProposal(BaseModel):
    model_config = ConfigDict(strict=True)

    type: str
    capability: str
    capability_version: int
    args: dict[str, Any]
    rationale: str
