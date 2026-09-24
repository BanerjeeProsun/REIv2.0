import json
import win32pipe # type: ignore
from typing import Any

class PipeClient:
    def __init__(self, pipe_name: str, auth_token: str) -> None:
        self.pipe_name = rf"\\.\pipe\{pipe_name}"
        self.auth_token = auth_token
        
    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        msg = {
            "token": self.auth_token,
            "payload": payload
        }
        raw_msg = json.dumps(msg).encode("utf-8")
        
        # Connect to pipe and send
        result, data = win32pipe.CallNamedPipe(
            self.pipe_name,
            raw_msg,
            65536,
            win32pipe.NMPWAIT_WAIT_FOREVER
        )
        res: dict[str, Any] = json.loads(data.decode("utf-8"))
        return res
