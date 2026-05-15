"""HeyGen LiveAvatar integration — mints streaming session tokens for the
in-browser kiosk avatar. The avatar's Custom LLM points back at this
backend's /v1/chat/completions endpoint."""

from __future__ import annotations

import json
import os
import ssl
import urllib.request

import certifi

API_KEY = os.environ.get("LIVEAVATAR_API_KEY", "")
CONTEXT_ID = os.environ.get("LIVEAVATAR_CONTEXT_ID", "")
LLM_CONFIG_ID = os.environ.get("LIVEAVATAR_LLM_CONFIG_ID", "")
AVATAR_ID = os.environ.get("LIVEAVATAR_SANDBOX_AVATAR", "")

_BASE = os.environ.get("LIVEAVATAR_API_BASE", "https://api.heygen.com")
_SSL = ssl.create_default_context(cafile=certifi.where())


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{_BASE}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15, context=_SSL) as r:  # noqa: S310
        return json.loads(r.read().decode())


def create_session_token() -> dict:
    """Create a HeyGen streaming token for the frontend SDK.

    Returns the token plus the avatar / context / LLM-config ids the
    browser SDK needs to start the WebRTC session.
    """
    if not API_KEY:
        return {"error": "LIVEAVATAR_API_KEY not configured"}
    data = _post("/v1/streaming.create_token", {}).get("data", {})
    return {
        "token": data.get("token", ""),
        "avatar_id": AVATAR_ID,
        "context_id": CONTEXT_ID,
        "llm_config_id": LLM_CONFIG_ID,
    }
