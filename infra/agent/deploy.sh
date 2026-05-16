#!/usr/bin/env bash
# Deploy the Portland Permit Assistant agent to the Bedrock AgentCore runtime.
# This is separate from the ECS deploy (infra/fargate/deploy.sh): ECS ships the
# web frontend + the thin API adapter, while the agent reasoning (classify,
# retrieve, answer) runs here, in the AgentCore runtime.
#
# Run from the repo root:  bash infra/agent/deploy.sh
set -euo pipefail

export AWS_PROFILE=cd
export AWS_REGION=us-west-2

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AGENTCORE="$REPO_ROOT/.venv/bin/agentcore"

# agentcore reads .bedrock_agentcore.yaml from the working directory.
cd "$REPO_ROOT/agent"

echo "==> Launching agent to Bedrock AgentCore (profile=$AWS_PROFILE, region=$AWS_REGION)"
"$AGENTCORE" launch

echo "==> Done. Runtime: permitpdx_agent-FRqyV95VJQ"
