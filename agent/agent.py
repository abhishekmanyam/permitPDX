"""Portland Permit Assistant — AgentCore Runtime entrypoint.

Pipeline: classify -> retrieve (multi-corpus KB) -> risk gate -> answer agent.
Streams a `meta` event (classification, sources, risk) followed by `token`
events (text channels) or `phrase` events (voice channels).

Run locally:  .venv/bin/python agent/agent.py
Deploy:       agentcore configure -e agent/agent.py  &&  agentcore launch
"""

from __future__ import annotations

import config
from prompts import ANSWER_PROMPT, VOICE_ANSWER_PROMPT
from pipeline import assess_risk, classify_query, retrieve_multi_corpus

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
    }
    if config.GUARDRAIL_ID:
        cfg["guardrail_id"] = config.GUARDRAIL_ID
        cfg["guardrail_version"] = config.GUARDRAIL_VERSION
        cfg["guardrail_trace"] = "enabled"
    return BedrockModel(**cfg)


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
async def invoke(payload: dict):
    """AgentCore Runtime entrypoint. Async generator -> streamed events."""
    query = (payload.get("prompt") or payload.get("query") or "").strip()
    channel = payload.get("channel", "web")
    prop = payload.get("property_context")
    voice = channel in ("voice", "avatar")

    if not query:
        yield {"type": "error", "message": "Empty query."}
        return

    # 1-3 — classify, retrieve, risk
    classification = classify_query(query)
    chunks = retrieve_multi_corpus(query, classification)
    risk = assess_risk(query, classification)

    yield {
        "type": "meta",
        "classification": classification,
        "risk": risk,
        "sources": [
            {"n": i + 1, "title": c["title"], "uri": c["uri"], "score": round(c["score"], 4)}
            for i, c in enumerate(chunks)
        ],
    }

    # 4 — answer agent
    agent = Agent(
        model=_build_model(voice),
        system_prompt=VOICE_ANSWER_PROMPT if voice else ANSWER_PROMPT,
    )
    user_message = _build_user_message(query, chunks, prop)

    buffer = ""
    async for event in agent.stream_async(user_message):
        delta = event.get("data")
        if not delta:
            continue
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

    yield {"type": "done"}


if __name__ == "__main__":
    app.run()
