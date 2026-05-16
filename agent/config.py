"""Agent runtime configuration. Values can be overridden by environment variables
set at `agentcore configure` time."""

import os

REGION = os.environ.get("AWS_REGION", "us-west-2")

# Bedrock Knowledge Base (see infra/outputs.json)
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "61POYN2UXQ")

# Models — inference profiles
ANSWER_MODEL = os.environ.get("ANSWER_MODEL", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
CLASSIFIER_MODEL = os.environ.get("CLASSIFIER_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# AgentCore Memory — conversation history. Provisioned by the agentcore
# toolkit (see `memory:` in .bedrock_agentcore.yaml); STM-only, 30-day expiry.
MEMORY_ID = os.environ.get("MEMORY_ID", "permitpdx_agent_mem-0vbaOv2Mhs")

# Bedrock Guardrail (see infra/outputs.json)
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "1hhciwdq9v9c")
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")

# Retrieval
MAX_TITLES_PER_QUERY = 3
RESULTS_PER_TITLE = 6
TOP_CHUNKS = 8
ON_CORPUS_BOOST = 1.15

# Portland City Code titles
TITLES = {
    "4": "Original Art Murals",
    "10": "Erosion and Sediment Control",
    "11": "Trees",
    "17": "Public Improvements",
    "18": "Noise Control",
    "24": "Building Regulations",
    "25": "Plumbing",
    "26": "Electrical",
    "27": "Heating and Ventilating",
    "28": "Floating Structures",
    "29": "Property Maintenance",
    "31": "Fire",
    "32": "Signs",
    "33": "Zoning Code",
}
