from pydantic import BaseModel, ConfigDict
from typing import Optional


class IPCMessage(BaseModel):
    model_config = ConfigDict(strict=True)
    version: str = "1.0"
    message_id: str
    session_id: str


class SubmitTurnRequest(IPCMessage):
    audio_data: Optional[bytes] = None
    text_data: Optional[str] = None


class ConfirmRequest(IPCMessage):
    turn_id: str
    prompt_text: str


class ConfirmResponse(IPCMessage):
    turn_id: str
    approved: bool


class CancelRequest(IPCMessage):
    turn_id: str
