import base64
import hashlib
import os
import secrets as pysecrets
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlencode, urlparse

from rei.capabilities.spec import CapabilitySpec
from rei.connectors.base import ConnectField, Connector, ConnectorError
from rei.connectors.email import SecretStore
from rei.connectors.music import MusicHub, music_play_spec
from rei.egress import spotify_http as sp
from rei.egress.gate import EgressGate

REDIRECT_PORT = 8765
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/callback"
SCOPES = "user-read-playback-state user-modify-playback-state user-read-private"
REFRESH_ENTRY = "connector.spotify.refresh"  # noqa: S105 - keyring entry name, not a secret


def pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def authorize_url(client_id: str, challenge: str, state: str) -> str:
    return "https://accounts.spotify.com/authorize?" + urlencode({
        "client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT_URI,
        "code_challenge_method": "S256", "code_challenge": challenge, "scope": SCOPES, "state": state,
    })


def wait_for_code(state: str, timeout_s: float = 180.0) -> str:
    """Tiny one-shot HTTP server on 127.0.0.1 that receives the OAuth redirect."""
    result: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            query = parse_qs(urlparse(self.path).query)
            if urlparse(self.path).path == "/callback":
                if query.get("state", [""])[0] != state:
                    result["error"] = "state_mismatch"
                elif "code" in query:
                    result["code"] = query["code"][0]
                else:
                    result["error"] = query.get("error", ["denied"])[0]
            ok = "code" in result
            body = ("<h2>Rei is connected to Spotify.</h2><p>You can close this tab.</p>" if ok
                    else "<h2>Spotify connection didn't complete.</h2><p>You can close this tab.</p>")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args: Any) -> None:
            pass

    try:
        server = HTTPServer(("127.0.0.1", REDIRECT_PORT), Handler)
    except OSError as e:
        raise ConnectorError(f"Port {REDIRECT_PORT} is busy; close other apps using it and retry.") from e
    server.timeout = 1.0
    deadline = time.monotonic() + timeout_s
    try:
        while not result and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    if "code" in result:
        return result["code"]
    if result.get("error"):
        raise ConnectorError(f"Spotify sign-in was not completed ({result['error']}).")
    raise ConnectorError("Timed out waiting for Spotify sign-in.")


class SpotifyConnector(Connector):
    id = "spotify"
    name = "Spotify"
    description = "Play and control Spotify on your devices, without opening the app."
    fields = (ConnectField("client_id", "Spotify app Client ID", "From developer.spotify.com/dashboard"),)
    note = ("One-time setup: create an app at developer.spotify.com/dashboard, add the redirect URI "
            f"{REDIRECT_URI}, tick 'Web API', then paste its Client ID here. Playback needs Spotify Premium.")

    def __init__(self, gate: EgressGate, secrets: SecretStore, hub: MusicHub,
                 open_browser: Callable[[str], Any] = lambda url: os.startfile(url)) -> None:  # noqa: S606
        super().__init__()
        self.gate = gate
        self.secrets = secrets
        self.hub = hub
        self.open_browser = open_browser
        self._access = ""
        self._expires = 0.0
        self._lock = threading.Lock()
        hub.add(self)

    @property
    def available(self) -> bool:
        return self.state.connected

    # --- auth ---

    def connect(self, params: dict[str, str]) -> None:
        client_id = params.get("client_id", "").strip()
        if len(client_id) < 16:
            raise ConnectorError("Paste the Client ID from your Spotify developer app.")
        verifier, challenge = pkce_pair()
        state = pysecrets.token_urlsafe(16)
        # The gate must allow Spotify hosts during the sign-in exchange
        self.state.config = {"client_id": client_id}
        self.state.connected = True
        try:
            self.open_browser(authorize_url(client_id, challenge, state))
            code = wait_for_code(state)
            tokens = sp.token(self.gate, {
                "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI,
                "client_id": client_id, "code_verifier": verifier,
            })
            self._store_tokens(tokens)
            me = sp.api(self.gate, self._access, "GET", "/me") or {}
        except sp.SpotifyHTTPError as e:
            self.state.connected = False
            raise ConnectorError(str(e)) from e
        except ConnectorError:
            self.state.connected = False
            raise
        except Exception as e:
            self.state.connected = False
            raise ConnectorError(f"Couldn't connect to Spotify: {e}") from e
        plan = " (Premium)" if me.get("product") == "premium" else " (Free: playback control needs Premium)"
        detail = f"{me.get('display_name') or me.get('id') or 'Spotify'}{plan}"
        self.state.config = {"client_id": client_id, "detail": detail}
        self.state.detail = detail

    def disconnect(self) -> None:
        self.secrets.delete_secret(REFRESH_ENTRY)
        self._access, self._expires = "", 0.0
        self.state.config = {}

    def _store_tokens(self, tokens: dict[str, Any]) -> None:
        self._access = str(tokens["access_token"])
        self._expires = time.monotonic() + float(tokens.get("expires_in", 3600)) - 60
        if tokens.get("refresh_token"):
            self.secrets.set_secret(REFRESH_ENTRY, str(tokens["refresh_token"]))

    def _token(self) -> str:
        with self._lock:
            if self._access and time.monotonic() < self._expires:
                return self._access
            refresh = self.secrets.get_secret(REFRESH_ENTRY)
            if not refresh:
                raise ConnectorError("Spotify isn't connected. Reconnect it on the Connectors page.")
            try:
                tokens = sp.token(self.gate, {"grant_type": "refresh_token", "refresh_token": refresh,
                                              "client_id": str(self.state.config.get("client_id", ""))})
            except sp.SpotifyHTTPError as e:
                raise ConnectorError(f"Spotify sign-in expired; reconnect it. ({e})") from e
            self._store_tokens(tokens)
            return self._access

    def _call(self, method: str, path: str, **kw: Any) -> Any:
        try:
            return sp.api(self.gate, self._token(), method, path, **kw)
        except sp.SpotifyHTTPError as e:
            if e.reason == "PREMIUM_REQUIRED" or e.status == 403:
                raise ConnectorError("Spotify only allows playback control with Premium.") from e
            if e.reason == "NO_ACTIVE_DEVICE":
                raise ConnectorError("No Spotify device is available. Open Spotify on any device once.") from e
            raise ConnectorError(f"Spotify error: {e}") from e

    def egress_hosts(self) -> set[str]:
        return set(sp.HOSTS)

    def capabilities(self) -> list[tuple[CapabilitySpec, Callable[..., Any]]]:
        return [(music_play_spec, self.hub.play)]

    # --- MusicProvider ---

    def _device(self) -> Optional[str]:
        devices = (self._call("GET", "/me/player/devices") or {}).get("devices", [])
        active = [d for d in devices if d.get("is_active")] or devices
        return str(active[0]["id"]) if active else None

    def _wake_desktop_app(self) -> None:
        """Start Spotify minimised in the background so it becomes a device."""
        exe = Path(os.environ.get("APPDATA", "")) / "Spotify" / "Spotify.exe"
        try:
            if exe.exists():
                # SW_SHOWMINNOACTIVE: start minimised without stealing focus
                os.startfile(str(exe), arguments="--minimized", show_cmd=7)  # noqa: S606
            else:
                os.startfile("spotify:", show_cmd=7)  # noqa: S606, S607
        except OSError as e:
            print(f"[spotify] couldn't start the app: {e}")

    def play(self, query: str) -> str:
        found = self._call("GET", "/search", params={"q": query, "type": "track", "limit": 1}) or {}
        items = (found.get("tracks") or {}).get("items") or []
        if not items:
            raise ConnectorError(f"Nothing found on Spotify for {query!r}.")
        track = items[0]
        device = self._device()
        if device is None:
            self._wake_desktop_app()
            for _ in range(20):
                time.sleep(0.5)
                device = self._device()
                if device:
                    break
        if device is None:
            raise ConnectorError("No Spotify device is available. Open Spotify on any device once.")
        self._call("PUT", "/me/player/play", params={"device_id": device}, body={"uris": [track["uri"]]})
        artists = ", ".join(a.get("name", "") for a in track.get("artists", [])[:2])
        return f"{track.get('name', query)} by {artists}" if artists else str(track.get("name", query))

    def control(self, action: str) -> bool:
        paths = {"pause": ("PUT", "/me/player/pause"), "play": ("PUT", "/me/player/play"),
                 "stop": ("PUT", "/me/player/pause"), "next": ("POST", "/me/player/next"),
                 "prev": ("POST", "/me/player/previous")}
        if action not in paths:
            return False
        method, path = paths[action]
        self._call(method, path)
        return True
