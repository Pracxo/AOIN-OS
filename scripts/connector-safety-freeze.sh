#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_CONNECTOR_SAFETY_FREEZE_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/connector-release-gate.sh

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "Connector safety freeze working tree summary:"
git status --short --branch

tag_ref="unavailable"
if git_ref_exists aion-v0.1.0; then
  tag_ref="$(git rev-parse aion-v0.1.0)"
  if git_ref_exists origin/main; then
    if git merge-base --is-ancestor aion-v0.1.0 origin/main; then
      echo "aion-v0.1.0 is in origin/main history"
    else
      echo "WARN: aion-v0.1.0 ancestry could not be confirmed against origin/main" >&2
    fi
  elif git_ref_exists main; then
    if git merge-base --is-ancestor aion-v0.1.0 main; then
      echo "aion-v0.1.0 is in main history"
    else
      echo "WARN: aion-v0.1.0 ancestry could not be confirmed against main" >&2
    fi
  else
    echo "WARN: origin/main unavailable in this checkout; skipping non-release tag ancestry confirmation"
  fi
else
  echo "WARN: aion-v0.1.0 tag unavailable in this checkout; skipping non-release tag ancestry confirmation"
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
