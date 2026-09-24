import json
import hashlib
from typing import Any
from pathlib import Path
from datetime import datetime

class AuditLogWriter:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.prev_hash = self._get_last_hash()
        
    def _get_last_hash(self) -> str:
        if not self.log_path.exists():
            return hashlib.sha256(b"genesis").hexdigest()
        
        # In a real implementation we would read the last line efficiently
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return hashlib.sha256(b"genesis").hexdigest()
            last_record = json.loads(lines[-1])
            return self._hash_record(last_record)
            
    def _hash_record(self, record: dict[str, Any]) -> str:
        canon = json.dumps(record, sort_keys=True)
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def write_event(self, event_type: str, data: dict[str, Any]) -> None:
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "prev_hash": self.prev_hash,
            "event": event_type,
            **data
        }
        
        # Redact secrets before writing
        self._redact_in_place(record)
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            
        self.prev_hash = self._hash_record(record)
        
    def _redact_in_place(self, data: Any) -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                if k in ("token", "key", "password", "authorization"):
                    data[k] = "<REDACTED>"
                else:
                    self._redact_in_place(v)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str) and "ghp_" in item:
                    data[i] = "<REDACTED_GH_TOKEN>"
                else:
                    self._redact_in_place(item)
