from rei.core.prompt_builder import PromptBuilder
from rei.capabilities.spec import (
    CapabilitySpec, RiskTier, DataClass, RateLimit,
)
from rei.policy.schemas import PrivacyMode
from rei.capabilities.builtin.apps import OpenAppArgs


def test_prompt_builder_includes_capabilities() -> None:
    builder = PromptBuilder()
    spec = CapabilitySpec(
        id="apps.open",
        version=1,
        summary="Opens an application",
        tier=RiskTier.R1,
        args_model=OpenAppArgs,
        reads=frozenset(),
        returns=DataClass.C0,
        network=False,
        reversible=True,
        allow_when_tainted=False,
        confirm_template="Open {app}?",
        timeout_s=10.0,
        rate_limit=RateLimit(limit=10, period_s=60),
        modes=frozenset({PrivacyMode.LOCAL_ONLY, PrivacyMode.CLOUD_ASSISTED}),
    )
    prompt = builder.build("open notepad", [spec])
    assert "apps.open" in prompt
    assert "open notepad" in prompt.lower()
    assert "JSON" in prompt
