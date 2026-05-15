#!/usr/bin/env bash
# Run the Portland Permit Assistant locally for testing.
#   bash dev.sh
# Backend  -> http://localhost:8000
# Frontend -> http://localhost:5173  (also printed on your LAN IP for phones)
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "Missing .env — copy .env.example to .env and fill it in."; exit 1
fi
set -a && . ./.env && set +a

echo "==> Starting backend on :8000"
( cd apps/backend && ../../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 ) &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT

echo "==> Starting frontend dev server (--host for device testing)"
cd apps/web
[ -d node_modules ] || npm install
npm run dev -- --host
