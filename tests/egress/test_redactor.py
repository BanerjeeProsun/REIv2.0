from rei.egress.redactor import Redactor

def test_redactor_secrets() -> None:
    redactor = Redactor()
    payload = {
        "user_message": "My key is ghp_123456789012345678901234567890123456",
        "safe_data": "Hello world"
    }
    redacted, found = redactor.redact_payload(payload)
    
    assert found
    assert "ghp_" not in redacted["user_message"]
    assert "<REDACTED_GH_TOKEN>" in redacted["user_message"]
    assert redacted["safe_data"] == "Hello world"

def test_redactor_pii() -> None:
    redactor = Redactor(mask_pii=True)
    text = "Contact me at user@example.com or 555-123-4567."
    redacted, found = redactor.redact_payload(text)
    
    assert not found # PII is not a C3 secret, just masked
    assert "user@example.com" not in redacted
    assert "<REDACTED_EMAIL>" in redacted
    assert "555-123-4567" not in redacted
    assert "<REDACTED_PHONE>" in redacted
