import tomllib
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, List, Any

class DefaultsConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    confirm_timeout_s: int
    voice_confirm_window_s: int
    max_intents_per_turn: int

class PreauthoriseConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    allowed: List[str]

class DisabledConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    capabilities: List[str]

class UrlPolicyConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    schemes: List[str]
    blocked_tlds: List[str]
    blocked_hosts_file: str
    max_length: int

class EgressHostConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    modes: List[str]
    purpose: str
    max_class: str = "C3" # default

class PolicyConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    version: str
    defaults: DefaultsConfig
    rate_limits: Dict[str, str]
    preauthorise: PreauthoriseConfig
    disabled: DisabledConfig
    url_policy: UrlPolicyConfig
    egress: Dict[str, Dict[str, EgressHostConfig]] = Field(default_factory=dict)

def load_policy_config(path: str) -> PolicyConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return PolicyConfig.model_validate(data)
