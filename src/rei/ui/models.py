from PySide6.QtCore import QAbstractListModel, Qt, QByteArray, Slot, Signal, QModelIndex
from typing import Any, List, Dict
import time

class MemoryModel(QAbstractListModel):
    IdRole = Qt.ItemDataRole.UserRole + 1
    ContentRole = Qt.ItemDataRole.UserRole + 2
    KindRole = Qt.ItemDataRole.UserRole + 3
    DataClassRole = Qt.ItemDataRole.UserRole + 4
    CreatedAtRole = Qt.ItemDataRole.UserRole + 5

    def __init__(self, store: Any, parent=None):
        super().__init__(parent)
        self.store = store
        self._memories: List[Dict[str, Any]] = []
        self.refresh()

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"id"),
            self.ContentRole: QByteArray(b"content"),
            self.KindRole: QByteArray(b"kind"),
            self.DataClassRole: QByteArray(b"dataClass"),
            self.CreatedAtRole: QByteArray(b"createdAt")
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._memories)

    def data(self, index, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._memories)):
            return None
        mem = self._memories[index.row()]
        if role == self.IdRole:
            return mem["id"]
        elif role == self.ContentRole:
            return self._readable(mem["content"])
        elif role == self.KindRole:
            return mem["kind"]
        elif role == self.DataClassRole:
            return mem["data_class"]
        elif role == self.CreatedAtRole:
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mem["created_at"]))
        return None

    @staticmethod
    def _readable(content: Any) -> str:
        """Show {"name": "Ada", "purpose": "research"} as "Name: Ada · Purpose: research"."""
        if isinstance(content, dict):
            return "  ·  ".join(f"{str(k).replace('_', ' ').capitalize()}: {v}" for k, v in content.items())
        if isinstance(content, list):
            return ", ".join(str(v) for v in content)
        return str(content)

    @Slot()
    def refresh(self):
        self.beginResetModel()
        self._memories = self.store.list_all() if self.store else []
        self.endResetModel()

    @Slot(str)
    def delete_memory(self, memory_id: str):
        # We don't have delete in MemoryStore yet, so we just log "Coming Soon" behavior.
        # Actually, let's not fake it if not implemented.
        pass

class CapabilityModel(QAbstractListModel):
    IdRole = Qt.ItemDataRole.UserRole + 1
    SummaryRole = Qt.ItemDataRole.UserRole + 2
    TierRole = Qt.ItemDataRole.UserRole + 3
    NetworkRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, registry: Any, parent=None):
        super().__init__(parent)
        self.registry = registry
        self._caps = []
        self.refresh()

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"id"),
            self.SummaryRole: QByteArray(b"summary"),
            self.TierRole: QByteArray(b"tier"),
            self.NetworkRole: QByteArray(b"network")
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._caps)

    def data(self, index, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._caps)):
            return None
        cap = self._caps[index.row()]
        if role == self.IdRole:
            return cap.id
        elif role == self.SummaryRole:
            return cap.summary
        elif role == self.TierRole:
            return cap.tier.value
        elif role == self.NetworkRole:
            return cap.network
        return None

    @Slot()
    def refresh(self):
        self.beginResetModel()
        self._caps = self.registry.get_all_specs() if self.registry else []
        self.endResetModel()
