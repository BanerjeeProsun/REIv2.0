from typing import Any, Callable, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field

from rei.capabilities.spec import CapabilitySpec, DataClass, RateLimit, RiskTier
from rei.connectors.base import ConnectField, Connector, ConnectorError
from rei.content.sanitiser import ContentSanitiser
from rei.egress import mail
from rei.egress.gate import EgressGate
from rei.egress.socket_guard import EgressBlockedError
from rei.policy.schemas import PrivacyMode

CONNECTOR_MODES = frozenset([PrivacyMode.LOCAL_PLUS_WEB, PrivacyMode.CLOUD_ASSISTED])
PASSWORD_ENTRY = "connector.email.password"  # noqa: S105 - keyring entry name, not a secret


class SecretStore(Protocol):
    def get_secret(self, key: str) -> str | None: ...
    def set_secret(self, key: str, value: str) -> None: ...
    def delete_secret(self, key: str) -> None: ...


class ListEmailArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    count: int = Field(5, ge=1, le=20)
    unread_only: bool = False
    sender: Optional[str] = Field(None, max_length=100)


class ReadEmailArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    which: int = Field(1, ge=1, le=50)
    sender: Optional[str] = Field(None, max_length=100)
    subject_contains: Optional[str] = Field(None, max_length=100)


class SendEmailArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    to: str = Field(..., pattern=r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$", max_length=254)
    subject: str = Field(..., max_length=200)
    body: str = Field(..., max_length=5000)


email_list_spec = CapabilitySpec(
    id="email.list_recent",
    version=1,
    summary="Check the email inbox: list the newest emails (sender, subject), optionally unread only or from someone",
    tier=RiskTier.R1,
    args_model=ListEmailArgs,
    reads=frozenset([DataClass.C2]),
    returns=DataClass.C2,
    network=True,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="List recent emails",
    timeout_s=30.0,
    rate_limit=RateLimit(limit=30, period_s=60),
    modes=CONNECTOR_MODES,
)

email_read_spec = CapabilitySpec(
    id="email.read",
    version=1,
    summary="Open and read the full text of one email (the newest, or the n-th newest, optionally from a sender)",
    tier=RiskTier.R1,
    args_model=ReadEmailArgs,
    reads=frozenset([DataClass.C2]),
    returns=DataClass.C2,
    network=True,
    reversible=True,
    allow_when_tainted=True,
    confirm_template="Read an email",
    timeout_s=30.0,
    rate_limit=RateLimit(limit=30, period_s=60),
    modes=CONNECTOR_MODES,
)

email_send_spec = CapabilitySpec(
    id="email.send",
    version=1,
    summary="Send (write, compose, reply with) an email to someone",
    tier=RiskTier.R3,
    args_model=SendEmailArgs,
    reads=frozenset(),
    returns=DataClass.C0,
    network=True,
    reversible=False,
    allow_when_tainted=True,   # still needs a spoken "confirm" after a full read-back
    confirm_template="Send an email to {to} with the subject \"{subject}\"",
    timeout_s=30.0,
    rate_limit=RateLimit(limit=5, period_s=3600),
    modes=CONNECTOR_MODES,
)


class EmailConnector(Connector):
    id = "email"
    name = "Email"
    description = "Read and send email from any IMAP/SMTP account."
    fields = (
        ConnectField("address", "Email address", "you@gmail.com"),
        ConnectField("password", "App password", "16-character app password", secret=True),
        ConnectField("imap_host", "IMAP server", "Auto for Gmail, Yahoo, iCloud, Zoho...", optional=True),
        ConnectField("smtp_host", "SMTP server", "Auto for Gmail, Yahoo, iCloud, Zoho...", optional=True),
    )
    note = ("Use an app password, not your normal password. Gmail: myaccount.google.com/apppasswords "
            "(needs 2-step verification). Your password is stored in Windows Credential Manager.")

    def __init__(self, gate: EgressGate, secrets: SecretStore) -> None:
        super().__init__()
        self.gate = gate
        self.secrets = secrets
        self.sanitiser = ContentSanitiser()

    # --- account ---

    def _account(self, config: dict[str, Any]) -> mail.MailAccount:
        return mail.MailAccount(
            address=str(config["address"]),
            imap_host=str(config["imap_host"]), imap_port=int(config["imap_port"]),
            smtp_host=str(config["smtp_host"]), smtp_port=int(config["smtp_port"]),
        )

    def _password(self) -> str:
        password = self.secrets.get_secret(PASSWORD_ENTRY)
        if not password:
            raise ConnectorError("Email isn't connected. Reconnect it on the Connectors page.")
        return password

    def connect(self, params: dict[str, str]) -> None:
        address = params.get("address", "").strip()
        password = params.get("password", "").replace(" ", "").strip()
        if "@" not in address or not password:
            raise ConnectorError("Enter your email address and an app password.")
        preset = mail.preset_for(address)
        imap_host = params.get("imap_host", "").strip() or (preset[0] if preset else "")
        smtp_host = params.get("smtp_host", "").strip() or (preset[2] if preset else "")
        if not imap_host or not smtp_host:
            raise ConnectorError("I don't know this provider's servers. Enter the IMAP and SMTP server.")
        config = {
            "address": address,
            "imap_host": imap_host, "imap_port": preset[1] if preset and imap_host == preset[0] else 993,
            "smtp_host": smtp_host, "smtp_port": preset[3] if preset and smtp_host == preset[2] else 465,
            "detail": address,
        }
        # The gate must allow these hosts for the test login
        self.state.config = config
        self.state.connected = True
        try:
            mail.test_login(self.gate, self._account(config), password)
        except mail.MailError as e:
            self.state.connected = False
            raise ConnectorError(str(e)) from e
        except EgressBlockedError as e:
            self.state.connected = False
            raise ConnectorError('Switch Privacy to "Local + Connectors" (or Cloud Assisted) first.') from e
        except Exception as e:
            self.state.connected = False
            raise ConnectorError(f"Couldn't connect: {e}") from e
        self.secrets.set_secret(PASSWORD_ENTRY, password)
        self.state.detail = address

    def disconnect(self) -> None:
        self.secrets.delete_secret(PASSWORD_ENTRY)
        self.state.config = {}

    def egress_hosts(self) -> set[str]:
        c = self.state.config
        return {h for h in (c.get("imap_host"), c.get("smtp_host")) if h}

    # --- capabilities ---

    def capabilities(self) -> list[tuple[CapabilitySpec, Callable[..., Any]]]:
        return [
            (email_list_spec, self.list_recent),
            (email_read_spec, self.read),
            (email_send_spec, self.send),
        ]

    def _clean(self, text: str) -> str:
        return self.sanitiser.sanitize(text)

    def list_recent(self, args: ListEmailArgs) -> dict[str, Any]:
        try:
            messages = mail.list_recent(self.gate, self._account(self.state.config), self._password(),
                                        args.count, args.unread_only, args.sender)
        except mail.MailError as e:
            raise ConnectorError(str(e)) from e
        if not messages:
            content = "No matching emails."
        else:
            content = "\n".join(
                f"{i}. From {self._clean(m['from'])} ({m['date']}): {self._clean(m['subject'])}"
                for i, m in enumerate(messages, 1)
            )
        return {"status": "success", "taint": "EMAIL", "content": content, "count": len(messages),
                "spoken": self._speak_list(messages, args)}

    def _speak_list(self, messages: list[dict[str, str]], args: ListEmailArgs) -> str:
        """Deterministic spoken summary: reliable even on the small local model,
        and email text never goes through a model that could act on it."""
        if not messages:
            who = f" from {args.sender}" if args.sender else ""
            return f"You don't have any {'unread ' if args.unread_only else ''}emails{who}."
        items = [f"{self._clean(m['from'])} about {self._clean(m['subject'])}" for m in messages]
        joined = items[0] if len(items) == 1 else ", ".join(items[:-1]) + ", and " + items[-1]
        kind = "unread " if args.unread_only else "recent "
        noun = "email" if len(items) == 1 else "emails"
        return f"You have {len(items)} {kind}{noun}: {joined}."

    def read(self, args: ReadEmailArgs) -> dict[str, Any]:
        try:
            message = mail.read_message(self.gate, self._account(self.state.config), self._password(),
                                        args.which, args.sender, args.subject_contains)
        except mail.MailError as e:
            raise ConnectorError(str(e)) from e
        if message is None:
            return {"status": "success", "taint": "EMAIL", "content": "No matching email found.",
                    "spoken": "I couldn't find that email."}
        content = (f"From: {self._clean(message['from'])}\nSubject: {self._clean(message['subject'])}\n\n"
                   f"{self._clean(message['body'])}")
        body = " ".join(self._clean(message["body"]).split())
        if len(body) > 400:
            body = body[:400].rsplit(" ", 1)[0] + "..."
        spoken = (f"Email from {self._clean(message['from'])}, subject {self._clean(message['subject'])}. "
                  + (f"It says: {body}" if body else "It's empty."))
        return {"status": "success", "taint": "EMAIL", "content": content, "spoken": spoken}

    def send(self, args: SendEmailArgs) -> dict[str, Any]:
        try:
            mail.send(self.gate, self._account(self.state.config), self._password(), args.to, args.subject, args.body)
        except mail.MailError as e:
            raise ConnectorError(str(e)) from e
        return {"status": "success", "to": args.to}
