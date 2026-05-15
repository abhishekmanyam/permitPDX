"""LiveAvatar integration — mints FULL-mode streaming sessions for the
in-browser kiosk avatar. The avatar's Custom LLM points back at this
backend's /v1/chat/completions endpoint."""

from __future__ import annotations

import json
import os
import ssl
import urllib.request

import certifi

API_BASE = os.environ.get("LIVEAVATAR_API_BASE", "https://api.liveavatar.com/v1")
API_KEY = os.environ.get("LIVEAVATAR_API_KEY", "")
CONTEXT_ID = os.environ.get("LIVEAVATAR_CONTEXT_ID", "")
LLM_CONFIG_ID = os.environ.get("LIVEAVATAR_LLM_CONFIG_ID", "")
SANDBOX_AVATAR = os.environ.get("LIVEAVATAR_SANDBOX_AVATAR", "")
DEFAULT_VOICE = os.environ.get("LIVEAVATAR_VOICE_ID", "c2527536-6d1f-4412-a643-53a3497dada9")

_SSL = ssl.create_default_context(cafile=certifi.where())


def _request(method: str, path: str, body: dict | None = None,
             token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-API-KEY"] = API_KEY
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API_BASE}{path}", data=data,
                                 headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15, context=_SSL) as r:  # noqa: S310
        raw = r.read().decode()
    return json.loads(raw) if raw else {}


def create_session_token(sandbox: bool = True) -> dict:
    """Create a FULL-mode LiveAvatar session whose Custom LLM is this backend.

    Returns {session_token, session_id} for the browser SDK, or {error}.
    """
    if not API_KEY:
        return {"error": "LIVEAVATAR_API_KEY not configured"}
    body = {
        "mode": "FULL",
        "avatar_id": SANDBOX_AVATAR,
        "llm_configuration_id": LLM_CONFIG_ID,
        "avatar_persona": {
            "voice_id": DEFAULT_VOICE,
            "context_id": CONTEXT_ID,
            "language": "en",
        },
    }
    if sandbox:
        body["is_sandbox"] = True
    try:
        result = _request("POST", "/sessions/token", body)
        data = result.get("data", result)
        return {
            "session_token": data.get("session_token"),
            "session_id": data.get("session_id"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def stop_session(token: str) -> dict:
    """End a LiveAvatar session."""
    try:
        _request("DELETE", "/sessions", token=token)
        return {"status": "stopped"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
