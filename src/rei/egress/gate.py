import hashlib
from typing import Any
from dataclasses import dataclass
from rei.policy.schemas import PrivacyMode
from rei.capabilities.spec import DataClass
from rei.egress.redactor import Redactor
from rei.policy.config import PolicyConfig

class EgressBlockedError(Exception):
    pass

@dataclass
class EgressPayloadPart:
    data_class: DataClass
    content: Any

@dataclass
class EgressRequest:
    destination: str
    purpose: str
    payload: list[EgressPayloadPart]
    turn_id: str
    consent_ref: str | None = None

class EgressGate:
    def __init__(self, config: PolicyConfig, current_mode: PrivacyMode) -> None:
        self.config = config
        self.current_mode = current_mode
        self.redactor = Redactor(mask_pii=True)

    def _assert_mode_allows(self, req: EgressRequest) -> None:
        if self.current_mode == PrivacyMode.LOCAL_ONLY:
            raise EgressBlockedError("Egress blocked in LOCAL_ONLY mode")

    def _assert_host_allowlisted(self, destination: str) -> None:
        hosts = self.config.egress.get("hosts", {})
        if destination not in hosts:
            raise EgressBlockedError(f"Host {destination} not in egress allowlist")
        host_config = hosts[destination]
        if self.current_mode.value not in host_config.modes:
            raise EgressBlockedError(f"Host {destination} not allowed in mode {self.current_mode.value}")

    def _require_valid_consent(self, consent_ref: str | None) -> None:
        if not consent_ref: # simplified consent check
            raise EgressBlockedError("Missing valid consent for C2 data")

    async def send(self, req: EgressRequest) -> Any:
        self._assert_mode_allows(req)
        self._assert_host_allowlisted(req.destination)
        
        max_class = DataClass.C0
        raw_payloads = []
        for part in req.payload:
            if part.data_class.value > max_class.value:
                max_class = part.data_class
            raw_payloads.append(part.content)
            
        if max_class == DataClass.C3:
            raise EgressBlockedError("SECRET data (C3) cannot leave the device")
            
        if max_class == DataClass.C2:
            self._require_valid_consent(req.consent_ref)
            
        # Redact payload
        redacted_payload, found_secret = self.redactor.redact_payload(raw_payloads)
        if found_secret:
            raise EgressBlockedError("SECRET data (C3) detected during redaction")
            
        # In a real app, record to ledger and send via httpx
        payload_digest = hashlib.sha256(str(redacted_payload).encode()).hexdigest()
        print(f"Ledger record: Sent data to {req.destination} for {req.purpose}. Digest: {payload_digest}")
        
        return {"status": "mock_sent", "digest": payload_digest}
