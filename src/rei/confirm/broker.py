from rei.policy.schemas import PolicyDecision, ConfirmLevel, Verdict
from rei.intents.schemas import IntentProposal

class ConfirmationTimeoutError(Exception):
    pass

class ConfirmationRejectedError(Exception):
    pass

class ConfirmationBroker:
    def __init__(self, ui_client: 'UIClientMock') -> None:
        self.ui = ui_client

    async def request_confirmation(self, intent: IntentProposal, decision: PolicyDecision) -> bool:
        if decision.verdict != Verdict.CONFIRM:
            return True

        if decision.confirm_level == ConfirmLevel.VOICE_OR_CLICK:
            return await self.ui.prompt_voice_or_click(intent)
            
        elif decision.confirm_level == ConfirmLevel.CLICK:
            return await self.ui.prompt_click(intent)
            
        elif decision.confirm_level == ConfirmLevel.CLICK_WITH_REVIEW:
            return await self.ui.prompt_click_with_review(intent)
            
        return False

import asyncio
import uuid

class UIClientWired:
    def __init__(self, backend: 'ReiBackend') -> None:
        self.backend = backend
        self.pending_confirmations: dict[str, asyncio.Future[bool]] = {}
        self.backend.response_callback = self._on_response
        
    def _on_response(self, intent_id: str, approved: bool) -> None:
        if intent_id in self.pending_confirmations:
            if not self.pending_confirmations[intent_id].done():
                self.pending_confirmations[intent_id].set_result(approved)

    async def prompt_voice_or_click(self, intent: IntentProposal) -> bool:
        return await self._request(intent, "Confirmation Needed")

    async def prompt_click(self, intent: IntentProposal) -> bool:
        return await self._request(intent, "Action Requires Click")

    async def prompt_click_with_review(self, intent: IntentProposal) -> bool:
        return await self._request(intent, "Review Required")
        
    async def _request(self, intent: IntentProposal, title: str) -> bool:
        intent_id = str(uuid.uuid4())
        future = asyncio.Future()
        self.pending_confirmations[intent_id] = future
        message = f"Capability: {intent.capability}\nReason: {intent.rationale}\nArgs: {intent.args}"
        self.backend.confirmationRequested.emit(title, message, intent_id)
        try:
            return await future
        finally:
            if intent_id in self.pending_confirmations:
                del self.pending_confirmations[intent_id]

class UIClientMock:
    async def prompt_voice_or_click(self, intent: IntentProposal) -> bool:
        print(f"UI: Voice or Click required for {intent.capability}")
        return True

    async def prompt_click(self, intent: IntentProposal) -> bool:
        print(f"UI: Click required for {intent.capability}")
        return True

    async def prompt_click_with_review(self, intent: IntentProposal) -> bool:
        print(f"UI: Click with full review required for {intent.capability}. Args: {intent.args}")
        return True
