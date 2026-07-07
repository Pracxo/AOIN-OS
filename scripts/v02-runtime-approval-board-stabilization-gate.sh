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
  [[ "${AION_V02_RUNTIME_APPROVAL_BOARD_STABILIZATION_SKIP_INHERITED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 "$@"
}

required_docs=(
  docs/release/v02-runtime-approval-board-stabilization-gate.md
  docs/release/v02-approval-vote-record-freeze.md
  docs/release/v02-implementation-go-no-go-ledger-evidence-baseline.md
  docs/release/v02-runtime-approval-board-lifecycle-evidence-matrix.md
  docs/release/v02-runtime-approval-board-stabilization-summary.md
  docs/release/v02-runtime-approval-board-stabilization-no-go.md
  docs/release/v02-runtime-approval-board-closeout-checklist.md
  docs/adr/0136-v02-runtime-approval-board-stabilization.md
)

required_examples=(
  examples/release/v02-runtime-approval-board-stabilization-gate.json
  examples/release/v02-approval-vote-record-freeze.json
  examples/release/v02-implementation-go-no-go-ledger-evidence-baseline.json
  examples/release/v02-runtime-approval-board-lifecycle-evidence-matrix.json
  examples/release/v02-runtime-approval-board-stabilization-summary.json
  operator-console-static/demo-data/v02-runtime-approval-board-stabilization.json
  operator-console-static/demo-data/v02-approval-vote-record-freeze.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-145 runtime approval board stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0136-v02-runtime-approval-board-stabilization.md" docs/adr/README.md || {
  echo "ADR 0136 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 runtime approval board stabilization inherited gates deferred to outer aggregate gate"
else
  run_inherited_gate ./scripts/v02-runtime-approval-board-preview-check.sh
  run_inherited_gate ./scripts/v02-approval-vote-record-freeze.sh
  ./scripts/v02-runtime-approval-board-no-go-regression.sh
  run_inherited_gate ./scripts/v02-approval-docket-final-review.sh
  run_inherited_gate ./scripts/v02-runtime-approval-lock-freeze.sh
  ./scripts/v02-approval-docket-final-no-go-regression.sh
  run_inherited_gate ./scripts/v02-approval-docket-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-implementation-decision-record-freeze.sh
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

./scripts/v02-runtime-approval-board-stabilization-no-go-regression.sh

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-145" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-145: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-145 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-145 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-145 must not add or change SDK resources or CLI implementations" >&2
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
    root / "examples/release/v02-runtime-approval-board-stabilization-gate.json",
    root / "examples/release/v02-approval-vote-record-freeze.json",
    root / "examples/release/v02-implementation-go-no-go-ledger-evidence-baseline.json",
    root / "examples/release/v02-runtime-approval-board-lifecycle-evidence-matrix.json",
    root / "examples/release/v02-runtime-approval-board-stabilization-summary.json",
    root / "operator-console-static/demo-data/v02-runtime-approval-board-stabilization.json",
    root / "operator-console-static/demo-data/v02-approval-vote-record-freeze.json",
]
true_keys = {
    "v02_runtime_approval_board_stabilized",
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
    "runtime_approval_board_decision_approved",
    "runtime_approval_board_stabilization_approval",
    "approval_vote_record_approval",
    "approval_vote_record_runtime_effect",
    "implementation_go_status",
    "go_no_go_ledger_runtime_effect",
    "approval_docket_item_approved",
    "approval_docket_final_review_approval",
    "approval_docket_stabilization_approval",
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
    "request_package_implementation_approved",
    "proposal_template_implementation_approved",
    "approval_evidence_approval",
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


def assert_false_keys(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys:
                assert nested is False, f"{context}.{key} must be false"
            if key in {
                "implementation_approval",
                "implementation_approved",
                "approval_state",
                "runtime_enabled",
                "release_approval",
                "approval_record_created",
            }:
                assert nested is False, f"{context}.{key} must be false"
            assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_false_keys(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    context = path.relative_to(root).as_posix()
    assert payload["task_id"] == "AION-145", context
    assert payload["status"] == "passed", context
    assert payload["synthetic"] is True, context
    for key in true_keys:
        assert payload.get(key) is True, f"{context}:{key}"
    for key in false_keys:
        assert payload.get(key) is False, f"{context}:{key}"
    assert set(payload["content_safety"]) == required_safety, context
    assert_false_keys(payload, context)

    if "operator-console-static" in context:
        assert payload["read_only"] is True, context
        assert payload["redaction_applied"] is True, context
        assert isinstance(payload["sections"], list) and payload["sections"], context
        assert isinstance(payload["blockers"], list) and payload["blockers"], context
        assert isinstance(payload["warnings"], list), context
        assert isinstance(payload["refs"], list) and payload["refs"], context
        actions = {item["action_key"]: item["allowed"] for item in payload["forbidden_actions"]}
        assert set(actions) == forbidden_actions, context
        assert all(value is False for value in actions.values()), context

    serialized = json.dumps(payload, sort_keys=True).lower()
    for marker in [
        "sk-",
        "ghp_",
        "xoxb-",
        "-----begin private key-----",
        "bearer ",
        "basic ",
        "api_key",
        "private_key",
        "access_token",
        "refresh_token",
        "id_token",
        "client_secret",
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
    ]:
        assert marker not in serialized, f"{context}: blocked marker {marker}"
PY

cat <<'SUMMARY'
v0.2 runtime approval board stabilization gate result:
- docs exist: true
- ADR 0136 indexed: true
- examples valid JSON: true
- runtime approval board stabilized: true
- runtime approval board preview only: true
- runtime approval board decision approved: false
- runtime approval board stabilization approval: false
- approval vote record approval: false
- approval vote record runtime effect: false
- implementation go status: false
- runtime approval lock release approved: false
- runtime approval review approved: false
- v02 tag created: false
- v02 release created: false
- runtime implementation approved: false
- package files added: false
- migrations added: false
v0.2 runtime approval board stabilization gate PASS
SUMMARY
