import pytest
from rei.memory.store import MemoryStore, MemoryWriteBlockedError
from rei.policy.context import PolicyContext
from rei.policy.schemas import Origin, PrivacyMode
from rei.capabilities.spec import DataClass

def test_memory_store_clean_write() -> None:
    store = MemoryStore()
    ctx = PolicyContext(
        session_id="1", turn_id="1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(),
        settings={}, recent=None
    )
    store.write("user_name", "Alice", "fact", DataClass.C2, 1000, ctx)
    assert store.read("user_name") == "Alice"

def test_memory_store_tainted_write_blocked() -> None:
    store = MemoryStore()
    ctx = PolicyContext(
        session_id="1", turn_id="1", origin=Origin.USER_VOICE,
        privacy_mode=PrivacyMode.LOCAL_ONLY, taint=frozenset(["WEB"]),
        settings={}, recent=None
    )
    with pytest.raises(MemoryWriteBlockedError):
        store.write("user_name", "Bob", "fact", DataClass.C2, 1000, ctx)
        
    assert store.read("user_name") is None
