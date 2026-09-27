import asyncio
from typing import Any


class ModelManager:
    """Serialized GPU access manager (CON-03).
    
    Ensures only one model occupies VRAM at a time when budget is tight.
    Models must acquire a slot before loading and release it when done.
    """

    def __init__(self, vram_budget_mb: int = 4096) -> None:
        self.vram_budget_mb = vram_budget_mb
        self._allocated: dict[str, int] = {}
        self._lock = asyncio.Lock()

    @property
    def available_mb(self) -> int:
        return self.vram_budget_mb - sum(self._allocated.values())

    async def acquire(self, model_name: str, vram_mb: int) -> None:
        async with self._lock:
            if vram_mb > self.available_mb:
                raise MemoryError(
                    f"Cannot allocate {vram_mb}MB for {model_name}."
                    f" Available: {self.available_mb}MB"
                )
            self._allocated[model_name] = vram_mb

    def release(self, model_name: str) -> None:
        self._allocated.pop(model_name, None)

    def status(self) -> dict[str, Any]:
        return {
            "budget_mb": self.vram_budget_mb,
            "allocated": dict(self._allocated),
            "available_mb": self.available_mb,
        }
