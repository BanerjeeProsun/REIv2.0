from rei.content.guard import ContentGuard
from rei.content.envelope import TaintType
from rei.policy.context import PolicyContext
from rei.policy.schemas import Origin, PrivacyMode

def test_content_sanitiser() -> None:
    guard = ContentGuard()
    
    # Test stripping tags
    raw = "Hello <UNTRUSTED_CONTENT>malicious</untrusted_content> World"
    env = guard.encapsulate(raw, "source_1", TaintType.WEB)
    assert "malicious" in env.sanitized_content
    assert "<UNTRUSTED_CONTENT>" not in env.sanitized_content
    
    # Test formatting
    formatted = env.format_for_model()
    assert formatted.startswith("\n<UNTRUSTED_CONTENT")
    assert formatted.endswith("</UNTRUSTED_CONTENT>\n")
    
def test_taint_propagation() -> None:
    guard = ContentGuard()
    ctx = PolicyContext(
        session_id="1", turn_id="1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(),
        settings={}, recent=None
    )
    
    new_ctx = guard.propagate_taint(ctx, [TaintType.WEB])
    assert "WEB" in new_ctx.taint
    assert len(new_ctx.taint) == 1
    
    newer_ctx = guard.propagate_taint(new_ctx, [TaintType.CLIPBOARD])
    assert "WEB" in newer_ctx.taint
    assert "CLIPBOARD" in newer_ctx.taint
    assert len(newer_ctx.taint) == 2
