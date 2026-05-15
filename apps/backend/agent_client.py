"""Client for the AgentCore Runtime. Invokes the deployed Portland Permit
Assistant agent and yields the events it streams back."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator

import boto3

REGION = os.environ.get("AWS_REGION", "us-west-2")
AGENT_RUNTIME_ARN = os.environ.get(
    "AGENT_RUNTIME_ARN",
    "arn:aws:bedrock-agentcore:us-west-2:890992969813:runtime/permitpdx_agent-FRqyV95VJQ",
)

_client = boto3.client("bedrock-agentcore", region_name=REGION)


def invoke_agent(prompt: str, session_id: str, channel: str = "web",
                 property_context: dict | None = None) -> Iterator[dict]:
    """Invoke the agent and yield each event dict it streams.

    AgentCore requires runtimeSessionId to be at least 33 characters.
    """
    payload = {"prompt": prompt, "channel": channel}
    if property_context:
        payload["property_context"] = property_context

    session_id = (session_id + "-permitpdx-session").ljust(33, "0")[:128]

    resp = _client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=session_id,
        contentType="application/json",
        accept="application/json",
        payload=json.dumps(payload).encode(),
    )

    body = resp["response"]
    for line in body.iter_lines():
        if not line:
            continue
        text = line.decode() if isinstance(line, bytes) else line
        # AgentCore wraps streamed chunks as Server-Sent Events ("data: ...").
        if text.startswith("data:"):
            text = text[5:].strip()
        if not text:
            continue
        try:
            yield json.loads(text)
        except json.JSONDecodeError:
            yield {"type": "token", "text": text}
