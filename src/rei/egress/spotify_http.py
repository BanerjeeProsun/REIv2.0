"""Spotify Web API HTTP calls (OAuth token exchange + player API).

Under rei.egress: every request is checked by the EgressGate and the socket
guard lets these connections through. Only accounts.spotify.com and
api.spotify.com are ever contacted.
"""
from typing import Any

import httpx

from rei.egress.gate import EgressGate

AUTH_HOST = "accounts.spotify.com"
API_HOST = "api.spotify.com"
HOSTS = {AUTH_HOST, API_HOST}


class SpotifyHTTPError(Exception):
    def __init__(self, status: int, message: str, reason: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason


def token(gate: EgressGate, form: dict[str, str]) -> dict[str, Any]:
    gate.check_host(AUTH_HOST, "spotify")
    try:
        resp = httpx.post(f"https://{AUTH_HOST}/api/token", data=form, timeout=15)
    except httpx.HTTPError as e:
        raise SpotifyHTTPError(0, f"Couldn't reach Spotify: {e}") from e
    if resp.status_code != 200:
        raise SpotifyHTTPError(resp.status_code, f"Spotify sign-in failed ({resp.status_code}): {resp.text[:200]}")
    data: dict[str, Any] = resp.json()
    return data


def api(gate: EgressGate, access_token: str, method: str, path: str,
        params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> Any:
    gate.check_host(API_HOST, "spotify")
    try:
        resp = httpx.request(method, f"https://{API_HOST}/v1{path}", params=params, json=body,
                             headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    except httpx.HTTPError as e:
        raise SpotifyHTTPError(0, f"Couldn't reach Spotify: {e}") from e
    if resp.status_code in (200, 201) and resp.content:
        return resp.json()
    if resp.status_code in (200, 201, 202, 204):
        return None
    reason = ""
    try:
        err = resp.json().get("error", {})
        reason = str(err.get("reason", "")) if isinstance(err, dict) else ""
        message = str(err.get("message", resp.text)) if isinstance(err, dict) else resp.text
    except ValueError:
        message = resp.text
    raise SpotifyHTTPError(resp.status_code, message[:200], reason)
