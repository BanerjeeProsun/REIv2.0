import json
from pathlib import Path
from typing import Any, Callable

from rei.capabilities.registry import CapabilityRegistry
from rei.connectors.base import Connector, ConnectorError


class ConnectorManager:
    """Owns the connectors: persists their non-secret config, registers their
    capabilities only while connected, and reports which hosts they may reach."""

    def __init__(self, registry: CapabilityRegistry, config_path: Path, connectors: list[Connector]) -> None:
        self.registry = registry
        self.config_path = config_path
        self.connectors: dict[str, Connector] = {c.id: c for c in connectors}
        self._listeners: list[Callable[[], None]] = []

    # --- lifecycle ---

    def load(self) -> None:
        saved = self._read()
        for cid, config in saved.items():
            connector = self.connectors.get(cid)
            if connector is None:
                continue
            try:
                connector.restore(config)
                self._register(connector)
            except Exception as e:
                connector.state.connected = False
                connector.state.error = str(e)

    def connect(self, cid: str, params: dict[str, str]) -> None:
        connector = self._get(cid)
        connector.state.error = ""
        try:
            connector.connect(params)
        except ConnectorError as e:
            connector.state.connected = False
            connector.state.error = str(e)
            self._changed()
            raise
        connector.state.connected = True
        self._register(connector)
        saved = self._read()
        saved[cid] = connector.state.config
        self._write(saved)
        self._changed()

    def disconnect(self, cid: str) -> None:
        connector = self._get(cid)
        for spec, _ in connector.capabilities():
            self.registry.unregister(spec.id)
        connector.disconnect()
        connector.state.connected = False
        connector.state.detail = ""
        saved = self._read()
        saved.pop(cid, None)
        self._write(saved)
        self._changed()

    # --- queries ---

    def hosts(self) -> set[str]:
        out: set[str] = set()
        for c in self.connectors.values():
            if c.state.connected:
                out |= c.egress_hosts()
        return out

    def get(self, cid: str) -> Connector | None:
        return self.connectors.get(cid)

    def on_change(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    # --- internals ---

    def _get(self, cid: str) -> Connector:
        if cid not in self.connectors:
            raise ConnectorError(f"Unknown connector {cid}")
        return self.connectors[cid]

    def _register(self, connector: Connector) -> None:
        for spec, handler in connector.capabilities():
            self.registry.register(spec, handler)

    def _changed(self) -> None:
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                print(f"[Connectors] listener failed: {e}")

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _write(self, data: dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
