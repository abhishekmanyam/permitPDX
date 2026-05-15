"""Phase 4 — create the Bedrock Guardrail for the Portland Permit Assistant.

The guardrail is attached to the answer model (see agent/agent.py). It applies:
  - content filters (hate, violence, sexual, insults, misconduct, prompt attack)
  - a denied topic: advice on evading permits / doing work illegally
  - PII protection for high-sensitivity identifiers (addresses stay allowed —
    they are core to the product)
  - contextual grounding + relevance thresholds

Run:  .venv/bin/python infra/guardrail/setup_guardrail.py
Writes the guardrail id/version into infra/outputs.json.
"""

from __future__ import annotations

import json
import pathlib

import boto3

ROOT = pathlib.Path(__file__).parent.parent
OUTPUTS_PATH = ROOT / "outputs.json"
OUTPUTS = json.loads(OUTPUTS_PATH.read_text())

PROFILE = "cd"
REGION = OUTPUTS["region"]
NAME = "permitpdx-guardrail-dev"

bedrock = boto3.Session(profile_name=PROFILE, region_name=REGION).client("bedrock")


def find_existing() -> str | None:
    for g in bedrock.list_guardrails().get("guardrails", []):
        if g["name"] == NAME:
            return g["id"]
    return None


def main() -> None:
    kwargs = dict(
        name=NAME,
        description="Portland Permit Assistant - safety and grounding guardrail",
        blockedInputMessaging=(
            "I can only help with Portland city code, permits, and zoning "
            "questions. Could you rephrase your question?"
        ),
        blockedOutputsMessaging=(
            "I can't provide that. For this topic, please contact the relevant "
            "City of Portland bureau directly."
        ),
        contentPolicyConfig={
            "filtersConfig": [
                {"type": t, "inputStrength": "HIGH", "outputStrength": "HIGH"}
                for t in ("HATE", "INSULTS", "SEXUAL", "VIOLENCE", "MISCONDUCT")
            ] + [
                # Prompt-attack filtering applies to input only.
                {"type": "PROMPT_ATTACK", "inputStrength": "HIGH",
                 "outputStrength": "NONE"},
            ]
        },
        topicPolicyConfig={
            "topicsConfig": [{
                "name": "Evading Permits",
                "definition": (
                    "Advice on how to avoid required permits, conceal "
                    "unpermitted work, or perform construction illegally."
                ),
                "examples": [
                    "How do I build this without the city finding out?",
                    "What's the best way to skip the permit process?",
                    "How can I hide unpermitted work from an inspector?",
                ],
                "type": "DENY",
            }]
        },
        sensitiveInformationPolicyConfig={
            "piiEntitiesConfig": [
                {"type": t, "action": "BLOCK"}
                for t in ("CREDIT_DEBIT_CARD_NUMBER", "US_SOCIAL_SECURITY_NUMBER",
                          "PASSWORD", "US_BANK_ACCOUNT_NUMBER")
            ]
        },
        contextualGroundingPolicyConfig={
            "filtersConfig": [
                {"type": "GROUNDING", "threshold": 0.6},
                {"type": "RELEVANCE", "threshold": 0.6},
            ]
        },
    )

    existing = find_existing()
    if existing:
        resp = bedrock.update_guardrail(guardrailIdentifier=existing, **kwargs)
        gid, version = existing, resp["version"]
        print(f"updated guardrail {gid} (version {version})")
    else:
        resp = bedrock.create_guardrail(**kwargs)
        gid, version = resp["guardrailId"], resp["version"]
        print(f"created guardrail {gid} (version {version})")

    OUTPUTS["guardrail_id"] = gid
    OUTPUTS["guardrail_version"] = version
    OUTPUTS_PATH.write_text(json.dumps(OUTPUTS, indent=2) + "\n")
    print(f"wrote guardrail_id/version to {OUTPUTS_PATH}")


if __name__ == "__main__":
    main()
