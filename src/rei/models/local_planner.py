import asyncio
import json
import threading
from pathlib import Path
from typing import Any
from rei.models.adapter import ModelAdapter
from rei.core.cancellation import CancelToken

class LocalPlannerError(Exception):
    pass


# Grammar-constrained output shape for the planner. llama.cpp compiles this
# into a GBNF grammar, so the small model can only emit valid JSON of this form
# (conversational replies go in "reply" instead of breaking the parser).
PLANNER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "intents": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["intent"]},
                    "capability": {"type": "string"},
                    "capability_version": {"type": "integer"},
                    "args": {"type": "object"},
                    "rationale": {"type": "string"},
                },
                "required": ["type", "capability", "capability_version", "args", "rationale"],
            },
        },
    },
    "required": ["reply", "intents"],
}


class LocalPlanner(ModelAdapter):
    """Wraps llama-cpp-python for local GGUF inference."""

    def __init__(self, model_path: Path, n_ctx: int = 4096, n_threads: int | None = None) -> None:
        try:
            from llama_cpp import Llama
        except ImportError:
            raise LocalPlannerError(
                "llama-cpp-python is not installed. Please install it to use LocalPlanner."
            )

        if not model_path.exists():
            raise LocalPlannerError(f"Model file not found: {model_path}")

        try:
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=n_ctx,
                n_threads=n_threads,
                verbose=False
            )
        except Exception as e:
            raise LocalPlannerError(f"Failed to load GGUF model: {e}")

        # llama.cpp contexts are not thread-safe; a timed-out call may still be
        # running in its worker thread when the next one starts.
        self._lock = threading.Lock()

    async def generate(self, prompt: str, cancel_token: CancelToken, deadline_ms: int = 60000) -> str:
        return await self.generate_json(
            system=None,
            user=prompt,
            schema=PLANNER_SCHEMA,
            cancel_token=cancel_token,
            deadline_ms=deadline_ms,
            max_tokens=512,
        )

    async def generate_json(
        self,
        system: str | None,
        user: str,
        schema: dict[str, Any],
        cancel_token: CancelToken,
        deadline_ms: int = 60000,
        max_tokens: int = 512,
    ) -> str:
        """Chat completion constrained to `schema`. Returns a JSON string."""
        cancel_token.raise_if_cancelled()

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        def _generate_sync() -> str:
            with self._lock:
                output = self.model.create_chat_completion(
                    messages=messages,  # type: ignore[arg-type]
                    response_format={"type": "json_object", "schema": schema},
                    max_tokens=max_tokens,
                    temperature=0.0,
                )
            return str(output["choices"][0]["message"]["content"] or "").strip()  # type: ignore[index]

        loop = asyncio.get_running_loop()
        try:
            text = await asyncio.wait_for(
                loop.run_in_executor(None, _generate_sync), timeout=deadline_ms / 1000.0
            )
        except asyncio.TimeoutError:
            raise LocalPlannerError(f"Local inference exceeded {deadline_ms} ms")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise LocalPlannerError(f"Local inference failed: {e}")

        cancel_token.raise_if_cancelled()
        # Grammar guarantees JSON, but max_tokens can truncate it
        try:
            json.loads(text)
        except json.JSONDecodeError:
            print("[LocalPlanner] Output truncated or malformed; returning raw text.")
        return text
