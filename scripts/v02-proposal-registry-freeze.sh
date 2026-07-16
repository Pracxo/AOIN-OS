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
  [[ "${AION_V02_PROPOSAL_REGISTRY_FREEZE_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

AION_V02_PROPOSAL_REGISTRY_SKIP_NESTED_GATES=1 ./scripts/v02-workstream-proposal-registry-check.sh

git diff --check

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/check.sh
fi

echo "v0.2 proposal registry freeze working tree summary:"
git status --short --branch

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-126" >&2
  exit 1
fi

tag_ref="unavailable"
# aion-v0.1.0 exact-fetch and immutable SHA verification live in scripts/lib/immutable-tags.sh.
tag_ref="$(aion_confirm_immutable_v01_tag_history)"

cat <<SUMMARY
v0.2 proposal registry freeze result:
- v02_workstream_proposal_registry_created: true
- proposal_registry_preview_only: true
- approval_queue_preview_only: true
- approval_queue_item_approved: false
- v02_tag_created: false
- v02_release_created: false
- runtime_implementation_approved: false
- backlog_implementation_items_approved: false
- workstream_implementation_approved: false
- approval_workflow_bypassed: false
- approval_record_missing: false
- adr_dependency_bypassed: false
- gate_dependency_bypassed: false
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
- aion_v0_1_0: ${tag_ref}
v0.2 proposal registry freeze PASS
SUMMARY
