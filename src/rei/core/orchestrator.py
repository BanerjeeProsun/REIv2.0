from typing import Any
from rei.intents.schemas import IntentProposal
from rei.policy.schemas import PolicyDecision
from rei.policy.grant import GrantToken


class PipelineError(Exception):
    pass


class Orchestrator:
    async def process_turn(self, raw_input: Any, cancel_token: Any) -> Any:
        try:
            # 1. Capture
            user_utterance = await self._capture(raw_input)

            # 2. Propose
            raw_output = await self._propose(user_utterance, cancel_token)

            # 3. Parse
            intents = await self._parse(raw_output)

            # 4. Decide
            decision = await self._decide(intents)

            # 5. Confirm
            approved = await self._confirm(decision, cancel_token)

            # 6. Grant
            grant = await self._grant(approved)

            # 7. Execute
            result = await self._execute(grant, cancel_token)

            # 8. Report
            return await self._report(result)

        except Exception as e:
            # DENY branch (no side effect, structured refusal, audit event)
            return self._handle_deny(e)

    async def _capture(self, raw_input: Any) -> Any:
        raise NotImplementedError

    async def _propose(self, utterance: Any, cancel_token: Any) -> Any:
        raise NotImplementedError

    async def _parse(self, raw_output: Any) -> list[IntentProposal]:
        raise NotImplementedError

    async def _decide(self, intents: list[IntentProposal]) -> PolicyDecision:
        raise NotImplementedError

    async def _confirm(self, decision: PolicyDecision, cancel_token: Any) -> Any:
        raise NotImplementedError

    async def _grant(self, approved_decision: Any) -> GrantToken:
        raise NotImplementedError

    async def _execute(self, grant: GrantToken, cancel_token: Any) -> Any:
        raise NotImplementedError

    async def _report(self, result: Any) -> Any:
        raise NotImplementedError

    def _handle_deny(self, error: Exception) -> Any:
        raise NotImplementedError
