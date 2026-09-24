import pytest
import socket
from rei.egress.socket_guard import install_socket_guard, EgressBlockedError

def test_socket_guard() -> None:
    # Need to save original to restore later so we don't break pytest
    orig_socket = socket.socket
    
    install_socket_guard()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Loopback should be allowed (we mock the connect by catching ConnectionRefusedError)
        try:
            s.connect(("127.0.0.1", 12345))
        except (ConnectionRefusedError, TimeoutError):
            pass # Expected
            
        # Non-loopback should raise EgressBlockedError
        with pytest.raises(EgressBlockedError):
            s.connect(("8.8.8.8", 53))
            
    finally:
        socket.socket = orig_socket
