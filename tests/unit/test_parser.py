import pytest
from rei.intents.parser import IntentParser, IntentParserError

def test_intent_parser_valid_json() -> None:
    parser = IntentParser()
    raw = """
    Here is my thought process.
    ```json
    {
        "type": "intent",
        "capability": "media.set_volume",
        "capability_version": 1,
        "args": {"level": 40},
        "rationale": "turn down"
    }
    ```
    """
    intents = parser.parse(raw)
    assert len(intents) == 1
    assert intents[0].capability == "media.set_volume"

def test_intent_parser_max_intents() -> None:
    parser = IntentParser()
    raw = """
    [
        {"type": "intent", "capability": "m1", "capability_version": 1, "args": {}, "rationale": "1"},
        {"type": "intent", "capability": "m2", "capability_version": 1, "args": {}, "rationale": "2"},
        {"type": "intent", "capability": "m3", "capability_version": 1, "args": {}, "rationale": "3"},
        {"type": "intent", "capability": "m4", "capability_version": 1, "args": {}, "rationale": "4"}
    ]
    """
    intents = parser.parse(raw)
    assert len(intents) == 3

def test_intent_parser_invalid_json() -> None:
    parser = IntentParser()
    with pytest.raises(IntentParserError):
        parser.parse("Just plain text, no json here.")
