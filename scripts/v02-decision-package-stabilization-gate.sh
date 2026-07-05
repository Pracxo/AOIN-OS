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
  [[ "${AION_V02_DECISION_PACKAGE_STABILIZATION_SKIP_INHERITED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 "$@"
}

required_docs=(
  docs/release/v02-decision-package-stabilization-gate.md
  docs/release/v02-approval-readiness-freeze.md
  docs/release/v02-runtime-decision-closeout-boundary.md
  docs/release/v02-decision-package-evidence-baseline.md
  docs/release/v02-decision-readiness-status-summary.md
  docs/release/v02-decision-package-stabilization-no-go.md
  docs/release/v02-decision-package-closeout-checklist.md
  docs/adr/0130-v02-decision-package-stabilization.md
)

required_examples=(
  examples/release/v02-decision-package-stabilization-gate.json
  examples/release/v02-approval-readiness-freeze.json
  examples/release/v02-runtime-decision-closeout-boundary.json
  examples/release/v02-decision-package-evidence-baseline.json
  examples/release/v02-decision-readiness-status-summary.json
  operator-console-static/demo-data/v02-decision-package-stabilization.json
  operator-console-static/demo-data/v02-approval-readiness-freeze.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-139 decision package stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0130-v02-decision-package-stabilization.md" docs/adr/README.md || {
  echo "ADR 0130 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 decision package stabilization inherited gates deferred to outer aggregate gate"
else
  run_inherited_gate ./scripts/v02-decision-package-preview-check.sh
  run_inherited_gate ./scripts/v02-decision-package-freeze.sh
  ./scripts/v02-decision-package-no-go-regression.sh
  run_inherited_gate ./scripts/v02-review-board-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-review-routing-freeze.sh
  ./scripts/v02-review-board-stabilization-no-go-regression.sh
  run_inherited_gate ./scripts/v02-preapproval-review-board-check.sh
  run_inherited_gate ./scripts/v02-submission-registry-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-submission-registry-preview-check.sh
  run_inherited_gate ./scripts/v02-request-pack-final-review.sh
  run_inherited_gate ./scripts/v02-request-pack-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-implementation-request-pack-check.sh
  run_inherited_gate ./scripts/v02-planning-track-closeout.sh
  run_inherited_gate ./scripts/v02-final-planning-release-gate.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

./scripts/v02-decision-package-stabilization-no-go-regression.sh

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-139" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-139: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-139 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-139 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-139 must not add or change SDK resources or CLI implementations" >&2
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
    root / "examples/release/v02-decision-package-stabilization-gate.json",
    root / "examples/release/v02-approval-readiness-freeze.json",
    root / "examples/release/v02-runtime-decision-closeout-boundary.json",
    root / "examples/release/v02-decision-package-evidence-baseline.json",
    root / "examples/release/v02-decision-readiness-status-summary.json",
    root / "operator-console-static/demo-data/v02-decision-package-stabilization.json",
    root / "operator-console-static/demo-data/v02-approval-readiness-freeze.json",
]
true_keys = {
    "v02_decision_package_stabilized",
    "decision_package_preview_only",
    "approval_readiness_preview_only",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}
false_keys = {
    "decision_package_approval",
    "approval_readiness_approved",
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
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
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
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in {
                "implementation_approval",
                "implementation_approved",
                "submission_approved",
                "runtime_enabled",
                "approval_state",
                "implementation_state",
            } and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_false_keys(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    if payload.get("task_id") != "AION-139":
        raise SystemExit(f"{path} must identify AION-139")
    if payload.get("status") != "passed":
        raise SystemExit(f"{path} must be passed")
    if payload.get("synthetic") is not True:
        raise SystemExit(f"{path} must be synthetic")
    for key in true_keys:
        if payload.get(key) is not True:
            raise SystemExit(f"{path} must mark {key} true")
    assert_false_keys(payload, str(path))

for path in paths[-2:]:
    payload = json.loads(path.read_text())
    if payload.get("read_only") is not True:
        raise SystemExit(f"{path} must be read-only static data")
    if payload.get("redaction_applied") is not True:
        raise SystemExit(f"{path} must mark redaction applied")
    for key in ("sections", "blockers", "warnings", "refs", "forbidden_actions"):
        if not payload.get(key):
            raise SystemExit(f"{path} must include {key}")
    action_keys = {action.get("action_key") for action in payload["forbidden_actions"]}
    if action_keys != forbidden_actions:
        raise SystemExit(f"{path} must use the shared forbidden action set")
    for action in payload["forbidden_actions"]:
        if action.get("allowed") is not False:
            raise SystemExit(f"{path} forbidden actions must remain denied")

print("AION-139 JSON examples valid")
PY

cat <<'SUMMARY'
v0.2 decision package stabilization gate result:
- v02_decision_package_stabilized: true
- decision_package_preview_only: true
- decision_package_approval: false
- approval_readiness_preview_only: true
- approval_readiness_approved: false
- runtime_decision_readiness_approved: false
- review_board_decision_approval: false
- routing_decision_approval: false
- reviewer_signoff_implementation_approval: false
- runtime_implementation_approved: false
- v02_tag_created: false
- v02_release_created: false
v0.2 decision package stabilization gate PASS
SUMMARY

