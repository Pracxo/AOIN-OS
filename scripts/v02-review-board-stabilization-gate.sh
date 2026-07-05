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
  [[ "${AION_V02_REVIEW_BOARD_STABILIZATION_SKIP_INHERITED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 "$@"
}

required_docs=(
  docs/release/v02-review-board-stabilization-gate.md
  docs/release/v02-review-routing-freeze.md
  docs/release/v02-reviewer-quorum-model.md
  docs/release/v02-decision-readiness-evidence-baseline.md
  docs/release/v02-review-board-closeout-checklist.md
  docs/release/v02-review-routing-no-go.md
  docs/release/v02-review-board-stabilization-summary.md
  docs/adr/0128-v02-review-board-stabilization.md
)

required_examples=(
  examples/release/v02-review-board-stabilization-gate.json
  examples/release/v02-review-routing-freeze.json
  examples/release/v02-reviewer-quorum-model.json
  examples/release/v02-decision-readiness-evidence-baseline.json
  examples/release/v02-review-board-closeout-result.json
  operator-console-static/demo-data/v02-review-board-stabilization.json
  operator-console-static/demo-data/v02-review-routing-freeze.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-137 review board stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0128-v02-review-board-stabilization.md" docs/adr/README.md || {
  echo "ADR 0128 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 review board stabilization inherited gates deferred to outer aggregate gate"
else
  run_inherited_gate ./scripts/v02-preapproval-review-board-check.sh
  run_inherited_gate ./scripts/v02-review-board-freeze.sh
  ./scripts/v02-review-board-no-go-regression.sh
  run_inherited_gate ./scripts/v02-submission-registry-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-submission-registry-freeze.sh
  run_inherited_gate ./scripts/v02-submission-registry-preview-check.sh
  run_inherited_gate ./scripts/v02-preapproval-queue-freeze.sh
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

./scripts/v02-review-board-stabilization-no-go-regression.sh

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-137" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-137: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-137 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-137 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-137 must not add or change SDK resources or CLI implementations" >&2
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
    root / "examples/release/v02-review-board-stabilization-gate.json",
    root / "examples/release/v02-review-routing-freeze.json",
    root / "examples/release/v02-reviewer-quorum-model.json",
    root / "examples/release/v02-decision-readiness-evidence-baseline.json",
    root / "examples/release/v02-review-board-closeout-result.json",
    root / "operator-console-static/demo-data/v02-review-board-stabilization.json",
    root / "operator-console-static/demo-data/v02-review-routing-freeze.json",
]
true_keys = {
    "v02_review_board_stabilized",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}
false_keys = {
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
    if payload.get("task_id") != "AION-137":
        raise SystemExit(f"{path} must identify AION-137")
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
    for action in payload["forbidden_actions"]:
        if action.get("allowed") is not False:
            raise SystemExit(f"{path} forbidden action must be disallowed")

routing = json.loads((root / "examples/release/v02-review-routing-freeze.json").read_text())
for route in routing.get("routes", []):
    if route.get("implementation_approval") is not False:
        raise SystemExit("routing implementation approval must be false")
    if route.get("runtime_enabled") is not False:
        raise SystemExit("routing runtime enabled must be false")

print("AION-137 JSON examples valid")
PY

cat <<'SUMMARY'
v0.2 review board stabilization gate result:
- v02_review_board_stabilized: true
- review_board_planning_only: true
- review_board_decision_approval: false
- routing_decision_approval: false
- reviewer_signoff_implementation_approval: false
- preapproval_queue_item_approved: false
- request_pack_approval: false
- submission_approval: false
- runtime_implementation_approved: false
- v02_tag_created: false
- v02_release_created: false
v0.2 review board stabilization gate PASS
SUMMARY
