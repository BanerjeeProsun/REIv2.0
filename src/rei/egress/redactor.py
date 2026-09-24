import re
from typing import Any

# Simplified v1 regexes for the redactor
SECRET_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "<REDACTED_GH_TOKEN>"),
    (r"sk-[a-zA-Z0-9]{48}", "<REDACTED_OPENAI_KEY>"),
    (r"-----BEGIN [\w\s]+ PRIVATE KEY-----[\s\S]+?-----END [\w\s]+ PRIVATE KEY-----", "<REDACTED_PRIVATE_KEY>"),
    (r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", "<REDACTED_JWT>")
]

PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "<REDACTED_EMAIL>"),
    (r"\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\b", "<REDACTED_PHONE>"),
    (r"\b(?:\d[ -]*?){13,16}\b", "<REDACTED_CARD>") # simplified card
]

class Redactor:
    def __init__(self, mask_pii: bool = True) -> None:
        self.mask_pii = mask_pii

    def redact_string(self, text: str) -> tuple[str, bool]:
        """Returns the redacted string and a boolean indicating if a C3 secret was found."""
        found_secret = False
        
        for pattern, replacement in SECRET_PATTERNS:
            if re.search(pattern, text):
                found_secret = True
                text = re.sub(pattern, replacement, text)
                
        if self.mask_pii:
            for pattern, replacement in PII_PATTERNS:
                text = re.sub(pattern, replacement, text)
                
        return text, found_secret

    def redact_payload(self, payload: Any) -> tuple[Any, bool]:
        if isinstance(payload, str):
            return self.redact_string(payload)
        elif isinstance(payload, dict):
            new_dict = {}
            found_any_secret = False
            for k, v in payload.items():
                new_v, found = self.redact_payload(v)
                new_dict[k] = new_v
                if found:
                    found_any_secret = True
            return new_dict, found_any_secret
        elif isinstance(payload, list):
            new_list = []
            found_any_secret = False
            for v in payload:
                new_v, found = self.redact_payload(v)
                new_list.append(new_v)
                if found:
                    found_any_secret = True
            return new_list, found_any_secret
        else:
            return payload, False
