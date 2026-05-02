#!/usr/bin/env bash
set -euo pipefail

echo "Starting tasty platform with Postgres..."
docker compose up --build -d

echo "Waiting for API health..."
for _ in {1..30}; do
  if curl -s "http://127.0.0.1:8000/health" >/dev/null; then
    echo "API is healthy."
    exit 0
  fi
  sleep 1
done

echo "API did not become healthy in time."
exit 1
