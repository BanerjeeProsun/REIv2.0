import asyncio
from typing import Any
from dataclasses import dataclass

from rei.intents.schemas import IntentProposal
from rei.intents.parser import IntentParser, IntentParserError
from rei.policy.schemas import PolicyDecision, Verdict
from rei.policy.engine import PolicyEngine
from rei.policy.context import PolicyContext
from rei.policy.grant import GrantToken
from rei.core.cancellation import CancelToken
from rei.core.prompt_builder import PromptBuilder
from rei.models.adapter import ModelAdapter
from rei.capabilities.registry import CapabilityRegistry
from rei.confirm.broker import ConfirmationBroker
from rei.core.executor import Executor
from rei.audit.writer import AuditLogWriter


class PipelineError(Exception):
    pass


class PipelineDenied(PipelineError):
    def __init__(self, reason: str, decision: PolicyDecision | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.decision = decision


@dataclass
class TurnResult:
    success: bool
    reply: str
    intents: list[IntentProposal]
    decisions: list[PolicyDecision]
    execution_results: list[dict[str, Any]]
    audit_events: list[dict[str, Any]]


class Orchestrator:
    """Wired 8-stage pipeline (ARC-01, ARC-02).

    Every user request flows through exactly these stages.
    Any failure routes to the DENY branch with zero side effects.
    """

    def __init__(
        self,
        model: ModelAdapter,
        registry: CapabilityRegistry,
        policy_engine: PolicyEngine,
        parser: IntentParser,
        prompt_builder: PromptBuilder,
        confirmation_broker: ConfirmationBroker,
        executor: Executor,
        audit: AuditLogWriter | None = None,
    ) -> None:
        self.model = model
        self.registry = registry
        self.policy_engine = policy_engine
        self.parser = parser
        self.prompt_builder = prompt_builder
        self.confirmation_broker = confirmation_broker
        self.executor = executor
        self.audit = audit

    async def process_turn(
        self,
        raw_input: str,
        ctx: PolicyContext,
        cancel_token: CancelToken,
    ) -> TurnResult:
        audit_events: list[dict[str, Any]] = []
        try:
            # 1. Capture
            utterance = self._capture(raw_input)
            audit_events.append({"stage": "capture", "utterance": utterance})

            # 2. Propose
            cancel_token.raise_if_cancelled()
            raw_output = await self._propose(utterance, cancel_token)
            audit_events.append({"stage": "propose", "output_len": len(raw_output)})

            # 3. Parse
            intents = self._parse(raw_output)
            audit_events.append({
                "stage": "parse",
                "intent_count": len(intents),
                "capabilities": [i.capability for i in intents],
            })

            if not intents:
                # Model returned conversational reply, no actions
                return TurnResult(
                    success=True,
                    reply=self._extract_reply(raw_output),
                    intents=[],
                    decisions=[],
                    execution_results=[],
                    audit_events=audit_events,
                )

            decisions: list[PolicyDecision] = []
            execution_results: list[dict[str, Any]] = []

            for intent in intents:
                cancel_token.raise_if_cancelled()

                # 4. Decide
                decision = self._decide(intent, ctx)
                decisions.append(decision)
                audit_events.append({
                    "stage": "decide",
                    "capability": intent.capability,
                    "verdict": decision.verdict.name,
                    "reasons": decision.reasons,
                })

                if decision.verdict == Verdict.DENY:
                    continue

                # 5. Confirm
                if decision.verdict == Verdict.CONFIRM:
                    approved = await self._confirm(intent, decision, cancel_token)
                    audit_events.append({
                        "stage": "confirm",
                        "capability": intent.capability,
                        "approved": approved,
                    })
                    if not approved:
                        continue

                # 6. Grant
                grant, mac = self._grant(intent, ctx, decision)
                audit_events.append({
                    "stage": "grant",
                    "grant_id": grant.grant_id,
                    "capability": intent.capability,
                })

                # 7. Execute
                result = self._execute(intent, grant, mac)
                execution_results.append(result)
                audit_events.append({
                    "stage": "execute",
                    "capability": intent.capability,
                    "status": result.get("status", "unknown"),
                })

            # 8. Report
            reply = self._report(intents, decisions, execution_results)

            if self.audit:
                for event in audit_events:
                    self.audit.write_event(event.get("stage", "unknown"), event)

            return TurnResult(
                success=True,
                reply=reply,
                intents=intents,
                decisions=decisions,
                execution_results=execution_results,
                audit_events=audit_events,
            )

        except (Exception, asyncio.CancelledError) as e:
            audit_events.append({"stage": "deny", "error": str(e)})
            if self.audit:
                for event in audit_events:
                    self.audit.write_event(event.get("stage", "unknown"), event)
            return TurnResult(
                success=False,
                reply=f"I was unable to complete that request. Reason: {e}",
                intents=[],
                decisions=[],
                execution_results=[],
                audit_events=audit_events,
            )

    # Stage implementations

    def _capture(self, raw_input: str) -> str:
        return raw_input.strip()

    async def _propose(self, utterance: str, cancel_token: CancelToken) -> str:
        specs = self.registry.get_all_specs()
        prompt = self.prompt_builder.build(utterance, specs)
        return await self.model.generate(prompt, cancel_token)

    def _parse(self, raw_output: str) -> list[IntentProposal]:
        try:
            return self.parser.parse(raw_output)
        except IntentParserError:
            return []

    def _decide(self, intent: IntentProposal, ctx: PolicyContext) -> PolicyDecision:
        return self.policy_engine.decide(intent, ctx)

    async def _confirm(
        self,
        intent: IntentProposal,
        decision: PolicyDecision,
        cancel_token: CancelToken,
    ) -> bool:
        cancel_token.raise_if_cancelled()
        return await self.confirmation_broker.request_confirmation(intent, decision)

    def _grant(
        self,
        intent: IntentProposal,
        ctx: PolicyContext,
        decision: PolicyDecision,
    ) -> tuple[GrantToken, str]:
        return self.policy_engine.issue_grant(intent, ctx, decision)

    def _execute(
        self,
        intent: IntentProposal,
        grant: GrantToken,
        mac: str,
    ) -> dict[str, Any]:
        args_model = self.registry.get_spec(intent.capability).args_model
        validated_args = args_model.model_validate(intent.args)
        result: dict[str, Any] = self.executor.execute(grant, validated_args, mac)
        return result

    def _report(
        self,
        intents: list[IntentProposal],
        decisions: list[PolicyDecision],
        results: list[dict[str, Any]],
    ) -> str:
        parts: list[str] = []
        for intent, decision in zip(intents, decisions):
            if decision.verdict == Verdict.DENY:
                reason = ", ".join(decision.reasons)
                parts.append(f"Could not execute {intent.capability}: {reason}")
            elif decision.verdict == Verdict.CONFIRM:
                parts.append(f"Awaiting confirmation for {intent.capability}")
            else:
                parts.append(f"Done: {intent.rationale}")

        return "; ".join(parts) if parts else "No actions were taken."

    def _extract_reply(self, raw_output: str) -> str:
        import json
        try:
            data = json.loads(raw_output)
            if isinstance(data, dict):
                return str(data.get("reply", "I'm not sure how to help with that."))
        except (json.JSONDecodeError, ValueError):
            pass
        return "I'm not sure how to help with that."
