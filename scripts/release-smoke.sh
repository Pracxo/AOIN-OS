#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:3000}"
SCOPE="${AION_SCOPE:-workspace:main}"

curl -fsS \
  -X POST \
  "${BASE_URL}/brain/golden-path/release-smoke?scope=${SCOPE}"
