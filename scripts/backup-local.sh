#!/usr/bin/env bash
set -euo pipefail

API_URL="${AION_BRAIN_API_URL:-http://localhost:8080}"
OUTPUT_DIR="${BACKUP_OUTPUT_DIR:-artifacts/backups}"
OWNER_SCOPE="${AION_BACKUP_OWNER_SCOPE:-workspace:dev-workspace}"
REDACTION_MODE="${AION_BACKUP_REDACTION_MODE:-redact_sensitive}"
DRY_RUN="${AION_BACKUP_DRY_RUN:-false}"

payload="$(cat <<JSON
{
  "owner_scope": ["${OWNER_SCOPE}"],
  "resource_types": ["events", "memory", "traces", "kernel_records"],
  "output_dir": "${OUTPUT_DIR}",
  "redaction_mode": "${REDACTION_MODE}",
  "dry_run": ${DRY_RUN}
}
JSON
)"

if ! curl -fsS \
  -H "Content-Type: application/json" \
  -d "${payload}" \
  "${API_URL}/brain/backups/export"; then
  echo "AION Brain API is unavailable at ${API_URL}. Start the local stack and retry." >&2
  exit 1
fi
echo
