"""Portland Permit Assistant — channel backend.

A thin FastAPI adapter. It does no agent reasoning: it relays the three
channels (web chat, Twilio voice, HeyGen avatar) to the AgentCore Runtime
and streams responses back. It also serves the built React frontend.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from xml.sax.saxutils import escape

from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

import avatar
from agent_client import invoke_agent
from property import resolve_address, reverse_geocode

app = FastAPI(title="Portland Permit Assistant")

# In production the backend serves the frontend (same origin); CORS only
# matters for the local dev server on a different port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = os.environ.get("WEB_DIR", "web")


# --------------------------------------------------------------- health


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# --------------------------------------------------------------- web chat


@app.post("/api/chat")
async def chat(req: Request) -> StreamingResponse:
    """Stream the agent's response to the web client as Server-Sent Events."""
    body = await req.json()
    message = (body.get("message") or "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())
    prop = body.get("property_context")

    def event_stream():
        try:
            for event in invoke_agent(message, session_id, "web", prop):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:  # noqa: BLE001 — surface failures to the client
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        # Defeat proxy/CDN buffering so tokens reach the browser as they stream.
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ------------------------------------------------------------- property


@app.post("/api/resolve")
async def resolve(req: Request) -> JSONResponse:
    body = await req.json()
    return JSONResponse(resolve_address(body.get("address", "")))


@app.post("/api/reverse-geocode")
async def reverse(req: Request) -> JSONResponse:
    body = await req.json()
    return JSONResponse(reverse_geocode(float(body["lat"]), float(body["lon"])))


# --------------------------------------------------------------- avatar


@app.post("/api/avatar/session")
async def avatar_session(req: Request) -> JSONResponse:
    body = await req.json() if await req.body() else {}
    return JSONResponse(avatar.create_session_token(body.get("sandbox", True)))


@app.post("/api/avatar/stop")
async def avatar_stop(req: Request) -> JSONResponse:
    body = await req.json()
    token = body.get("session_token", "")
    if not token:
        return JSONResponse({"error": "session_token required"}, status_code=400)
    return JSONResponse(avatar.stop_session(token))


# ---------------------- OpenAI-compatible endpoint (HeyGen Custom LLM) ------


def _voice_phrases(message: str, session_id: str):
    """Yield the agent's spoken phrases for a voice/avatar turn."""
    for event in invoke_agent(message, session_id, "avatar"):
        if event.get("type") in ("phrase", "token"):
            text = event.get("text", "").strip()
            if text:
                yield text


def _run_voice_agent(message: str, session_id: str) -> str:
    """Collect the full voice answer from the agent (non-streamed)."""
    return " ".join(_voice_phrases(message, session_id)).strip()


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(req: Request):
    """OpenAI-shaped endpoint. The LiveAvatar Custom LLM posts here."""
    body = await req.json()
    messages = body.get("messages", [])
    stream = bool(body.get("stream", False))
    user_msg = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    session_id = body.get("user") or str(uuid.uuid4())
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    if stream:
        def sse():
            for phrase in _voice_phrases(user_msg, session_id):
                delta = {"role": "assistant", "content": phrase + " "}
                yield "data: " + json.dumps({
                    "id": chunk_id, "object": "chat.completion.chunk",
                    "created": int(time.time()), "model": "portland-permit-assistant",
                    "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
                }) + "\n\n"
            yield "data: " + json.dumps({
                "id": chunk_id, "object": "chat.completion.chunk",
                "created": int(time.time()), "model": "portland-permit-assistant",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }) + "\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            sse(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache, no-transform",
                     "X-Accel-Buffering": "no"},
        )

    answer = _run_voice_agent(user_msg, session_id) or (
        "I'm sorry, I didn't catch that. Could you ask again?"
    )
    return JSONResponse({
        "id": chunk_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "portland-permit-assistant",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": answer},
            "finish_reason": "stop",
        }],
    })


# ------------------------------------------------------ Twilio voice -------

_GREETING = (
    "Welcome to the Portland Permit Assistant. "
    "Ask me a question about city code, permits, or zoning."
)


def _twiml(xml: str) -> Response:
    # Twilio rejects application/xml — it requires text/xml.
    return Response(content=xml, media_type="text/xml")


def _gather(prompt: str, action: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?><Response>'
        f'<Gather input="speech" action="{action}" method="POST" '
        'speechTimeout="auto" language="en-US">'
        f"<Say>{escape(prompt)}</Say></Gather>"
        '<Say>I did not hear anything. Goodbye.</Say><Hangup/></Response>'
    )


@app.post("/api/voice/incoming")
async def voice_incoming() -> Response:
    return _twiml(_gather(_GREETING, "/api/voice/respond"))


@app.post("/api/voice/respond")
async def voice_respond(
    SpeechResult: str = Form(default=""), CallSid: str = Form(default=""),
) -> Response:
    speech = (SpeechResult or "").strip()
    if not speech:
        return _twiml(_gather("Sorry, could you repeat that?", "/api/voice/respond"))
    if any(w in speech.lower() for w in ("goodbye", "thank you", "bye", "that's all")):
        return _twiml(
            '<?xml version="1.0" encoding="UTF-8"?><Response>'
            "<Say>Thanks for calling the Portland Permit Assistant. Goodbye.</Say>"
            "<Hangup/></Response>"
        )
    answer = _run_voice_agent(speech, CallSid or str(uuid.uuid4()))
    answer = answer or "I'm sorry, I couldn't find an answer to that."
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?><Response>'
        f"<Say>{escape(answer)}</Say>"
        '<Gather input="speech" action="/api/voice/respond" method="POST" '
        'speechTimeout="auto" language="en-US">'
        "<Say>Do you have another question?</Say></Gather>"
        "<Say>Goodbye.</Say><Hangup/></Response>"
    )
    return _twiml(xml)


# ------------------------------------------------------- static frontend ---

if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
else:
    @app.get("/")
    def root() -> HTMLResponse:
        return HTMLResponse("<h1>Portland Permit Assistant</h1>"
                            "<p>API is running. Frontend build not found.</p>")
