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
  [[ "${AION_CONNECTOR_PLATFORM_STABILIZATION_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/connector-platform-regression.sh

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "Connector platform stabilization working tree summary:"
git status --short --branch

tag_ref="unavailable"
# aion-v0.1.0 exact-fetch and immutable SHA verification live in scripts/lib/immutable-tags.sh.
tag_ref="$(aion_confirm_immutable_v01_tag_history)"

cat <<SUMMARY
Connector platform stabilization gate result:
- connector_runtime: disabled
- external_calls: absent
- credentials_tokens: absent
- sandbox_execution: absent
- implementation_approved: false
- aion_v0_1_0: ${tag_ref}
connector platform stabilization gate PASS
SUMMARY
