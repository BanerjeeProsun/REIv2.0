import asyncio
from pathlib import Path
from rei.models.adapter import ModelAdapter
from rei.core.cancellation import CancelToken

class LocalPlannerError(Exception):
    pass

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

    async def generate(self, prompt: str, cancel_token: CancelToken, deadline_ms: int = 5000) -> str:
        cancel_token.raise_if_cancelled()
        
        loop = asyncio.get_running_loop()
        
        def _generate_sync() -> str:
            # Simple text generation
            output = self.model(
                prompt,
                max_tokens=256,
                stop=["User said:"],
                echo=False
            )
            return output["choices"][0]["text"] # type: ignore
            
        try:
            # TODO: apply deadline_ms via asyncio.wait_for
            text = await loop.run_in_executor(None, _generate_sync)
            cancel_token.raise_if_cancelled()
            return text
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise LocalPlannerError(f"Local inference failed: {e}")
