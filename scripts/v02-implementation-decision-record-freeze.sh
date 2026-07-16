#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_V02_IMPLEMENTATION_DECISION_RECORD_FREEZE_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/v02-approval-docket-stabilization-gate.sh

git diff --check

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/check.sh
fi

echo "v0.2 implementation decision record freeze working tree summary:"
git status --short --branch

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-142" >&2
  exit 1
fi

tag_ref="unavailable"
# aion-v0.1.0 exact-fetch and immutable SHA verification live in scripts/lib/immutable-tags.sh.
tag_ref="$(aion_confirm_immutable_v01_tag_history)"

cat <<SUMMARY
v0.2 implementation decision record freeze result:
- v02_approval_docket_stabilized: true
- implementation_decision_record_freeze_created: true
- approval_docket_stabilization_approval: false
- implementation_decision_record_freeze_approval: false
- implementation_decision_record_approval: false
- runtime_approval_review_approved: false
- runtime_decision_lock_release_approved: false
- runtime_decision_readiness_approved: false
- runtime_implementation_approved: false
- v02_tag_created: false
- v02_release_created: false
- aion_v0_1_0: ${tag_ref}
v0.2 implementation decision record freeze PASS
SUMMARY
