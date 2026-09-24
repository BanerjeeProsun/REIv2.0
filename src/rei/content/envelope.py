from dataclasses import dataclass
from enum import Enum

class TaintType(Enum):
    WEB = "WEB"
    EMAIL = "EMAIL"
    CLIPBOARD = "CLIPBOARD"
    DOCUMENT = "DOCUMENT"

@dataclass
class ContentEnvelope:
    source_id: str
    taint: TaintType
    raw_content: str
    sanitized_content: str
    
    def format_for_model(self) -> str:
        # Enclose the content in a strict structural envelope so prompt injection is contained
        header = f'<UNTRUSTED_CONTENT source="{self.source_id}" type="{self.taint.value}">'
        return f"\n{header}\n{self.sanitized_content}\n</UNTRUSTED_CONTENT>\n"
