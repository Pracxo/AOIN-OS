#!/usr/bin/env bash
set -euo pipefail

API_URL="${AION_BRAIN_API_URL:-http://localhost:8080}"
BACKUP_PATH="${BACKUP_PATH:-${1:-}}"
OWNER_SCOPE="${AION_BACKUP_OWNER_SCOPE:-workspace:dev-workspace}"

if [[ -z "${BACKUP_PATH}" ]]; then
  echo "Usage: BACKUP_PATH=artifacts/backups/<backup-id> scripts/restore-preview.sh" >&2
  echo "   or: scripts/restore-preview.sh artifacts/backups/<backup-id>" >&2
  exit 2
fi

payload="$(cat <<JSON
{
  "backup_path": "${BACKUP_PATH}",
  "owner_scope": ["${OWNER_SCOPE}"],
  "conflict_strategy": "skip_conflicts"
}
JSON
)"

if ! curl -fsS \
  -H "Content-Type: application/json" \
  -d "${payload}" \
  "${API_URL}/brain/restore/preview"; then
  echo "AION Brain API is unavailable at ${API_URL}. Start the local stack and retry." >&2
  exit 1
fi
echo
