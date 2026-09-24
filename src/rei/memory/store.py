import sqlite3
import json
from typing import Any, Optional
import win32crypt # type: ignore
from rei.policy.context import PolicyContext
from rei.capabilities.spec import DataClass

class MemoryWriteBlockedError(Exception):
    pass

class MemoryStore:
    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    id TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    kind TEXT NOT NULL,
                    data_class TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    source_turn TEXT NOT NULL,
                    tainted INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER,
                    deleted_at INTEGER
                )
            ''')

    def _encrypt(self, plaintext: str) -> bytes:
        # DPAPI encryption scoped to current user
        return win32crypt.CryptProtectData(plaintext.encode("utf-8"), "ReiMemory", None, None, None, 0) # type: ignore

    def _decrypt(self, ciphertext: bytes) -> str:
        # DPAPI decryption
        desc, data = win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)
        return str(data.decode("utf-8"))

    def write(self, memory_id: str, content: Any, kind: str, data_class: DataClass, 
              created_at: int, ctx: PolicyContext, expires_at: Optional[int] = None) -> None:
        # MEM-01: No memory writes from tainted contexts
        if ctx.taint:
            raise MemoryWriteBlockedError("Cannot write to memory during a tainted turn")
            
        encrypted_content = self._encrypt(json.dumps(content))
        
        with self.conn:
            self.conn.execute('''
                INSERT OR REPLACE INTO memory 
                (id, content, kind, data_class, origin, source_turn, tainted, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id,
                encrypted_content,
                kind,
                data_class.value,
                ctx.origin.value,
                ctx.turn_id,
                1 if ctx.taint else 0,
                created_at,
                expires_at
            ))

    def read(self, memory_id: str) -> Optional[Any]:
        cursor = self.conn.execute('SELECT content FROM memory WHERE id = ? AND deleted_at IS NULL', (memory_id,))
        row = cursor.fetchone()
        if row:
            decrypted = self._decrypt(row[0])
            return json.loads(decrypted)
        return None
