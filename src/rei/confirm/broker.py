import asyncio
import uuid
from typing import Any, Awaitable, Callable, Optional

from rei.confirm.voice import VoiceConfirmer

from rei.policy.schemas import PolicyDecision, ConfirmLevel, Verdict
from rei.intents.schemas import IntentProposal

class ConfirmationTimeoutError(Exception):
    pass

class ConfirmationRejectedError(Exception):
    pass

class ConfirmationBroker:
    def __init__(self, ui_client: Any) -> None:
        self.ui = ui_client

    async def request_confirmation(self, intent: IntentProposal, decision: PolicyDecision) -> bool:
        if decision.verdict != Verdict.CONFIRM:
            return True

        if decision.confirm_level == ConfirmLevel.VOICE_OR_CLICK:
            return bool(await self.ui.prompt_voice_or_click(intent))

        elif decision.confirm_level == ConfirmLevel.CLICK:
            return bool(await self.ui.prompt_click(intent))

        elif decision.confirm_level == ConfirmLevel.CLICK_WITH_REVIEW:
            return bool(await self.ui.prompt_click_with_review(intent))

        return False


class UIClientWired:
    """Confirmation by voice or click, whichever comes first.

    Rei reads the action back aloud, then listens. Normal actions (R2) accept
    "yes"/"no"; high-risk ones (R3, and anything tainted) require the word
    "confirm". Clicking Allow/Deny always works. No answer in time means no.
    """

    def __init__(
        self,
        backend: Any,
        confirmer: Optional[VoiceConfirmer] = None,
        say: Optional[Callable[[str], Awaitable[None]]] = None,
        describe: Callable[[IntentProposal], str] = lambda i: i.capability,
        mic_active: Callable[[], bool] = lambda: False,
        on_listen: Callable[[bool], None] = lambda listening: None,
        voice_window_s: float = 10.0,
        click_window_s: float = 30.0,
    ) -> None:
        self.backend = backend
        self.confirmer = confirmer
        self.say = say
        self.describe = describe
        self.mic_active = mic_active
        self.on_listen = on_listen
        self.voice_window_s = voice_window_s
        self.click_window_s = click_window_s
        self.pending_confirmations: dict[str, asyncio.Future[bool]] = {}
        self.backend.response_callback = self._on_response

    def _on_response(self, intent_id: str, approved: bool) -> None:
        if intent_id in self.pending_confirmations:
            if not self.pending_confirmations[intent_id].done():
                self.pending_confirmations[intent_id].set_result(approved)

    async def prompt_voice_or_click(self, intent: IntentProposal) -> bool:
        return await self._request(intent, "Confirm this action", strict=False)

    async def prompt_click(self, intent: IntentProposal) -> bool:
        return await self._request(intent, "High-risk action", strict=True)

    async def prompt_click_with_review(self, intent: IntentProposal) -> bool:
        return await self._request(intent, "Review carefully", strict=True, review=True)

    async def _request(self, intent: IntentProposal, title: str, strict: bool, review: bool = False) -> bool:
        intent_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        click: asyncio.Future[bool] = loop.create_future()
        self.pending_confirmations[intent_id] = click

        action = self.describe(intent)
        voice = self.confirmer is not None and self.mic_active()
        answer_hint = 'Say "confirm" or "no".' if strict else 'Say "yes" or "no".'
        message = action
        if review:
            message += f"\n\nThis request involved content from outside (e.g. an email).\nDetails: {intent.args}"
        timeout = self.voice_window_s if voice else self.click_window_s
        self.backend.confirmationRequested.emit(title, message, intent_id)

        voice_answer: Optional[asyncio.Future[bool]] = None
        try:
            if self.say is not None:
                question = f"{action}. {'Say confirm to go ahead, or no.' if strict else 'Should I? Say yes or no.'}"
                # Answering by click while Rei is still talking is fine
                speak: asyncio.Future[Any] = asyncio.ensure_future(self.say(question))
                first: list[asyncio.Future[Any]] = [speak, click]
                await asyncio.wait(first, return_when=asyncio.FIRST_COMPLETED)
                if click.done():
                    speak.cancel()
                    return click.result()
            if voice and self.confirmer is not None:
                voice_answer = self.confirmer.expect(strict)
                self.on_listen(True)
            # The answer window (and the popup's countdown) starts after the read-back
            if hasattr(self.backend, "confirmationHint"):
                self.backend.confirmationHint.emit(answer_hint if voice else "", int(timeout), strict)
            waiters: list[asyncio.Future[bool]] = [click] + ([voice_answer] if voice_answer else [])
            done, _ = await asyncio.wait(waiters, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
            for fut in done:
                if not fut.cancelled():
                    return bool(fut.result())
            return False  # no answer in time: fail safe
        finally:
            if voice_answer is not None and self.confirmer is not None:
                self.confirmer.cancel()
                self.on_listen(False)
            self.pending_confirmations.pop(intent_id, None)
            if hasattr(self.backend, "confirmationClosed"):
                self.backend.confirmationClosed.emit(intent_id)

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
