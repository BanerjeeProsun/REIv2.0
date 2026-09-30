"""IMAP/SMTP network I/O for the Email connector.

All mail connections go through here: this module lives under rei.egress, so
the socket guard lets it connect, and every connection is first checked by the
EgressGate (mode + host allowlist). Nothing else in Rei may open mail sockets.
"""
import email
import email.policy
import imaplib
import re
import smtplib
import ssl
from dataclasses import dataclass
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from typing import Any, Iterator
from contextlib import contextmanager

from rei.egress.gate import EgressGate

TIMEOUT_S = 20


class MailError(Exception):
    pass


@dataclass(frozen=True)
class MailAccount:
    address: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int


# Well-known providers, so most people only type address + app password
PRESETS: dict[str, tuple[str, int, str, int]] = {
    "gmail.com": ("imap.gmail.com", 993, "smtp.gmail.com", 465),
    "googlemail.com": ("imap.gmail.com", 993, "smtp.gmail.com", 465),
    "yahoo.com": ("imap.mail.yahoo.com", 993, "smtp.mail.yahoo.com", 465),
    "icloud.com": ("imap.mail.me.com", 993, "smtp.mail.me.com", 587),
    "me.com": ("imap.mail.me.com", 993, "smtp.mail.me.com", 587),
    "zoho.com": ("imap.zoho.com", 993, "smtp.zoho.com", 465),
    "aol.com": ("imap.aol.com", 993, "smtp.aol.com", 465),
    "gmx.com": ("imap.gmx.com", 993, "mail.gmx.com", 465),
    "fastmail.com": ("imap.fastmail.com", 993, "smtp.fastmail.com", 465),
}


def preset_for(address: str) -> tuple[str, int, str, int] | None:
    domain = address.rsplit("@", 1)[-1].lower().strip()
    return PRESETS.get(domain)


def _decode(value: Any) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(str(value))))
    except Exception:
        return str(value)


@contextmanager
def _imap(gate: EgressGate, account: MailAccount, password: str) -> Iterator[imaplib.IMAP4_SSL]:
    gate.check_host(account.imap_host, "email")
    try:
        conn = imaplib.IMAP4_SSL(account.imap_host, account.imap_port,
                                 ssl_context=ssl.create_default_context(), timeout=TIMEOUT_S)
    except (OSError, imaplib.IMAP4.error) as e:
        raise MailError(f"Couldn't reach {account.imap_host}: {e}") from e
    try:
        try:
            conn.login(account.address, password)
        except imaplib.IMAP4.error as e:
            raise MailError("The email server rejected the sign-in. Check the app password.") from e
        yield conn
    finally:
        try:
            conn.logout()
        except Exception as e:  # already disconnected; nothing to clean up
            print(f"[mail] logout: {e}")


def test_login(gate: EgressGate, account: MailAccount, password: str) -> None:
    with _imap(gate, account, password) as conn:
        conn.noop()


def _search(conn: imaplib.IMAP4_SSL, unread_only: bool, sender: str | None, subject: str | None) -> list[bytes]:
    conn.select("INBOX", readonly=True)
    criteria: list[str] = ["UNSEEN"] if unread_only else ["ALL"]
    if sender:
        criteria += ["FROM", _quote(sender)]
    if subject:
        criteria += ["SUBJECT", _quote(subject)]
    status, data = conn.uid("SEARCH", *criteria)
    if status != "OK" or not data or not data[0]:
        return []
    return list(data[0].split())


def _quote(value: str) -> str:
    # IMAP quoted string; drop characters that could break out of it
    return '"' + re.sub(r'["\\\r\n]', " ", value)[:100] + '"'


def list_recent(gate: EgressGate, account: MailAccount, password: str, count: int = 5,
                unread_only: bool = False, sender: str | None = None) -> list[dict[str, str]]:
    with _imap(gate, account, password) as conn:
        uids = _search(conn, unread_only, sender, None)[-count:][::-1]  # newest first
        messages = []
        for uid in uids:
            status, data = conn.uid("FETCH", uid.decode(), "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if status != "OK" or not data or not isinstance(data[0], tuple):
                continue
            msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
            name, addr = parseaddr(_decode(msg.get("From")))
            try:
                date = parsedate_to_datetime(str(msg.get("Date"))).strftime("%a %d %b, %H:%M")
            except Exception:
                date = ""
            messages.append({"uid": uid.decode(), "from": name or addr, "from_address": addr,
                             "subject": _decode(msg.get("Subject")) or "(no subject)", "date": date})
        return messages


def read_message(gate: EgressGate, account: MailAccount, password: str, which: int = 1,
                 sender: str | None = None, subject: str | None = None) -> dict[str, str] | None:
    """The which-th newest message (optionally filtered), body as plain text."""
    with _imap(gate, account, password) as conn:
        uids = _search(conn, False, sender, subject)
        if len(uids) < which:
            return None
        uid = uids[-which]
        status, data = conn.uid("FETCH", uid.decode(), "(BODY.PEEK[])")
        if status != "OK" or not data or not isinstance(data[0], tuple):
            return None
        msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
        body_part = msg.get_body(preferencelist=("plain", "html"))
        body = body_part.get_content() if body_part is not None else ""
        if body_part is not None and body_part.get_content_type() == "text/html":
            body = _html_to_text(body)
        name, addr = parseaddr(_decode(msg.get("From")))
        return {"from": name or addr, "from_address": addr,
                "subject": _decode(msg.get("Subject")) or "(no subject)",
                "body": re.sub(r"\n{3,}", "\n\n", body).strip()[:4000]}


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>", "\n", html)
    text = re.sub(r"<[^>]+>", " ", html)
    import html as html_lib
    return re.sub(r"[ \t]{2,}", " ", html_lib.unescape(text))


def send(gate: EgressGate, account: MailAccount, password: str, to: str, subject: str, body: str) -> None:
    gate.check_host(account.smtp_host, "email")
    msg = EmailMessage()
    msg["From"] = account.address
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    context = ssl.create_default_context()
    try:
        if account.smtp_port == 465:
            with smtplib.SMTP_SSL(account.smtp_host, account.smtp_port, context=context, timeout=TIMEOUT_S) as smtp:
                smtp.login(account.address, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=TIMEOUT_S) as smtp:
                smtp.starttls(context=context)
                smtp.login(account.address, password)
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise MailError("The email server rejected the sign-in. Check the app password.") from e
    except (OSError, smtplib.SMTPException) as e:
        raise MailError(f"Sending failed: {e}") from e
