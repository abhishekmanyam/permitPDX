"""Shared infrastructure constants for the Portland Permit Assistant."""

AWS_PROFILE = "cd"
REGION = "us-west-2"
ACCOUNT_ID = "890992969813"

PROJECT = "portland-permit"
ENV = "dev"

# Phase 1 — Knowledge Base
SOURCE_BUCKET = f"portland-permit-kb-source-dev-{ACCOUNT_ID}"
VECTOR_BUCKET = f"portland-permit-kb-vectors-dev-{ACCOUNT_ID}"
VECTOR_INDEX = "portland-permit-index"
KB_NAME = f"permitpdx-kb-{ENV}"
KB_ROLE_NAME = f"{PROJECT}-kb-role-{ENV}"
DATA_SOURCE_NAME = f"permitpdx-city-code-{ENV}"

EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBED_DIM = 1024

# Models (inference profiles)
ANSWER_MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
CLASSIFIER_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Title number -> human name, for the corpus
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
