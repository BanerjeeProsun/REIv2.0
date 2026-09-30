from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from rei.capabilities.spec import CapabilitySpec


class ConnectorError(Exception):
    """User-facing problem connecting or using a connector."""


@dataclass(frozen=True)
class ConnectField:
    """One input on the connector's connect form."""
    key: str
    label: str
    placeholder: str = ""
    secret: bool = False
    optional: bool = False


@dataclass
class ConnectorState:
    connected: bool = False
    detail: str = ""               # e.g. the connected account address
    error: str = ""
    config: dict[str, Any] = field(default_factory=dict)  # non-secret, persisted


class Connector(ABC):
    """An external service Rei can use once the user connects it (like Claude
    connectors). Capabilities are only offered to the planner while connected,
    and network access is limited to egress_hosts()."""

    id: str = ""
    name: str = ""
    description: str = ""
    fields: tuple[ConnectField, ...] = ()
    note: str = ""                 # setup hint shown on the connect form

    def __init__(self) -> None:
        self.state = ConnectorState()

    @abstractmethod
    def connect(self, params: dict[str, str]) -> None:
        """Validate and save credentials. Runs off the UI thread (may do network)."""

    def restore(self, config: dict[str, Any]) -> None:
        """Re-attach saved (non-secret) config at startup without network calls."""
        self.state = ConnectorState(connected=True, config=dict(config), detail=str(config.get("detail", "")))

    @abstractmethod
    def disconnect(self) -> None:
        """Forget credentials."""

    @abstractmethod
    def capabilities(self) -> list[tuple[CapabilitySpec, Callable[..., Any]]]:
        """(spec, handler) pairs registered while connected."""

    def egress_hosts(self) -> set[str]:
        return set()
