import socket
import inspect
from typing import Any, Callable

class EgressBlockedError(Exception):
    pass

_original_socket_connect: Callable[..., Any] = socket.socket.connect
_original_socket_connect_ex: Callable[..., Any] = socket.socket.connect_ex

def _is_loopback(address: Any) -> bool:
    if not isinstance(address, tuple) or len(address) < 2:
        return False
    host = address[0]
    return host in ("127.0.0.1", "localhost", "::1")

def _is_egress_broker_caller() -> bool:
    # Inspect the stack to see if the call originated from rei.egress
    stack = inspect.stack()
    for frame_info in stack:
        module_name = frame_info.frame.f_globals.get("__name__", "")
        if module_name == "rei.egress.socket_guard":
            continue
        if module_name.startswith("rei.egress."):
            return True
    return False

_original_socket = socket.socket

class GuardedSocket(_original_socket):
    def connect(self, address: Any) -> Any:
        if not _is_loopback(address) and not _is_egress_broker_caller():
            raise EgressBlockedError(f"Egress blocked to {address} by socket guard")
        return super().connect(address)

    def connect_ex(self, address: Any) -> Any:
        if not _is_loopback(address) and not _is_egress_broker_caller():
            raise EgressBlockedError(f"Egress blocked to {address} by socket guard")
        return super().connect_ex(address)

def install_socket_guard() -> None:
    socket.socket = GuardedSocket # type: ignore
