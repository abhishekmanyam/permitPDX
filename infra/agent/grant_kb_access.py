"""Grant the AgentCore Runtime execution role permission to query the
Knowledge Base. `agentcore deploy` auto-creates the execution role but does
not know about our KB, so this inline policy must be added after deploy.

Run:  .venv/bin/python infra/agent/grant_kb_access.py <execution-role-name>
The role name is printed by `agentcore status` and stored in infra/outputs.json.
"""

import json
import pathlib
import sys

import boto3

ROOT = pathlib.Path(__file__).parent.parent
OUTPUTS = json.loads((ROOT / "outputs.json").read_text())

PROFILE = "cd"
REGION = OUTPUTS["region"]
ACCOUNT = "890992969813"
KB_ID = OUTPUTS["knowledge_base_id"]


def main() -> None:
    role = sys.argv[1] if len(sys.argv) > 1 else OUTPUTS.get("agent_execution_role")
    if not role:
        sys.exit("usage: grant_kb_access.py <execution-role-name>")

    iam = boto3.Session(profile_name=PROFILE, region_name=REGION).client("iam")
    iam.put_role_policy(
        RoleName=role,
        PolicyName="kb-retrieve",
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": ["bedrock:Retrieve"],
                "Resource": f"arn:aws:bedrock:{REGION}:{ACCOUNT}:knowledge-base/{KB_ID}",
            }],
        }),
    )
    print(f"granted bedrock:Retrieve on KB {KB_ID} to role {role}")


if __name__ == "__main__":
    main()
