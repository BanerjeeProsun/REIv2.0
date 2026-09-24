import pytest
from pydantic import ValidationError
from rei.intents.schemas import IntentProposal
from rei.policy.schemas import PolicyDecision, Verdict, ConfirmLevel


def test_intent_proposal_strictness() -> None:
    # Valid proposal
    proposal = IntentProposal(
        type="intent",
        capability="media.set_volume",
        capability_version=3,
        args={"level": 40},
        rationale="User asked to turn it down a bit",
    )
    assert proposal.capability == "media.set_volume"

    # Strictness check
    with pytest.raises(ValidationError):
        IntentProposal(
            type="intent",
            capability="media.set_volume",
            capability_version="3", 
            args={"level": 40},
            rationale="User asked to turn it down a bit",
        )


def test_policy_decision() -> None:

    decision = PolicyDecision(
        verdict=Verdict.CONFIRM,
        confirm_level=ConfirmLevel.CLICK_WITH_REVIEW,
        reasons=("TAINT_ESCALATION",),
        policy_version="2026.09.1",
    )
    assert decision.verdict == Verdict.CONFIRM
