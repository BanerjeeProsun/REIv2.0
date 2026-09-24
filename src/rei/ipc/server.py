import asyncio
import json
from typing import Any, Callable, Awaitable
import win32file # type: ignore
import win32pipe # type: ignore
import win32security # type: ignore
import ntsecuritycon # type: ignore

class IPCAuthError(Exception):
    pass

class PipeServer:
    def __init__(self, pipe_name: str, auth_token: str) -> None:
        self.pipe_name = rf"\\.\pipe\{pipe_name}"
        self.auth_token = auth_token
        self.handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None

    def _create_security_attributes(self) -> win32security.SECURITY_ATTRIBUTES:
        # P1.3: User-only DACL
        sd = win32security.SECURITY_DESCRIPTOR()
        dacl = win32security.ACL()
        
        # Current user SID
        import win32api # type: ignore
        user_name = win32api.GetUserName()
        user_sid, _, _ = win32security.LookupAccountName(None, user_name)
        
        dacl.AddAccessAllowedAce(
            win32security.ACL_REVISION, 
            ntsecuritycon.GENERIC_READ | ntsecuritycon.GENERIC_WRITE, 
            user_sid
        )
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.SECURITY_DESCRIPTOR = sd
        return sa

    async def start(self) -> None:
        sa = self._create_security_attributes()
        # Create named pipe
        self.pipe = win32pipe.CreateNamedPipe(
            self.pipe_name,
            win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_REJECT_REMOTE_CLIENTS,
            win32pipe.PIPE_UNLIMITED_INSTANCES,
            65536, 65536, 0, sa
        )
        
        while True:
            # We would typically use asyncio to wait on the overlapped event
            # For simplicity in this architectural outline, we simulate connection handling
            await asyncio.sleep(0.1)

    async def process_message(self, raw_msg: bytes) -> bytes:
        msg = json.loads(raw_msg.decode("utf-8"))
        
        # P1.3: Per-launch token authentication
        if msg.get("token") != self.auth_token:
            raise IPCAuthError("Invalid token")
            
        if self.handler:
            resp = await self.handler(msg["payload"])
            return json.dumps(resp).encode("utf-8")
        return b"{}"
