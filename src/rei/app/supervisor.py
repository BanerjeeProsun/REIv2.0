import asyncio
import subprocess
import time
from typing import Optional
from rei.app.job_object import ProcessJobObject


class ChildProcess:
    def __init__(self, name: str, args: list[str], job: ProcessJobObject) -> None:
        self.name = name
        self.args = args
        self.job = job
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.restart_times: list[float] = []
        self.in_safe_mode = False

    def start(self) -> None:
        if self.in_safe_mode:
            return

        now = time.time()
        # Keep only restarts within last 60s
        self.restart_times = [t for t in self.restart_times if now - t < 60]

        if len(self.restart_times) >= 3:
            print(f"[{self.name}] Crash loop detected (3 restarts in 60s). Entering safe mode.")
            self.in_safe_mode = True
            return

        print(f"[{self.name}] Starting process...")
        self.process = subprocess.Popen(self.args, shell=False)  # noqa: S603
        self.job.assign_process(self.process)
        self.restart_times.append(now)

    async def stop(self) -> None:
        if not self.process or self.process.poll() is not None:
            return

        print(f"[{self.name}] Sending graceful shutdown...")
        # In real code, signal via IPC. Here we mock waiting.
        # await ipc.send_shutdown(self.name)

        for _ in range(50):  # wait up to 5s
            if self.process.poll() is not None:
                break
            await asyncio.sleep(0.1)

        if self.process.poll() is None:
            print(f"[{self.name}] Force terminating by handle...")
            self.process.terminate()
            self.process.wait(timeout=2.0)


class Supervisor:
    def __init__(self) -> None:
        self.job = ProcessJobObject()
        self.children: dict[str, ChildProcess] = {}

    def add_child(self, name: str, args: list[str]) -> None:
        self.children[name] = ChildProcess(name, args, self.job)

    async def run(self) -> None:
        for child in self.children.values():
            child.start()

        try:
            while True:
                for child in self.children.values():
                    if child.process and child.process.poll() is not None and not child.in_safe_mode:
                        print(f"[{child.name}] Process exited unexpectedly, restarting...")
                        child.start()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("Supervisor shutting down...")
            for child in self.children.values():
                await child.stop()
