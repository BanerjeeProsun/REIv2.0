import sys
import asyncio
import pytest
from rei.app.supervisor import Supervisor


@pytest.mark.asyncio
async def test_supervisor_crash_loop() -> None:
    supervisor = Supervisor()

    # We will run a script that crashes immediately
    supervisor.add_child("crasher", [sys.executable, "tests/fixtures/dummy_child.py", "crash"])

    # Start the supervisor as a task
    task = asyncio.create_task(supervisor.run())

    # Wait for the crash loop to be detected (3 restarts in 60s)
    # The child exits immediately, so 3 restarts should happen very fast.
    await asyncio.sleep(4.0)

    child = supervisor.children["crasher"]
    assert child.in_safe_mode

    # Clean up
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
