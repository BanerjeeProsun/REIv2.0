from rei.egress.anonymizer import Anonymizer, Vault


def test_known_name_is_placeholdered_and_rehydrated() -> None:
    vault = Vault()
    anon = Anonymizer({"USER_NAME": "Ada Lovelace"})
    out = anon.scrub("My name is Ada Lovelace, but call me ada.", vault)
    assert "Ada" not in out and "ada" not in out
    assert out.count("[USER_NAME]") == 2
    assert vault.rehydrate("Hello [USER_NAME]!") == "Hello Ada Lovelace!"


def test_email_and_phone_get_stable_reversible_placeholders() -> None:
    vault = Vault()
    anon = Anonymizer()
    out = anon.scrub("Mail a@b.com or a@b.com, phone 555-123-4567", vault)
    assert "a@b.com" not in out and "555" not in out
    assert out.count("[EMAIL_1]") == 2
    assert "[PHONE_1]" in out
    assert vault.rehydrate(out) == "Mail a@b.com or a@b.com, phone 555-123-4567"


def test_secrets_are_irreversible() -> None:
    vault = Vault()
    anon = Anonymizer()
    token = "ghp_" + "a" * 36
    out = anon.scrub(f"my token is {token}", vault)
    assert token not in out
    assert "<REDACTED_GH_TOKEN>" in out
    assert len(vault) == 0
    assert token not in vault.rehydrate(out)
    assert anon.stats.secrets_removed == 1


def test_spans_only_replace_verbatim_text() -> None:
    vault = Vault()
    anon = Anonymizer()
    text = "Send the report to Grace at Contoso"
    # A hallucinated span that is not in the text must not change anything
    out = anon.apply_spans(text, [("Grace", "NAME"), ("Contoso", "ORG"), ("Bob", "NAME")], vault)
    assert out == "Send the report to [NAME_1] at [ORG_1]"
    assert vault.rehydrate(out) == text


def test_secret_span_is_dropped_not_vaulted() -> None:
    vault = Vault()
    anon = Anonymizer()
    out = anon.apply_spans("password hunter2 please", [("hunter2", "SECRET")], vault)
    assert out == "password <REDACTED_SECRET> please"
    assert len(vault) == 0


def test_rehydrate_obj_restores_nested_args() -> None:
    vault = Vault()
    anon = Anonymizer({"USER_NAME": "Ada"})
    anon.scrub("Ada", vault)
    assert vault.rehydrate_obj({"content": ["hi [USER_NAME]"], "n": 1}) == {"content": ["hi Ada"], "n": 1}
