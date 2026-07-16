#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

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

if [[ "${AION_CONNECTOR_SAFETY_FREEZE_SKIP_RELEASE_GATE:-}" == "1" ]]; then
  echo "PASS: connector release gate deferred to outer aggregate gate"
else
  ./scripts/connector-release-gate.sh
fi

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "Connector safety freeze working tree summary:"
git status --short --branch

tag_ref="unavailable"
# aion-v0.1.0 exact-fetch and immutable SHA verification live in scripts/lib/immutable-tags.sh.
tag_ref="$(aion_confirm_immutable_v01_tag_history)"

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
