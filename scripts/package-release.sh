#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BRAIN_API_URL:-http://localhost:8080}"
VERSION="${AION_RELEASE_VERSION:-0.1.0}"
OUTPUT_DIR="${AION_RELEASE_PACKAGE_OUTPUT_DIR:-artifacts/releases}"
SCOPE="${AION_RELEASE_PACKAGE_SCOPE:-workspace:dev-workspace}"

if ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "AION server is not reachable. Start core stack first." >&2
  exit 1
fi

curl -fsS \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{
    \"version\": \"${VERSION}\",
    \"owner_scope\": [\"${SCOPE}\"],
    \"output_dir\": \"${OUTPUT_DIR}\",
    \"dry_run\": false
  }" \
  "${BASE_URL}/brain/release-package/create"

echo
