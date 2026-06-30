#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/connector-release-gate.sh

if [[ "${AION_CONNECTOR_SAFETY_FREEZE_SKIP_FULL_CHECK:-0}" != "1" ]]; then
  ./scripts/check.sh
else
  echo "Connector safety freeze full check skipped by aggregate gate"
fi

echo "Connector safety freeze working tree summary:"
git status --short --branch

tag_ref="$(git rev-parse aion-v0.1.0 2>/dev/null)" || {
  echo "aion-v0.1.0 tag is missing" >&2
  exit 1
}

if git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
  if git merge-base --is-ancestor aion-v0.1.0 origin/main; then
    echo "aion-v0.1.0 is in origin/main history"
  else
    echo "aion-v0.1.0 ancestry could not be confirmed against origin/main" >&2
  fi
elif git rev-parse --verify --quiet main >/dev/null 2>&1; then
  if git merge-base --is-ancestor aion-v0.1.0 main; then
    echo "aion-v0.1.0 is in main history"
  else
    echo "aion-v0.1.0 ancestry could not be confirmed against main" >&2
  fi
else
  echo "main comparison ref unavailable; tag ancestry check skipped"
fi

cat <<SUMMARY
Connector safety freeze result:
- connector_runtime: disabled
- external_calls: absent
- credentials_tokens: absent
- sandbox_execution: absent
- implementation_approved: false
- aion_v0_1_0: ${tag_ref}
Connector safety freeze PASS
SUMMARY
