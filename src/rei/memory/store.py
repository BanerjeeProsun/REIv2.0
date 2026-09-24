from typing import Any
from rei.policy.context import PolicyContext

class MemoryWriteBlockedError(Exception):
    pass

class MemoryStore:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def write(self, key: str, value: Any, ctx: PolicyContext) -> None:
        # MEM-01: No memory writes from tainted contexts
        if ctx.taint:
            raise MemoryWriteBlockedError("Cannot write to memory during a tainted turn")
            
        self.data[key] = value

    def read(self, key: str) -> Any:
        return self.data.get(key)
