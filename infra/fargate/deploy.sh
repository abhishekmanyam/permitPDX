#!/usr/bin/env bash
# Build the backend container, push to ECR, and roll the ECS service.
# Run from the repo root:  bash infra/fargate/deploy.sh
set -euo pipefail

PROFILE=cd
REGION=us-west-2
ACCOUNT=890992969813
REPO="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/permitpdx-backend"
CLUSTER=permitpdx-cluster
SERVICE=permitpdx-backend
CLOUDFRONT_ID=E1BJO1ZJ0D01W5

# Load MAPBOX_TOKEN for the frontend build.
set -a && . ./.env && set +a

echo "==> ECR login"
aws ecr get-login-password --profile "$PROFILE" --region "$REGION" \
  | docker login --username AWS --password-stdin "${REPO%/*}"

echo "==> Build (linux/amd64 — Fargate requires it)"
docker buildx build --platform linux/amd64 \
  --build-arg VITE_MAPBOX_TOKEN="$MAPBOX_TOKEN" \
  -t "$REPO:latest" --push .

echo "==> Roll the ECS service"
aws ecs update-service --profile "$PROFILE" --region "$REGION" \
  --cluster "$CLUSTER" --service "$SERVICE" --force-new-deployment >/dev/null

# CloudFront caches index.html in front of the ALB — without this the CDN
# keeps serving the old build (and its stale hashed asset references).
echo "==> Invalidate CloudFront cache"
aws cloudfront create-invalidation --profile "$PROFILE" \
  --distribution-id "$CLOUDFRONT_ID" --paths "/*" \
  --query "Invalidation.{Id:Id,Status:Status}" --output text

echo "==> Done. Watch: aws ecs wait services-stable --cluster $CLUSTER --services $SERVICE"
