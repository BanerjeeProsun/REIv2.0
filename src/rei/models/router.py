from enum import Enum
from typing import Any, Optional
from rei.models.adapter import ModelAdapter
from rei.models.formatter import LocalFormatter
from rei.core.cancellation import CancelToken
from rei.policy.schemas import PrivacyMode


class Route(Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class ModelRouter(ModelAdapter):
    """
    Chooses between the on-device and cloud planners.

    The cloud planner is only used in Cloud Assisted mode, and only with a
    prompt that has been sanitized by the caller (see Orchestrator._propose).
    generate() is always local, so an unsanitized prompt can never leave the device.
    """
    def __init__(self, cloud_model: Optional[ModelAdapter], local_model: Optional[ModelAdapter]):
        self.cloud_model = cloud_model
        self.local_model = local_model
        # The local model doubles as the privacy formatter in front of the cloud
        self.formatter: LocalFormatter | None = (
            LocalFormatter(local_model) if local_model is not None and hasattr(local_model, "generate_json") else None
        )

    def route(self, privacy_mode: PrivacyMode) -> Route:
        if privacy_mode == PrivacyMode.CLOUD_ASSISTED and self.cloud_model is not None:
            return Route.CLOUD
        return Route.LOCAL

    async def generate(self, prompt: str, cancel_token: CancelToken, deadline_ms: int = 60000) -> str:
        return await self.generate_local(prompt, cancel_token, deadline_ms)

    async def generate_local(
        self,
        prompt: str,
        cancel_token: CancelToken,
        deadline_ms: int = 60000,
        schema: dict[str, Any] | None = None,
    ) -> str:
        if not self.local_model:
            raise RuntimeError("No local model available")
        print("Routing to Local Model (Llama 1B)...")
        generate_json = getattr(self.local_model, "generate_json", None)
        if schema is not None and generate_json is not None:
            # Registry-derived grammar: the small model can only emit valid intents
            return str(await generate_json(None, prompt, schema, cancel_token, deadline_ms=deadline_ms, max_tokens=512))
        return await self.local_model.generate(prompt, cancel_token, deadline_ms=deadline_ms)

    async def generate_cloud(self, sanitized_prompt: str, cancel_token: CancelToken, deadline_ms: int = 15000) -> str:
        if not self.cloud_model:
            raise RuntimeError("No cloud model available")
        print("Routing to Cloud Model (NIM)...")
        return await self.cloud_model.generate(sanitized_prompt, cancel_token, deadline_ms=deadline_ms)
