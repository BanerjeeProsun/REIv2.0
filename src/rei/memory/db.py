import sqlite3
import json
from pathlib import Path
from typing import Any
import win32crypt # type: ignore

class MemoryStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    encrypted_value BLOB,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
    def set(self, key: str, value: Any) -> None:
        json_val = json.dumps(value)
        # Encrypt with Windows DPAPI (tied to current user account)
        encrypted = win32crypt.CryptProtectData(json_val.encode('utf-8'), 'ReiMemory')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT OR REPLACE INTO memory (key, encrypted_value) VALUES (?, ?)', 
                         (key, encrypted))
                         
    def get(self, key: str) -> Any | None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT encrypted_value FROM memory WHERE key = ?', (key,))
            row = cur.fetchone()
            if row:
                try:
                    _, decrypted = win32crypt.CryptUnprotectData(row[0])
                    return json.loads(decrypted.decode('utf-8'))
                except Exception:
                    return None
            return None
            
    def get_all(self) -> dict[str, Any]:
        """Returns all memory as a dict to inject into LLM context."""
        results = {}
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT key, encrypted_value FROM memory')
            for key, encrypted_value in cur.fetchall():
                try:
                    _, decrypted = win32crypt.CryptUnprotectData(encrypted_value)
                    results[key] = json.loads(decrypted.decode('utf-8'))
                except Exception:
                    continue
        return results
