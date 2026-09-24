import pytest
from pydantic import ValidationError
from rei.policy.config import load_policy_config, PolicyConfig

def test_load_policy_config() -> None:
    config = load_policy_config("src/rei/policy/policy.toml")
    assert config.version == "2026.09.1"
    assert "web.open_url" in config.rate_limits
    assert "integrate.api.nvidia.com" in config.egress.get("hosts", {})
