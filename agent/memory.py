"""Conversation memory backed by Amazon Bedrock AgentCore Memory.

Each runtimeSessionId maps to one AgentCore Memory session; turns are stored
as events and survive cold starts and instance changes — unlike a process-local
store. The memory resource is short-term only (no long-term extraction
strategies configured), so this just persists and replays raw turns.

Memory is best-effort: any failure here is swallowed so a memory outage
degrades to a stateless answer rather than failing the request.
"""

from __future__ import annotations

import config

from bedrock_agentcore.memory import MemoryClient

_client = MemoryClient(region_name=config.REGION)

# AgentCore Memory partitions events by actor. Short-term memory is keyed by
# (actor_id, session_id); a single actor is enough since session_id is unique.
ACTOR_ID = "permitpdx-user"
# How many recent turns to replay into the prompt.
RECENT_TURNS = 6


def _text_of(msg: dict) -> str:
    """Extract plain text from an AgentCore message, whatever its shape."""
    content = msg.get("content")
    if isinstance(content, dict):
        return (content.get("text") or "").strip()
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return " ".join(
            c.get("text", "") for c in content if isinstance(c, dict)
        ).strip()
    return ""


def get_history(session_id: str | None) -> list[dict]:
    """Return recent turns as [{role, text}, ...] in chronological order."""
    if not (session_id and config.MEMORY_ID):
        return []
    try:
        turns = _client.get_last_k_turns(
            memory_id=config.MEMORY_ID,
            actor_id=ACTOR_ID,
            session_id=session_id,
            k=RECENT_TURNS,
        )
    except Exception:  # noqa: BLE001 — memory is best-effort, never fatal
        return []
    history: list[dict] = []
    # get_last_k_turns returns newest-first; replay oldest-first.
    for turn in reversed(turns):
        for msg in turn:
            role = (msg.get("role") or "").lower()
            text = _text_of(msg)
            if role in ("user", "assistant") and text:
                history.append({"role": role, "text": text})
    return history


def append_turn(session_id: str | None, query: str, answer: str) -> None:
    """Persist one user/assistant exchange to AgentCore Memory."""
    if not (session_id and config.MEMORY_ID and answer):
        return
    try:
        _client.create_event(
            memory_id=config.MEMORY_ID,
            actor_id=ACTOR_ID,
            session_id=session_id,
            messages=[(query, "USER"), (answer, "ASSISTANT")],
        )
    except Exception:  # noqa: BLE001 — memory is best-effort, never fatal
        pass


def to_strands_messages(history: list[dict]) -> list[dict]:
    """Convert stored history to the Strands Messages format."""
    return [
        {"role": m["role"], "content": [{"text": m["text"]}]}
        for m in history
    ]
