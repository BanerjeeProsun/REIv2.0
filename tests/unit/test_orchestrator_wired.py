import pytest
import secrets
from rei.core.orchestrator import Orchestrator
from rei.core.cancellation import CancelToken
from rei.core.prompt_builder import PromptBuilder
from rei.models.fake import FakeModel
from rei.intents.parser import IntentParser
from rei.policy.engine import PolicyEngine
from rei.policy.context import PolicyContext
from rei.policy.schemas import Origin, PrivacyMode
from rei.capabilities.registry import CapabilityRegistry
from rei.capabilities.builtin import register_builtin
from rei.confirm.broker import ConfirmationBroker, UIClientMock
from rei.core.executor import Executor
from rei.host.verify import GrantVerifier


def _build_orchestrator() -> Orchestrator:
    grant_key = secrets.token_bytes(32)
    registry = CapabilityRegistry()
    register_builtin(registry)

    policy_config = {
        "version": "test",
        "defaults": {"safe_mode": False},
        "disabled": {"capabilities": []},
        "preauthorise": {"allowed": ["apps.open", "media.set_volume"]},
    }

    return Orchestrator(
        model=FakeModel(),
        registry=registry,
        policy_engine=PolicyEngine(registry, policy_config, grant_key),
        parser=IntentParser(),
        prompt_builder=PromptBuilder(),
        confirmation_broker=ConfirmationBroker(UIClientMock()),
        executor=Executor(registry, GrantVerifier(registry, grant_key)),
    )


def _build_ctx() -> PolicyContext:
    return PolicyContext(
        session_id="test",
        turn_id="turn-1",
        origin=Origin.USER_TYPED,
        privacy_mode=PrivacyMode.LOCAL_ONLY,
        taint=frozenset(),
        settings={},
        recent=None,
    )


@pytest.mark.asyncio
async def test_orchestrator_open_notepad() -> None:
    orch = _build_orchestrator()
    ctx = _build_ctx()
    token = CancelToken()

    result = await orch.process_turn("open notepad", ctx, token)

    assert result.success
    assert len(result.intents) == 1
    assert result.intents[0].capability == "apps.open"
    assert len(result.decisions) == 1
    assert result.decisions[0].verdict.name == "ALLOW"
    assert len(result.execution_results) >= 1


@pytest.mark.asyncio
async def test_orchestrator_unknown_command() -> None:
    orch = _build_orchestrator()
    ctx = _build_ctx()
    token = CancelToken()

    result = await orch.process_turn("fly me to the moon", ctx, token)

    assert result.success
    assert len(result.intents) == 0
    assert "not sure" in result.reply.lower() or "don't have" in result.reply.lower()


@pytest.mark.asyncio
async def test_orchestrator_cancelled() -> None:
    orch = _build_orchestrator()
    ctx = _build_ctx()
    token = CancelToken()
    token.cancel()

    result = await orch.process_turn("open notepad", ctx, token)

    # Should not crash, but should fail gracefully
    assert not result.success
