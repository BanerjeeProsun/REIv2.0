from rei.content.envelope import ContentEnvelope, TaintType
from rei.content.sanitiser import ContentSanitiser
from rei.policy.context import PolicyContext

class ContentGuard:
    def __init__(self) -> None:
        self.sanitiser = ContentSanitiser()
        
    def encapsulate(self, raw: str, source_id: str, taint: TaintType) -> ContentEnvelope:
        clean = self.sanitiser.sanitize(raw)
        return ContentEnvelope(
            source_id=source_id,
            taint=taint,
            raw_content=raw,
            sanitized_content=clean
        )
        
    def propagate_taint(self, ctx: PolicyContext, new_taints: list[TaintType]) -> PolicyContext:
        current = set(ctx.taint)
        for t in new_taints:
            current.add(t.value)
            
        return PolicyContext(
            session_id=ctx.session_id,
            turn_id=ctx.turn_id,
            origin=ctx.origin,
            privacy_mode=ctx.privacy_mode,
            taint=frozenset(current),
            settings=ctx.settings,
            recent=ctx.recent
        )
