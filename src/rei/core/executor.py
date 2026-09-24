from typing import Any
from pydantic import BaseModel
from rei.policy.grant import GrantToken
from rei.host.verify import GrantVerifier, GrantVerificationError
from rei.capabilities.registry import CapabilityRegistry

class ExecutorError(Exception):
    pass

class Executor:
    def __init__(self, registry: CapabilityRegistry, verifier: GrantVerifier) -> None:
        self.registry = registry
        self.verifier = verifier

    def execute(self, token: GrantToken, args: BaseModel, mac: str) -> Any:
        try:
            # 1. Host verifies token
            self.verifier.verify(token, args, mac)
            
            # 2. Execute capability
            result = self.registry.execute(token.capability, args)
            return {"status": "success", "data": result}
            
        except GrantVerificationError as e:
            raise ExecutorError(f"Grant verification failed: {e}")
        except Exception as e:
            raise ExecutorError(f"Capability execution failed: {e}")
