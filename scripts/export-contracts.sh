#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BRAIN_API_URL:-http://localhost:8080}"

if ! curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  echo "AION server is not reachable. Start it with scripts/docker-up-core.sh."
  exit 0
fi

mkdir -p "$ROOT_DIR/artifacts"
curl --fail-with-body "$BASE_URL/brain/kernel/contracts" \
  > "$ROOT_DIR/artifacts/aion-contracts.json"
echo "Wrote artifacts/aion-contracts.json"
