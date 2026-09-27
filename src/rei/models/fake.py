import asyncio
from rei.models.adapter import ModelAdapter
from rei.core.cancellation import CancelToken


class FakeModel(ModelAdapter):
    """Deterministic fake model for testing (TST-02).
    
    Returns pre-configured responses based on keyword matching.
    Used in unit tests and the demo harness to verify the pipeline
    without requiring actual model weights.
    """

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or self._default_responses()

    def _default_responses(self) -> dict[str, str]:
        return {
            "open notepad": (
                '{"intents": [{"type": "intent", "capability": "apps.open",'
                ' "capability_version": 1, "args": {"app": "notepad"},'
                ' "rationale": "User asked to open Notepad"}]}'
            ),
            "set volume to 50": (
                '{"intents": [{"type": "intent", "capability": "media.set_volume",'
                ' "capability_version": 1, "args": {"level": 50},'
                ' "rationale": "User asked to set volume to 50"}]}'
            ),
            "open google": (
                '{"intents": [{"type": "intent", "capability": "web.open_url",'
                ' "capability_version": 1, "args": {"url": "https://google.com"},'
                ' "rationale": "User asked to open Google"}]}'
            ),
            "lock my computer": (
                '{"intents": [{"type": "intent", "capability": "system.lock",'
                ' "capability_version": 1, "args": {},'
                ' "rationale": "User asked to lock the computer"}]}'
            ),
        }

    async def generate(
        self,
        prompt: str,
        cancel_token: CancelToken,
        deadline_ms: int = 5000,
    ) -> str:
        cancel_token.raise_if_cancelled()
        await asyncio.sleep(0.01)

        # Extract the user utterance from the full prompt
        # The prompt builder formats it as "User said: <utterance>"
        search_text = prompt.lower()
        user_said_marker = "user said:"
        marker_idx = search_text.find(user_said_marker)
        if marker_idx != -1:
            search_text = search_text[marker_idx + len(user_said_marker):]

        # Match the user utterance against known responses
        for keyword, response in self._responses.items():
            if keyword in search_text:
                return response

        # Default: return a conversational non-intent response
        return (
            '{"intents": [], "reply": "I understood your request'
            ' but I don\'t have a capability for that."}'
        )
