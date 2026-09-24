import pytest
from rei.host.api import APIHardeningMiddleware, UnauthorizedError

def test_api_hardening() -> None:
    middleware = APIHardeningMiddleware()
    valid_token = middleware.launch_token
    
    # Valid
    middleware.verify_request(valid_token, "localhost", 500)
    
    # Invalid token
    with pytest.raises(UnauthorizedError, match="token"):
        middleware.verify_request("wrong", "localhost", 500)
        
    # Invalid host
    with pytest.raises(UnauthorizedError, match="Host"):
        middleware.verify_request(valid_token, "attacker.com", 500)
        
    # Payload too large
    with pytest.raises(UnauthorizedError, match="large"):
        middleware.verify_request(valid_token, "localhost", 2 * 1024 * 1024)
