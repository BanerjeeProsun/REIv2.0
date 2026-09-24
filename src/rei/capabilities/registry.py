from typing import Callable, Any, Dict
from pydantic import BaseModel
from rei.capabilities.spec import CapabilitySpec, RiskTier


class UnknownCapabilityError(Exception):
    pass


class InvalidCapabilitySpecError(Exception):
    pass


class CapabilityRegistry:
    def __init__(self) -> None:
        self._specs: Dict[str, CapabilitySpec] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register(self, spec: CapabilitySpec, handler: Callable[..., Any]) -> None:
        if spec.tier == RiskTier.R4:
            raise InvalidCapabilitySpecError(f"Cannot register R4 capability: {spec.id}")

        self._specs[spec.id] = spec
        self._handlers[spec.id] = handler

    def get_spec(self, capability_id: str) -> CapabilitySpec:
        if capability_id not in self._specs:
            raise UnknownCapabilityError(f"UNKNOWN_CAPABILITY: {capability_id}")
        return self._specs[capability_id]

    def execute(self, capability_id: str, args: BaseModel) -> Any:
        if capability_id not in self._handlers:
            raise UnknownCapabilityError(f"UNKNOWN_CAPABILITY: {capability_id}")

        handler = self._handlers[capability_id]
        return handler(args)

    def get_all_specs(self) -> list[CapabilitySpec]:
        return list(self._specs.values())
