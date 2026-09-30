from typing import Optional
from rei.models.adapter import ModelAdapter
from rei.core.cancellation import CancelToken


class ModelRouter(ModelAdapter):
    """
    Routes inference requests based on active models and handles graceful fallback.
    """
    def __init__(self, cloud_model: Optional[ModelAdapter], local_model: Optional[ModelAdapter]):
        self.cloud_model = cloud_model
        self.local_model = local_model
        
    async def generate(self, prompt: str, cancel_token: CancelToken, deadline_ms: int = 15000) -> str:
        # Try cloud model first if available
        if self.cloud_model:
            try:
                print("Routing to Cloud Model (NIM)...")
                response = await self.cloud_model.generate(prompt, cancel_token, deadline_ms=deadline_ms)
                return response
            except Exception as e:
                print(f"Cloud Model failed ({e}). Gracefully falling back to Local Model...")
                
        # Fallback to local model
        if self.local_model:
            print("Routing to Local Model (Llama 1B)...")
            return await self.local_model.generate(prompt, cancel_token, deadline_ms=deadline_ms)
            
        raise RuntimeError("No models available (both cloud and local failed or are uninitialized)")

    async def format_intent(self, utterance: str, cancel_token: CancelToken) -> str:
        if not self.local_model:
            return utterance
            
        prompt = (
            "You are a strict data-privacy formatter. "
            "Rewrite the following user intent to remove any sensitive Personal Identifiable Information "
            "(PII), secrets, or private keys, replacing them with placeholders like [REDACTED_NAME] or [REDACTED_KEY]. "
            "If there is no sensitive data, output the original string exactly. Do not add conversational text. "
            f"\n\nUser Input: {utterance}"
        )
        try:
            # We enforce a strict short deadline for the formatter to keep the UI snappy
            formatted = await self.local_model.generate(prompt, cancel_token, deadline_ms=5000)
            print(f"[ModelRouter] Local model formatted intent: {formatted}")
            return formatted.strip()
        except Exception as e:
            print(f"[ModelRouter] Local model formatter failed ({e}). Proceeding with original utterance.")
            return utterance
