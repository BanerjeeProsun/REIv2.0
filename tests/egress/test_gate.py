import pytest
from rei.egress.gate import EgressGate, EgressRequest, EgressPayloadPart, EgressBlockedError
from rei.capabilities.spec import DataClass
from rei.policy.schemas import PrivacyMode
from rei.policy.config import (
    PolicyConfig, DefaultsConfig, PreauthoriseConfig, 
    DisabledConfig, UrlPolicyConfig, EgressHostConfig
)

@pytest.fixture
def policy_config() -> PolicyConfig:
    return PolicyConfig(
        version="1",
        defaults=DefaultsConfig(confirm_timeout_s=30, voice_confirm_window_s=10, max_intents_per_turn=3),
        rate_limits={},
        preauthorise=PreauthoriseConfig(allowed=[]),
        disabled=DisabledConfig(capabilities=[]),
        url_policy=UrlPolicyConfig(schemes=[], blocked_tlds=[], blocked_hosts_file="", max_length=2000),
        egress={
            "hosts": {
                "api.test.com": EgressHostConfig(modes=["CLOUD_ASSISTED"], purpose="test")
            }
        }
    )

@pytest.mark.asyncio
async def test_egress_gate_local_only(policy_config: PolicyConfig) -> None:
    gate = EgressGate(policy_config, PrivacyMode.LOCAL_ONLY)
    req = EgressRequest("api.test.com", "test", [], "t1")
    
    with pytest.raises(EgressBlockedError, match="LOCAL_ONLY"):
        await gate.send(req)

@pytest.mark.asyncio
async def test_egress_gate_c3_blocked(policy_config: PolicyConfig) -> None:
    gate = EgressGate(policy_config, PrivacyMode.CLOUD_ASSISTED)
    req = EgressRequest(
        destination="api.test.com", purpose="test",
        payload=[EgressPayloadPart(DataClass.C3, "my secret password")],
        turn_id="t1"
    )
    
    with pytest.raises(EgressBlockedError, match="SECRET data"):
        await gate.send(req)

@pytest.mark.asyncio
async def test_egress_gate_success(policy_config: PolicyConfig) -> None:
    gate = EgressGate(policy_config, PrivacyMode.CLOUD_ASSISTED)
    req = EgressRequest(
        destination="api.test.com", purpose="test",
        payload=[EgressPayloadPart(DataClass.C0, "weather in london")],
        turn_id="t1"
    )
    
    res = await gate.send(req)
    assert res["status"] == "mock_sent"
