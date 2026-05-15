"""Phase 1 — provision the Bedrock Knowledge Base over the Portland city code corpus.

Creates (idempotently):
  1. an S3 Vectors bucket + index (1024-dim, cosine — Titan Embed v2)
  2. an IAM service role for the Knowledge Base
  3. the Bedrock Knowledge Base (S3 Vectors storage)
  4. an S3 data source with hierarchical chunking
  5. starts an ingestion job

Run:  .venv/bin/python infra/kb/setup_kb.py
Outputs are written to infra/outputs.json.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

import boto3
from botocore.exceptions import ClientError

import config as c

session = boto3.Session(profile_name=c.AWS_PROFILE, region_name=c.REGION)
s3v = session.client("s3vectors")
iam = session.client("iam")
bedrock_agent = session.client("bedrock-agent")

OUTPUTS = pathlib.Path(__file__).parent.parent / "outputs.json"


def load_outputs() -> dict:
    return json.loads(OUTPUTS.read_text()) if OUTPUTS.exists() else {}


def save_outputs(data: dict) -> None:
    OUTPUTS.write_text(json.dumps(data, indent=2) + "\n")
    print(f"  → wrote {OUTPUTS}")


def step_vector_store() -> tuple[str, str]:
    """Create the S3 Vectors bucket and index. Returns (bucket_arn, index_arn)."""
    print("[1/5] S3 Vectors store")
    try:
        s3v.create_vector_bucket(vectorBucketName=c.VECTOR_BUCKET)
        print(f"  created vector bucket {c.VECTOR_BUCKET}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise
        print(f"  vector bucket {c.VECTOR_BUCKET} already exists")

    bucket = s3v.get_vector_bucket(vectorBucketName=c.VECTOR_BUCKET)["vectorBucket"]

    # Bedrock KB stores the chunk text and a metadata blob in the vector store;
    # both exceed the S3 Vectors 2048-byte filterable-metadata cap, so they must
    # be declared non-filterable.
    try:
        s3v.create_index(
            vectorBucketName=c.VECTOR_BUCKET,
            indexName=c.VECTOR_INDEX,
            dataType="float32",
            dimension=c.EMBED_DIM,
            distanceMetric="cosine",
            metadataConfiguration={
                "nonFilterableMetadataKeys": [
                    "AMAZON_BEDROCK_TEXT",
                    "AMAZON_BEDROCK_METADATA",
                ]
            },
        )
        print(f"  created index {c.VECTOR_INDEX}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise
        print(f"  index {c.VECTOR_INDEX} already exists")

    index = s3v.get_index(
        vectorBucketName=c.VECTOR_BUCKET, indexName=c.VECTOR_INDEX
    )["index"]
    return bucket["vectorBucketArn"], index["indexArn"]


def step_iam_role(vector_bucket_arn: str) -> str:
    """Create the Knowledge Base service role. Returns role ARN."""
    print("[2/5] IAM service role")
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {"StringEquals": {"aws:SourceAccount": c.ACCOUNT_ID}},
        }],
    }
    try:
        role = iam.create_role(
            RoleName=c.KB_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="Portland Permit Assistant - Bedrock Knowledge Base role",
        )["Role"]
        print(f"  created role {c.KB_ROLE_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            raise
        role = iam.get_role(RoleName=c.KB_ROLE_NAME)["Role"]
        print(f"  role {c.KB_ROLE_NAME} already exists")

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "EmbedModel",
                "Effect": "Allow",
                "Action": "bedrock:InvokeModel",
                "Resource": f"arn:aws:bedrock:{c.REGION}::foundation-model/{c.EMBED_MODEL_ID}",
            },
            {
                "Sid": "SourceBucket",
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{c.SOURCE_BUCKET}",
                    f"arn:aws:s3:::{c.SOURCE_BUCKET}/*",
                ],
            },
            {
                "Sid": "VectorStore",
                "Effect": "Allow",
                "Action": "s3vectors:*",
                "Resource": [vector_bucket_arn, f"{vector_bucket_arn}/*"],
            },
        ],
    }
    iam.put_role_policy(
        RoleName=c.KB_ROLE_NAME,
        PolicyName="kb-access",
        PolicyDocument=json.dumps(policy),
    )
    print("  attached inline policy kb-access")
    return role["Arn"]


def step_knowledge_base(role_arn: str, vector_bucket_arn: str, index_arn: str) -> str:
    """Create the Knowledge Base. Returns KB id."""
    print("[3/5] Knowledge Base")
    existing = bedrock_agent.list_knowledge_bases(maxResults=100)["knowledgeBaseSummaries"]
    for kb in existing:
        if kb["name"] == c.KB_NAME:
            print(f"  KB {c.KB_NAME} already exists: {kb['knowledgeBaseId']}")
            return kb["knowledgeBaseId"]

    # IAM role propagation can lag — retry the create.
    for attempt in range(6):
        try:
            resp = bedrock_agent.create_knowledge_base(
                name=c.KB_NAME,
                description="Portland City Code — 14 titles",
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": (
                            f"arn:aws:bedrock:{c.REGION}::foundation-model/{c.EMBED_MODEL_ID}"
                        ),
                        "embeddingModelConfiguration": {
                            "bedrockEmbeddingModelConfiguration": {
                                "dimensions": c.EMBED_DIM,
                                "embeddingDataType": "FLOAT32",
                            }
                        },
                    },
                },
                storageConfiguration={
                    "type": "S3_VECTORS",
                    "s3VectorsConfiguration": {
                        "vectorBucketArn": vector_bucket_arn,
                        "indexArn": index_arn,
                    },
                },
            )
            kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
            print(f"  created KB {kb_id}")
            return kb_id
        except ClientError as e:
            if "validate" in str(e).lower() or "role" in str(e).lower():
                print(f"  role not ready, retrying ({attempt + 1}/6)...")
                time.sleep(10)
                continue
            raise
    raise RuntimeError("Knowledge Base creation failed after retries")


def step_data_source(kb_id: str) -> str:
    """Create the S3 data source with hierarchical chunking. Returns data source id."""
    print("[4/5] Data source")
    existing = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)["dataSourceSummaries"]
    for ds in existing:
        if ds["name"] == c.DATA_SOURCE_NAME:
            print(f"  data source already exists: {ds['dataSourceId']}")
            return ds["dataSourceId"]

    resp = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name=c.DATA_SOURCE_NAME,
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{c.SOURCE_BUCKET}",
                "inclusionPrefixes": ["city-code/"],
            },
        },
        vectorIngestionConfiguration={
            "chunkingConfiguration": {
                "chunkingStrategy": "HIERARCHICAL",
                "hierarchicalChunkingConfiguration": {
                    "levelConfigurations": [
                        {"maxTokens": 1500},  # parent
                        {"maxTokens": 300},   # child
                    ],
                    "overlapTokens": 60,
                },
            }
        },
    )
    ds_id = resp["dataSource"]["dataSourceId"]
    print(f"  created data source {ds_id}")
    return ds_id


def step_ingest(kb_id: str, ds_id: str) -> None:
    """Start an ingestion job."""
    print("[5/5] Ingestion job")
    job = bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
    job_id = job["ingestionJob"]["ingestionJobId"]
    print(f"  started ingestion job {job_id} — this runs in the background (~5-15 min)")
    print(f"  check: aws bedrock-agent get-ingestion-job --profile {c.AWS_PROFILE} "
          f"--region {c.REGION} --knowledge-base-id {kb_id} --data-source-id {ds_id} "
          f"--ingestion-job-id {job_id}")


def main() -> None:
    outputs = load_outputs()
    vb_arn, idx_arn = step_vector_store()
    role_arn = step_iam_role(vb_arn)
    kb_id = step_knowledge_base(role_arn, vb_arn, idx_arn)
    ds_id = step_data_source(kb_id)
    outputs.update({
        "region": c.REGION,
        "source_bucket": c.SOURCE_BUCKET,
        "vector_bucket_arn": vb_arn,
        "vector_index_arn": idx_arn,
        "kb_role_arn": role_arn,
        "knowledge_base_id": kb_id,
        "data_source_id": ds_id,
    })
    save_outputs(outputs)
    step_ingest(kb_id, ds_id)
    print("\nPhase 1 complete. Knowledge Base id:", kb_id)


if __name__ == "__main__":
    sys.exit(main())
