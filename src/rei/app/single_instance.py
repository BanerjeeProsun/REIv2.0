import ctypes
import sys
from typing import Any


def enforce_single_instance(session_uuid: str) -> Any:
    mutex_name = f"Global\\Rei-Mutex-{session_uuid}"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        print("Rei is already running in this session.")
        sys.exit(0)

    return mutex
