#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AION_BASE_URL:-http://localhost:3000}"
OUTPUT_DIR="${AION_AUDIT_EXPORT_OUTPUT_DIR:-artifacts/audit}"

if ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "AION Brain API is not reachable at ${BASE_URL}. Start the server first."
  exit 1
fi

curl -fsS \
  -X POST \
  "${BASE_URL}/brain/audit/export" \
  -H "content-type: application/json" \
  -d "{\"owner_scope\":[\"workspace:main\"],\"export_type\":\"jsonl\",\"redaction_mode\":\"redact_sensitive\",\"output_dir\":\"${OUTPUT_DIR}\",\"dry_run\":false,\"metadata\":{\"source\":\"scripts/audit-export.sh\"}}"
