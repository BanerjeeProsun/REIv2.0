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
