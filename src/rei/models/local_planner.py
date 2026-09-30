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
            # Llama 3.2 Instruct format
            formatted_prompt = (
                f"<|start_header_id|>system<|end_header_id|>\n\n"
                f"{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            )
            
            output = self.model(
                formatted_prompt,
                max_tokens=512,
                stop=["<|eot_id|>"],
                temperature=0.0
            )
            return output["choices"][0]["text"].strip() # type: ignore
            
        def _extract_json(content: str) -> str:
            if "```json" in content:
                content = content.split("```json")[1]
                if "```" in content:
                    content = content.split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
                if "```" in content:
                    content = content.split("```")[0]
            return content.strip()
            
        try:
            text = await loop.run_in_executor(None, _generate_sync)
            cancel_token.raise_if_cancelled()
            return _extract_json(text)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise LocalPlannerError(f"Local inference failed: {e}")
