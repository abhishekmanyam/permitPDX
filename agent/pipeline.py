"""Pre-answer pipeline: classify the query, retrieve from the Knowledge Base,
and assess risk. Runs before the answer agent."""

from __future__ import annotations

import json
import re

import boto3

import config
from prompts import CLASSIFIER_PROMPT

_bedrock = boto3.client("bedrock-runtime", region_name=config.REGION)
_kb = boto3.client("bedrock-agent-runtime", region_name=config.REGION)

# ---------------------------------------------------------------- classifier


def classify_query(query: str) -> dict:
    """Single Haiku call returning a structured classification."""
    try:
        resp = _bedrock.converse(
            modelId=config.CLASSIFIER_MODEL,
            system=[{"text": CLASSIFIER_PROMPT}],
            messages=[{"role": "user", "content": [{"text": query}]}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.0},
        )
        text = resp["output"]["message"]["content"][0]["text"].strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        data = json.loads(text)
    except (json.JSONDecodeError, KeyError, IndexError, Exception):  # noqa: BLE001
        # Fail safe: broad classification, no title scoping.
        return {
            "intent": "other",
            "bureau": "unknown",
            "relevant_titles": [],
            "requires_property": False,
            "urgency": "low",
            "confidence": 0.0,
        }
    data.setdefault("relevant_titles", [])
    data.setdefault("urgency", "low")
    data.setdefault("requires_property", False)
    data.setdefault("confidence", 0.0)
    return data


# ----------------------------------------------------------------- retrieval


def _retrieve_one(text: str, n: int) -> list[dict]:
    resp = _kb.retrieve(
        knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": text},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": n}
        },
    )
    return resp.get("retrievalResults", [])


def retrieve_multi_corpus(query: str, classification: dict) -> list[dict]:
    """Run a focused KB query per relevant title, merge, dedupe, and rank.

    Returns up to TOP_CHUNKS chunks, each: {text, uri, title, score}.
    """
    titles = classification.get("relevant_titles", [])[: config.MAX_TITLES_PER_QUERY]
    merged: dict[str, dict] = {}

    queries: list[tuple[str, str | None]] = []
    if titles:
        for n in titles:
            name = config.TITLES.get(str(n), "")
            queries.append((f"Title {n} {name}: {query}", str(n)))
    else:
        queries.append((query, None))  # broad fallback

    for text, title_n in queries:
        for r in _retrieve_one(text, config.RESULTS_PER_TITLE):
            uri = r.get("location", {}).get("s3Location", {}).get("uri", "")
            chunk_text = r.get("content", {}).get("text", "")
            score = r.get("score", 0.0)
            # +boost when the chunk's source file matches the queried title.
            if title_n and f"title_{title_n}." in uri:
                score *= config.ON_CORPUS_BOOST
            # Dedupe by chunk content — every chunk of a title shares one
            # source-file URI, so the URI cannot identify a chunk.
            key = chunk_text[:200]
            prev = merged.get(key)
            if prev is None or score > prev["score"]:
                merged[key] = {
                    "text": chunk_text,
                    "uri": uri,
                    "title": _title_from_uri(uri),
                    "score": score,
                }

    ranked = sorted(merged.values(), key=lambda c: c["score"], reverse=True)
    return ranked[: config.TOP_CHUNKS]


def _title_from_uri(uri: str) -> str:
    m = re.search(r"title_(\d+)\.", uri)
    if not m:
        return "Portland City Code"
    n = m.group(1)
    return f"Title {n} - {config.TITLES.get(n, '')}".strip(" -")


# ---------------------------------------------------------------- risk gate

_STRUCTURAL = re.compile(
    r"\b(structural|load.bearing|foundation|retaining wall|demolition|"
    r"remove a wall|beam|joist|seismic)\b",
    re.I,
)
_ENVIRONMENTAL = re.compile(
    r"\b(asbestos|lead paint|mold|sewage|hazardous|contaminat|flood|landslide|"
    r"erosion|wetland)\b",
    re.I,
)
_LAND_DIVISION = re.compile(r"\b(subdivid|partition|lot line|land division|lot split)\b", re.I)


def assess_risk(query: str, classification: dict) -> dict:
    """Return {level: LOW|MEDIUM|HIGH, reason, category}."""
    text = query
    if _STRUCTURAL.search(text):
        return {"level": "HIGH", "category": "structural_safety",
                "reason": "Touches structural safety — recommend a licensed professional."}
    if _ENVIRONMENTAL.search(text):
        return {"level": "HIGH", "category": "environmental_health",
                "reason": "Touches environmental/health hazards — recommend a professional."}
    level = "LOW"
    if _LAND_DIVISION.search(text):
        level = "MEDIUM"
    if classification.get("urgency") == "high" and level == "LOW":
        level = "MEDIUM"
    reason = {
        "LOW": "",
        "MEDIUM": "This may need a permit or professional review — confirm before starting.",
    }[level]
    return {"level": level, "category": "general", "reason": reason}
