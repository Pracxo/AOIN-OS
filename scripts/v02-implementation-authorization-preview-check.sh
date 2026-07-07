#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local candidates=()
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    candidates+=("origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}")
  fi
  candidates+=(origin/main main)

  for candidate in "${candidates[@]}"; do
    if git_ref_exists "$candidate"; then
      git merge-base HEAD "$candidate" 2>/dev/null && return 0
    fi
  done
  if git_ref_exists HEAD~1; then
    printf '%s\n' "HEAD~1"
    return 0
  fi
  return 1
}

changed_files() {
  local base
  if base="$(comparison_base)"; then
    git diff --name-only --diff-filter=ACMRT "$base" HEAD --
  fi
  git diff --name-only --diff-filter=ACMRT --
  git diff --cached --name-only --diff-filter=ACMRT --
  git ls-files --others --exclude-standard
}

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_V02_IMPLEMENTATION_AUTHORIZATION_PREVIEW_SKIP_INHERITED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 "$@"
}

required_docs=(
  docs/release/v02-implementation-authorization-preview.md
  docs/release/v02-explicit-approval-record-schema.md
  docs/release/v02-runtime-enablement-guard-boundary.md
  docs/release/v02-authorization-state-model.md
  docs/release/v02-authorization-evidence-matrix.md
  docs/release/v02-implementation-authorization-no-go.md
  docs/release/v02-implementation-authorization-checklist.md
  docs/adr/0138-v02-implementation-authorization-preview.md
)

required_examples=(
  examples/release/v02-implementation-authorization-preview.json
  examples/release/v02-explicit-approval-record-schema.json
  examples/release/v02-runtime-enablement-guard-boundary.json
  examples/release/v02-authorization-state-model.json
  examples/release/v02-authorization-evidence-matrix.json
  operator-console-static/demo-data/v02-implementation-authorization-preview.json
  operator-console-static/demo-data/v02-runtime-enablement-guard-boundary.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-147 implementation authorization artifact: $file" >&2
    exit 1
  }
done

grep -q "0138-v02-implementation-authorization-preview.md" docs/adr/README.md || {
  echo "ADR 0138 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 implementation authorization inherited gates deferred to outer aggregate gate"
else
  run_inherited_gate ./scripts/v02-runtime-approval-board-final-review.sh
  run_inherited_gate ./scripts/v02-implementation-go-no-go-final-freeze.sh
  ./scripts/v02-runtime-approval-board-final-no-go-regression.sh
  run_inherited_gate ./scripts/v02-runtime-approval-board-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-approval-vote-record-stabilization-freeze.sh
  run_inherited_gate ./scripts/v02-runtime-approval-board-preview-check.sh
  run_inherited_gate ./scripts/v02-approval-docket-final-review.sh
  run_inherited_gate ./scripts/v02-decision-package-final-review.sh
  run_inherited_gate ./scripts/v02-review-board-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-submission-registry-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-request-pack-final-review.sh
  run_inherited_gate ./scripts/v02-planning-track-closeout.sh
  run_inherited_gate ./scripts/v02-final-planning-release-gate.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

./scripts/v02-implementation-authorization-no-go-regression.sh

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-147" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-147: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-147 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-147 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-147 must not add or change SDK resources or CLI implementations" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

root = Path(sys.argv[1])
paths = [
    root / "examples/release/v02-implementation-authorization-preview.json",
    root / "examples/release/v02-explicit-approval-record-schema.json",
    root / "examples/release/v02-runtime-enablement-guard-boundary.json",
    root / "examples/release/v02-authorization-state-model.json",
    root / "examples/release/v02-authorization-evidence-matrix.json",
    root / "operator-console-static/demo-data/v02-implementation-authorization-preview.json",
    root / "operator-console-static/demo-data/v02-runtime-enablement-guard-boundary.json",
]
true_keys = {
    "v02_implementation_authorization_preview_created",
    "implementation_authorization_preview_only",
    "explicit_approval_record_created",
    "runtime_enablement_guard_created",
    "runtime_approval_board_preview_only",
    "approval_vote_record_created",
    "go_no_go_ledger_created",
    "implementation_no_go_status",
    "approval_docket_preview_only",
    "implementation_decision_record_created",
    "runtime_approval_lock_created",
    "decision_package_preview_only",
    "approval_readiness_preview_only",
    "runtime_decision_lock_created",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}
false_keys = {
    "implementation_authorization_approved",
    "explicit_approval_record_approval",
    "runtime_enablement_guard_release_approved",
    "runtime_approval_board_decision_approved",
    "runtime_approval_board_final_review_approval",
    "approval_vote_record_approval",
    "approval_vote_record_closeout_approval",
    "approval_vote_record_runtime_effect",
    "implementation_go_status",
    "implementation_go_final_approval",
    "go_no_go_ledger_runtime_effect",
    "approval_docket_item_approved",
    "approval_docket_final_review_approval",
    "implementation_decision_record_approval",
    "implementation_decision_record_closeout_approval",
    "runtime_approval_lock_release_approved",
    "runtime_approval_review_approved",
    "decision_package_approval",
    "approval_readiness_approved",
    "runtime_decision_lock_release_approved",
    "runtime_decision_readiness_approved",
    "review_board_decision_approval",
    "routing_decision_approval",
    "reviewer_signoff_implementation_approval",
    "preapproval_queue_item_approved",
    "request_pack_approval",
    "submission_approval",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
    "runtime_implementation_approved",
    "backlog_implementation_items_approved",
    "workstream_implementation_approved",
    "proposal_implementation_approved",
    "approval_queue_item_approved",
    "approval_workflow_bypassed",
    "approval_record_missing",
    "adr_dependency_bypassed",
    "gate_dependency_bypassed",
    "evidence_completeness_bypassed",
    "submission_freeze_bypassed",
    "preapproval_gate_bypassed",
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "package_files_added",
    "migrations_added",
    "approval_status",
    "implementation_authorization_status",
    "runtime_guard_release_status",
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}
required_safety = {
    "no secrets",
    "no tokens",
    "no credentials",
    "no endpoints",
    "no raw prompts",
    "no hidden reasoning",
}
forbidden_actions = {
    "activate_module",
    "activate_capability",
    "load_code",
    "execute_tool",
    "enable_external_model_calls",
    "hard_delete",
}


def assert_nested_false(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}: {key} must be false")
            assert_nested_false(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            assert_nested_false(nested, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    for key in true_keys:
        if payload.get(key) is not True:
            raise SystemExit(f"{path}: {key} must be true")
    for key in false_keys:
        if payload.get(key) is not False:
            raise SystemExit(f"{path}: {key} must be false")
    safety = set(payload.get("content_safety", []))
    if not required_safety.issubset(safety):
        raise SystemExit(f"{path}: content safety markers missing")
    actions = {
        item.get("action_key")
        for item in payload.get("forbidden_actions", [])
        if isinstance(item, dict) and item.get("allowed") is False
    }
    if not forbidden_actions.issubset(actions):
        raise SystemExit(f"{path}: forbidden action descriptors missing")
    assert_nested_false(payload, str(path))

print("v0.2 implementation authorization JSON checks PASS")
PY

cat <<'SUMMARY'
v0.2 implementation authorization preview result:
- v02_implementation_authorization_preview_created: true
- implementation_authorization_preview_only: true
- implementation_authorization_approved: false
- explicit_approval_record_created: true
- explicit_approval_record_approval: false
- runtime_enablement_guard_created: true
- runtime_enablement_guard_release_approved: false
- runtime_approval_board_decision_approved: false
- implementation_go_status: false
- implementation_no_go_status: true
- runtime_implementation_approved: false
- v02_tag_created: false
- v02_release_created: false
v0.2 implementation authorization preview check PASS
SUMMARY
