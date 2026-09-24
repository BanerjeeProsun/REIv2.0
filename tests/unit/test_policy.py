import pytest
from rei.policy.engine import PolicyEngine
from rei.policy.context import PolicyContext
from rei.policy.schemas import Origin, PrivacyMode, Verdict, ConfirmLevel
from rei.intents.schemas import IntentProposal
from rei.capabilities.registry import CapabilityRegistry
from rei.capabilities.builtin import register_builtin

@pytest.fixture
def registry() -> CapabilityRegistry:
    reg = CapabilityRegistry()
    register_builtin(reg)
    return reg

@pytest.fixture
def engine(registry: CapabilityRegistry) -> PolicyEngine:
    config = {
        "version": "2026.09.1",
        "disabled": {"capabilities": ["apps.close"]},
        "preauthorise": {"allowed": ["web.open_url"]}
    }
    return PolicyEngine(registry, config, b"secret_grant_key")

def test_policy_integrity(engine: PolicyEngine) -> None:
    ctx = PolicyContext(
        session_id="s1", turn_id="t1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(),
        settings={}, recent=None
    )
    
    # Valid R1 intent (should ALLOW)
    intent = IntentProposal(
        type="intent", capability="media.set_volume", capability_version=1,
        args={"level": 50}, rationale=""
    )
    decision = engine.decide(intent, ctx)
    assert decision.verdict == Verdict.ALLOW
    
    # Invalid args (should DENY schemas_invalid)
    intent_bad = IntentProposal(
        type="intent", capability="media.set_volume", capability_version=1,
        args={"level": 150}, rationale=""
    )
    decision_bad = engine.decide(intent_bad, ctx)
    assert decision_bad.verdict == Verdict.DENY
    assert "SCHEMA_INVALID" in decision_bad.reasons

def test_policy_kill_switches(engine: PolicyEngine) -> None:
    ctx = PolicyContext(
        session_id="s1", turn_id="t1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(),
        settings={}, recent=None
    )
    
    # disabled capability
    intent = IntentProposal(
        type="intent", capability="apps.close", capability_version=1,
        args={"app": "notepad"}, rationale=""
    )
    decision = engine.decide(intent, ctx)
    assert decision.verdict == Verdict.DENY
    assert "CAPABILITY_DISABLED" in decision.reasons

def test_policy_taint_escalation(engine: PolicyEngine) -> None:
    ctx = PolicyContext(
        session_id="s1", turn_id="t1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(["EMAIL"]),
        settings={}, recent=None
    )
    
    # R1 tainted escalates to VOICE_OR_CLICK
    intent = IntentProposal(
        type="intent", capability="media.set_volume", capability_version=1,
        args={"level": 50}, rationale=""
    )
    decision = engine.decide(intent, ctx)
    assert decision.verdict == Verdict.CONFIRM
    assert decision.confirm_level == ConfirmLevel.VOICE_OR_CLICK
    assert "TAINT_ESCALATION" in decision.reasons
