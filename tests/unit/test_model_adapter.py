import pytest
import asyncio
from rei.models.fake import FakeModel
from rei.models.manager import ModelManager
from rei.core.cancellation import CancelToken


@pytest.mark.asyncio
async def test_fake_model_known_command() -> None:
    model = FakeModel()
    token = CancelToken()
    result = await model.generate("open notepad", token)
    assert "apps.open" in result
    assert "notepad" in result


@pytest.mark.asyncio
async def test_fake_model_unknown_command() -> None:
    model = FakeModel()
    token = CancelToken()
    result = await model.generate("fly me to the moon", token)
    assert "intents" in result
    assert '"intents": []' in result


@pytest.mark.asyncio
async def test_fake_model_cancelled() -> None:
    model = FakeModel()
    token = CancelToken()
    token.cancel()
    with pytest.raises(asyncio.CancelledError):
        await model.generate("open notepad", token)


@pytest.mark.asyncio
async def test_model_manager_acquire_release() -> None:
    mgr = ModelManager(vram_budget_mb=1000)
    await mgr.acquire("whisper", 300)
    assert mgr.available_mb == 700
    await mgr.acquire("kokoro", 200)
    assert mgr.available_mb == 500
    mgr.release("whisper")
    assert mgr.available_mb == 800


@pytest.mark.asyncio
async def test_model_manager_over_budget() -> None:
    mgr = ModelManager(vram_budget_mb=500)
    await mgr.acquire("whisper", 300)
    with pytest.raises(MemoryError):
        await mgr.acquire("llm", 400)
