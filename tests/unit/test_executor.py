import pytest
from rei.core.executor import Executor, ExecutorError
from rei.host.verify import GrantVerifier
from rei.policy.engine import PolicyEngine
from rei.policy.context import PolicyContext
from rei.policy.schemas import Origin, PrivacyMode
from rei.intents.schemas import IntentProposal
from rei.capabilities.registry import CapabilityRegistry
from rei.capabilities.builtin import register_builtin
from rei.capabilities.builtin.media import SetVolumeArgs

@pytest.fixture
def registry() -> CapabilityRegistry:
    reg = CapabilityRegistry()
    register_builtin(reg)
    return reg

@pytest.fixture
def engine(registry: CapabilityRegistry) -> PolicyEngine:
    return PolicyEngine(registry, {}, b"test_key")

@pytest.fixture
def executor(registry: CapabilityRegistry) -> Executor:
    verifier = GrantVerifier(registry, b"test_key")
    return Executor(registry, verifier)

def test_executor_valid_grant(engine: PolicyEngine, executor: Executor) -> None:
    intent = IntentProposal(
        type="intent", capability="media.set_volume", capability_version=1,
        args={"level": 50}, rationale=""
    )
    ctx = PolicyContext(
        session_id="1", turn_id="1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(),
        settings={}, recent=None
    )
    decision = engine.decide(intent, ctx)
    token, mac = engine.issue_grant(intent, ctx, decision)
    
    # Execution should succeed
    args = SetVolumeArgs(level=50)
    result = executor.execute(token, args, mac)
    assert result["status"] == "success"
    
    # Replay should fail
    with pytest.raises(ExecutorError, match="Token already consumed"):
        executor.execute(token, args, mac)
        
def test_executor_tampered_mac(engine: PolicyEngine, executor: Executor) -> None:
    intent = IntentProposal(
        type="intent", capability="media.set_volume", capability_version=1,
        args={"level": 50}, rationale=""
    )
    ctx = PolicyContext(
        session_id="1", turn_id="1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(),
        settings={}, recent=None
    )
    decision = engine.decide(intent, ctx)
    token, mac = engine.issue_grant(intent, ctx, decision)
    
    args = SetVolumeArgs(level=50)
    # Tampered mac
    with pytest.raises(ExecutorError, match="Invalid MAC"):
        executor.execute(token, args, "bad_mac")
