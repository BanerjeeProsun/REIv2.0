import hashlib
from typing import Any, Callable
from dataclasses import dataclass
from rei.policy.schemas import PrivacyMode
from rei.capabilities.spec import DataClass
from rei.egress.redactor import Redactor
from rei.policy.config import PolicyConfig
from rei.egress.socket_guard import EgressBlockedError

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

# Modes in which user-approved connector hosts may be contacted
CONNECTOR_MODES = (PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED)


class EgressGate:
    def __init__(
        self,
        config: PolicyConfig,
        current_mode: PrivacyMode,
        connector_hosts: Callable[[], set[str]] = lambda: set(),
    ) -> None:
        self.config = config
        self.current_mode = current_mode
        self.redactor = Redactor(mask_pii=True)
        # Hosts of connectors the user has connected (e.g. imap.gmail.com)
        self.connector_hosts = connector_hosts

    def _assert_mode_allows(self, req: EgressRequest) -> None:
        if self.current_mode == PrivacyMode.LOCAL_ONLY:
            raise EgressBlockedError("Egress blocked in LOCAL_ONLY mode")

    def _is_connector_host(self, destination: str) -> bool:
        """Exact match, or a suffix entry starting with "." (e.g. ".googlevideo.com"
        for YouTube's per-stream hosts like rr3---sn-abc.googlevideo.com)."""
        host = destination.lower().rstrip(".")
        for entry in self.connector_hosts():
            entry = entry.lower()
            if host == entry or (entry.startswith(".") and host.endswith(entry)):
                return True
        return False

    def _assert_host_allowlisted(self, destination: str) -> None:
        if self._is_connector_host(destination):
            if self.current_mode not in CONNECTOR_MODES:
                raise EgressBlockedError(f"Host {destination} not allowed in mode {self.current_mode.value}")
            return
        hosts = self.config.egress.get("hosts", {})
        if destination not in hosts:
            raise EgressBlockedError(f"Host {destination} not in egress allowlist")
        host_config = hosts[destination]
        if self.current_mode.value.lower() not in [m.lower() for m in host_config.modes]:
            raise EgressBlockedError(f"Host {destination} not allowed in mode {self.current_mode.value}")

    def _require_valid_consent(self, consent_ref: str | None) -> None:
        if not consent_ref: # simplified consent check
            raise EgressBlockedError("Missing valid consent for C2 data")

    def check_host(self, destination: str, purpose: str) -> None:
        """Gate a direct connection (IMAP/SMTP, streaming) made by an egress module.

        Raises EgressBlockedError unless the current mode allows network access
        and the host is allowlisted (policy.toml or a connected connector).
        """
        req = EgressRequest(destination=destination, purpose=purpose, payload=[], turn_id="system")
        self._assert_mode_allows(req)
        self._assert_host_allowlisted(destination)
        print(f"Ledger record: Connection to {destination} for {purpose}.")

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

    async def post_http(self, destination: str, purpose: str, url: str, headers: dict[str, str], json_body: dict[str, Any], timeout: Any = None, data_class: DataClass = DataClass.C0) -> Any:
        import httpx
        req = EgressRequest(
            destination=destination,
            purpose=purpose,
            payload=[EgressPayloadPart(data_class=data_class, content=json_body)],
            turn_id="system"
        )
        self._assert_mode_allows(req)
        self._assert_host_allowlisted(req.destination)
        
        if data_class == DataClass.C3:
            raise EgressBlockedError("SECRET data (C3) cannot leave the device")
            
        if data_class == DataClass.C2:
            self._require_valid_consent(None)
            
        redacted_payload, found_secret = self.redactor.redact_payload(json_body)
        if found_secret:
            raise EgressBlockedError("SECRET data (C3) detected during redaction")
            
        payload_digest = hashlib.sha256(str(redacted_payload).encode()).hexdigest()
        print(f"Ledger record: Sent HTTP POST to {url} for {purpose}. Digest: {payload_digest}")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(url, headers=headers, json=redacted_payload)
