import time
import uuid
import hmac
import hashlib
import json
from typing import Any
from rei.intents.schemas import IntentProposal
from rei.policy.context import PolicyContext
from rei.policy.schemas import PolicyDecision, Verdict, ConfirmLevel, Origin
from rei.policy.grant import GrantToken
from rei.capabilities.registry import CapabilityRegistry, UnknownCapabilityError
from rei.capabilities.spec import RiskTier

class PolicyEngineError(Exception):
    pass

class PolicyEngine:
    def __init__(self, registry: CapabilityRegistry, config: dict[str, Any], grant_key: bytes) -> None:
        self.registry = registry
        self.config = config
        self.grant_key = grant_key
        self.policy_version = config.get("version", "unknown")

    def decide(self, intent: IntentProposal, ctx: PolicyContext) -> PolicyDecision:
        try:
            # 1. Integrity
            try:
                spec = self.registry.get_spec(intent.capability)
            except UnknownCapabilityError:
                return self._deny("UNKNOWN_CAPABILITY")
                
            if spec.version != intent.capability_version:
                return self._deny("VERSION_MISMATCH")
                
            try:
                spec.args_model.model_validate(intent.args)
            except Exception:
                return self._deny("SCHEMA_INVALID")
                
            # 2. Kill switches
            if self.config.get("defaults", {}).get("safe_mode"):
                return self._deny("SAFE_MODE")
            
            disabled = self.config.get("disabled", {}).get("capabilities", [])
            if intent.capability in disabled:
                return self._deny("CAPABILITY_DISABLED")
                
            if ctx.privacy_mode not in spec.modes:
                return self._deny("MODE_NOT_ALLOWED")
                
            # 3. Origin
            if ctx.origin == Origin.WORKER and not getattr(spec, "worker_allowed", False): 
                # The capability spec doesn't have worker_allowed explicitly in the snippet 
                # but it's an architecture rule.
                # Let's say if we didn't add it, we check if it's there.
                return self._deny("ORIGIN_WORKER_NOT_ALLOWED")
                
            # 4. Taint
            if ctx.taint and not spec.allow_when_tainted:
                return self._deny("TAINTED_BLOCKED")
                
            # 5. Data egress
            if spec.network:
                # Egress pre-check mock
                if ctx.privacy_mode.value == "LOCAL_ONLY":
                    return self._deny("EGRESS_BLOCKED_LOCAL_ONLY")
                    
            # 6. Rate limits
            # Rate limit mock logic
            limit = spec.rate_limit
            if limit and limit.limit < 1: # simplistic
                return self._deny("RATE_LIMITED")
                
            # 7 & 8 & 9. Base tier, Escalation, Pre-authorisation
            pre_auths = self.config.get("preauthorise", {}).get("allowed", [])
            is_pre_auth = (
                intent.capability in pre_auths 
                and ctx.origin in (Origin.USER_VOICE, Origin.USER_TYPED) 
                and not ctx.taint
            )
            
            if spec.tier in (RiskTier.R0, RiskTier.R1):
                if ctx.taint:
                    return self._escalate(ConfirmLevel.VOICE_OR_CLICK, "TAINT_ESCALATION")
                return self._allow()
                
            elif spec.tier == RiskTier.R2:
                if is_pre_auth:
                    return self._allow()
                if ctx.taint:
                    return self._escalate(ConfirmLevel.CLICK, "TAINT_ESCALATION")
                return self._escalate(ConfirmLevel.VOICE_OR_CLICK, "TIER_R2")
                
            elif spec.tier == RiskTier.R3:
                if ctx.taint:
                    return self._escalate(ConfirmLevel.CLICK_WITH_REVIEW, "TAINT_ESCALATION")
                return self._escalate(ConfirmLevel.CLICK, "TIER_R3")
                
            # 10. Default
            return self._deny("NO_RULE")

        except Exception:
            # POL-02: Any exception yields DENY
            return self._deny("INTERNAL_ERROR")

    def issue_grant(
        self, intent: IntentProposal, ctx: PolicyContext, decision: PolicyDecision
    ) -> tuple[GrantToken, str]:
        # Single-use bound token
        spec = self.registry.get_spec(intent.capability)
        
        args_sha256 = hashlib.sha256(self._canonical_json(intent.args)).hexdigest()
        
        token = GrantToken(
            grant_id=str(uuid.uuid4()),
            turn_id=ctx.turn_id,
            capability=intent.capability,
            capability_version=intent.capability_version,
            args_sha256=args_sha256,
            tier=spec.tier.value,
            confirmed_by=decision.confirm_level.value if decision.confirm_level else "NONE",
            taint=[str(t) for t in ctx.taint],
            issued_at=time.time(),
            expires_at=time.time() + 30.0,
            nonce=uuid.uuid4().hex
        )
        
        mac = self._compute_mac(token)
        return token, mac

    def _canonical_json(self, data: Any) -> bytes:
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')

    def _compute_mac(self, token: GrantToken) -> str:
        payload = self._canonical_json(token.model_dump())
        return hmac.new(self.grant_key, payload, hashlib.sha256).hexdigest()

    def _deny(self, reason: str) -> PolicyDecision:
        return PolicyDecision(Verdict.DENY, None, (reason,), self.policy_version)
        
    def _allow(self) -> PolicyDecision:
        return PolicyDecision(Verdict.ALLOW, None, ("ALLOW",), self.policy_version)
        
    def _escalate(self, level: ConfirmLevel, reason: str) -> PolicyDecision:
        return PolicyDecision(Verdict.CONFIRM, level, (reason,), self.policy_version)
