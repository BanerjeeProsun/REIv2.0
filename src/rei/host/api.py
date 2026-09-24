import secrets
from typing import Callable, Any

class UnauthorizedError(Exception):
    pass

class APIHardeningMiddleware:
    def __init__(self) -> None:
        # Per-launch token (API-01)
        self.launch_token = secrets.token_urlsafe(32)
        self.max_body_size = 1024 * 1024 # 1MB limit
        
    def verify_request(self, token: str, host_header: str, body_size: int) -> None:
        # API-01: Must bear the per-launch token
        if not secrets.compare_digest(self.launch_token, token):
            raise UnauthorizedError("Invalid launch token")
            
        # API-02: Must verify Host == localhost
        if host_header not in ("localhost", "127.0.0.1"):
            raise UnauthorizedError("Invalid Host header")
            
        # API-05: Enforce body limits
        if body_size > self.max_body_size:
            raise UnauthorizedError("Payload too large")
            
    def wrap_endpoint(self, endpoint: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(token: str, host_header: str, body_size: int, *args: Any, **kwargs: Any) -> Any:
            self.verify_request(token, host_header, body_size)
            return endpoint(*args, **kwargs)
        return wrapper
