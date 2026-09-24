import time
import hmac
import hashlib
import json
from typing import Any
from pydantic import BaseModel
from rei.policy.grant import GrantToken
from rei.capabilities.registry import CapabilityRegistry

class GrantVerificationError(Exception):
    pass

class GrantVerifier:
    def __init__(self, registry: CapabilityRegistry, grant_key: bytes) -> None:
        self.registry = registry
        self.grant_key = grant_key
        self.consumed_nonces: set[str] = set()
        
    def _canonical_json(self, data: Any) -> bytes:
        if isinstance(data, BaseModel):
            data = data.model_dump()
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
        
    def _hash_args(self, args: Any) -> str:
        return hashlib.sha256(self._canonical_json(args)).hexdigest()
        
    def _compute_mac(self, token: GrantToken) -> str:
        # MAC over the token excluding the mac itself
        token_dict = token.model_dump()
        payload = self._canonical_json(token_dict)
        return hmac.new(self.grant_key, payload, hashlib.sha256).hexdigest()

    def verify(self, token: GrantToken, args: Any, provided_mac: str) -> None:
        # 1. MAC valid under grant_key
        expected_mac = self._compute_mac(token)
        if not hmac.compare_digest(expected_mac, provided_mac):
            raise GrantVerificationError("Invalid MAC")
            
        # 2. now < expires_at
        if time.time() > token.expires_at:
            raise GrantVerificationError("Token expired")
            
        # 3. nonce not in consumed set
        if token.nonce in self.consumed_nonces:
            raise GrantVerificationError("Token already consumed (nonce replay)")
            
        # 4. args_sha256 == sha256(canonical_json(received_args))
        if token.args_sha256 != self._hash_args(args):
            raise GrantVerificationError("Argument hash mismatch")
            
        # 5. capability/version registered in host
        spec = self.registry.get_spec(token.capability)
        if spec.version != token.capability_version:
            raise GrantVerificationError("Capability version mismatch")
            
        # 6. tier in token == tier in host registry
        if spec.tier.value != token.tier:
            raise GrantVerificationError("Capability tier mismatch")
            
        # Consume the nonce (in a real system, use an LRU cache)
        self.consumed_nonces.add(token.nonce)
        if len(self.consumed_nonces) > 10000:
            # Simple bounded cache
            self.consumed_nonces.clear()
