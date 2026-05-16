"""Portland Permit Assistant — AgentCore Runtime entrypoint.

Pipeline: classify -> retrieve (multi-corpus KB) -> risk gate -> answer agent.
Streams a `meta` event (classification, sources, risk) followed by `token`
events (text channels) or `phrase` events (voice channels).

Run locally:  .venv/bin/python agent/agent.py
Deploy:       agentcore configure -e agent/agent.py  &&  agentcore launch
"""

from __future__ import annotations

import config
import memory
from prompts import ANSWER_PROMPT, VOICE_ANSWER_PROMPT
from pipeline import (
    assess_risk,
    classify_query,
    contextualize_query,
    retrieve_multi_corpus,
)
from tools import resolve_property

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

app = BedrockAgentCoreApp()


def _build_model(voice: bool) -> BedrockModel:
    cfg: dict = {
        "model_id": config.ANSWER_MODEL,
        "region_name": config.REGION,
        "temperature": 0.3,
        "streaming": True,
        # Without an explicit cap the model can stop mid-sentence on a low
        # default. Voice answers are short; text answers need room.
        "max_tokens": 600 if voice else 2048,
    }
    if config.GUARDRAIL_ID:
        cfg["guardrail_id"] = config.GUARDRAIL_ID
        cfg["guardrail_version"] = config.GUARDRAIL_VERSION
        cfg["guardrail_trace"] = "enabled"
        # "async" lets tokens stream out immediately while the guardrail
        # evaluates in parallel. The default "sync" mode holds and releases
        # tokens in batched windows — which looks like a non-streamed answer.
        cfg["guardrail_stream_processing_mode"] = "async"
    return BedrockModel(**cfg)


def _snippet(text: str, limit: int = 320) -> str:
    """A clean, single-paragraph excerpt of a chunk for the citation UI."""
    s = " ".join(text.split())
    if len(s) <= limit:
        return s
    # Cut at the last word boundary before the limit so it reads cleanly.
    return s[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _sources_block(chunks: list[dict]) -> str:
    """Render retrieved chunks as a numbered SOURCES block for the prompt."""
    if not chunks:
        return "SOURCES: (none found)"
    lines = ["SOURCES:"]
    for i, ch in enumerate(chunks, 1):
        lines.append(f"\n[{i}] {ch['title']}\n{ch['text'].strip()}")
    return "\n".join(lines)


def _build_user_message(query: str, chunks: list[dict], prop: dict | None) -> str:
    parts = []
    if prop:
        parts.append(
            "PROPERTY CONTEXT:\n"
            f"  Address: {prop.get('address', 'unknown')}\n"
            f"  Zone: {prop.get('zone', 'unknown')} - {prop.get('zone_desc', '')}\n"
            f"  Overlays: {prop.get('overlays', 'none')}\n"
            f"  Comp plan: {prop.get('comp_plan', 'unknown')}"
        )
    parts.append(_sources_block(chunks))
    parts.append(f"QUESTION: {query}")
    return "\n\n".join(parts)


@app.entrypoint
async def invoke(payload: dict, context=None):
    """AgentCore Runtime entrypoint. Async generator -> streamed events."""
    query = (payload.get("prompt") or payload.get("query") or "").strip()
    channel = payload.get("channel", "web")
    prop = payload.get("property_context")
    voice = channel in ("voice", "avatar")

    # The runtime supplies the conversation key via context.session_id (the
    # caller's runtimeSessionId); fall back to a payload field for local runs.
    session_id = getattr(context, "session_id", None) or payload.get("session_id")

    if not query:
        yield {"type": "error", "message": "Empty query."}
        return

    # Prior turns for this session — drives both the answer agent's memory
    # and the follow-up query rewrite below.
    history = memory.get_history(session_id)

    # 1-3 — classify, retrieve, risk. Emit a status event before each blocking
    # step so the client shows progress instead of a silent wait.
    yield {"type": "status", "stage": "classifying",
           "text": "Understanding your question…"}
    # Rewrite follow-ups into a standalone query so classify/retrieve resolve
    # references ("what about side fences?") against earlier turns.
    search_query = contextualize_query(query, history)
    classification = classify_query(search_query)

    yield {"type": "status", "stage": "retrieving",
           "text": "Searching Portland city code…"}
    chunks = retrieve_multi_corpus(search_query, classification)
    risk = assess_risk(f"{query}\n{search_query}", classification)

    meta = {
        "type": "meta",
        "classification": classification,
        "risk": risk,
        "sources": [
            {
                "n": i + 1,
                "title": c["title"],
                "uri": c["uri"],
                "score": round(c["score"], 4),
                "snippet": _snippet(c["text"]),
            }
            for i, c in enumerate(chunks)
        ],
    }
    # Surface the rewrite only when it changed something — useful for debugging.
    if search_query != query:
        meta["search_query"] = search_query
    yield meta

    # 4 — answer agent, seeded with prior turns so it has conversation memory.
    agent = Agent(
        model=_build_model(voice),
        system_prompt=VOICE_ANSWER_PROMPT if voice else ANSWER_PROMPT,
        tools=[resolve_property],
        messages=memory.to_strands_messages(history),
    )
    user_message = _build_user_message(query, chunks, prop)

    buffer = ""
    emitted = False
    answer_parts: list[str] = []
    async for event in agent.stream_async(user_message):
        delta = event.get("data")
        if not delta:
            continue
        emitted = True
        answer_parts.append(delta)
        if voice:
            # Emit phrase-by-phrase for natural TTS pacing.
            buffer += delta
            while any(p in buffer for p in ".!?"):
                idx = min(
                    (buffer.index(p) for p in ".!?" if p in buffer), default=-1
                )
                phrase, buffer = buffer[: idx + 1].strip(), buffer[idx + 1:]
                if phrase:
                    yield {"type": "phrase", "text": phrase}
        else:
            yield {"type": "token", "text": delta}

    if voice and buffer.strip():
        yield {"type": "phrase", "text": buffer.strip()}

    # A guardrail block produces an empty stream — give the user a clear reply.
    answer = "".join(answer_parts).strip()
    if not emitted:
        answer = (
            "I can only help with Portland city code, permits, and zoning. "
            "For this topic, please contact the relevant City of Portland "
            "bureau directly."
        )
        yield {"type": "phrase" if voice else "token", "text": answer}
        yield {"type": "blocked", "by": "guardrail"}

    # Persist the exchange so the next turn in this session has context.
    memory.append_turn(session_id, query, answer)

    yield {"type": "done"}


if __name__ == "__main__":
    app.run()
