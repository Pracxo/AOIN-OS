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
  [[ "${AION_V02_REQUEST_PACK_FINAL_REVIEW_SKIP_INHERITED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 "$@"
}

required_docs=(
  docs/release/v02-request-pack-final-review.md
  docs/release/v02-evidence-boundary-closeout.md
  docs/release/v02-preapproval-submission-gate.md
  docs/release/v02-request-approval-guard.md
  docs/release/v02-final-submission-evidence-matrix.md
  docs/release/v02-submission-no-go-review.md
  docs/release/v02-request-pack-final-checklist.md
  docs/adr/0124-v02-request-pack-final-review.md
)

required_examples=(
  examples/release/v02-request-pack-final-review.json
  examples/release/v02-evidence-boundary-closeout.json
  examples/release/v02-preapproval-submission-gate.json
  examples/release/v02-request-approval-guard.json
  examples/release/v02-final-submission-evidence-matrix.json
  operator-console-static/demo-data/v02-request-pack-final-review.json
  operator-console-static/demo-data/v02-preapproval-submission-gate.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-133 request pack final review artifact: $file" >&2
    exit 1
  }
done

grep -q "0124-v02-request-pack-final-review.md" docs/adr/README.md || {
  echo "ADR 0124 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 request pack final review inherited gates deferred to outer aggregate gate"
else
  run_inherited_gate ./scripts/v02-request-pack-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-request-pack-submission-freeze.sh
  ./scripts/v02-request-pack-stabilization-no-go-regression.sh
  run_inherited_gate ./scripts/v02-implementation-request-pack-check.sh
  run_inherited_gate ./scripts/v02-request-pack-freeze.sh
  ./scripts/v02-request-pack-no-go-regression.sh
  run_inherited_gate ./scripts/v02-planning-track-closeout.sh
  run_inherited_gate ./scripts/v02-final-planning-release-gate.sh
  run_inherited_gate ./scripts/v02-planning-master-checkpoint.sh
  run_inherited_gate ./scripts/v02-proposal-registry-stabilization-gate.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

./scripts/v02-request-pack-final-no-go-regression.sh

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-133" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-133: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-133 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-133 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-133 must not add or change SDK resources or CLI implementations" >&2
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
    root / "examples/release/v02-request-pack-final-review.json",
    root / "examples/release/v02-evidence-boundary-closeout.json",
    root / "examples/release/v02-preapproval-submission-gate.json",
    root / "examples/release/v02-request-approval-guard.json",
    root / "examples/release/v02-final-submission-evidence-matrix.json",
    root / "operator-console-static/demo-data/v02-request-pack-final-review.json",
    root / "operator-console-static/demo-data/v02-preapproval-submission-gate.json",
]
false_keys = {
    "request_pack_approval",
    "submission_approval",
    "request_package_implementation_approved",
    "proposal_template_implementation_approved",
    "approval_evidence_approval_true",
    "evidence_completeness_bypassed",
    "submission_freeze_bypassed",
    "preapproval_gate_bypassed",
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
    "api_runtime_execution_route_added",
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
            if key in {"implementation_approved", "approval_state", "implementation_state"} and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_false_keys(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    if payload.get("task_id") != "AION-133":
        raise SystemExit(f"{path} must identify AION-133")
    if payload.get("status") != "passed":
        raise SystemExit(f"{path} must be passed")
    if payload.get("synthetic") is not True:
        raise SystemExit(f"{path} must be synthetic")
    for key in (
        "v02_request_pack_final_review_passed",
        "evidence_boundary_closed_out",
        "preapproval_submission_gate_created",
        "request_pack_preview_only",
        "proposal_registry_preview_only",
        "approval_queue_preview_only",
    ):
        if payload.get(key) is not True:
            raise SystemExit(f"{path} must mark {key} true")
    assert_false_keys(payload, str(path))

for path in paths[-2:]:
    payload = json.loads(path.read_text())
    if payload.get("read_only") is not True:
        raise SystemExit(f"{path} must be read-only static data")
    if payload.get("redaction_applied") is not True:
        raise SystemExit(f"{path} must mark redaction applied")

matrix = json.loads((root / "examples/release/v02-final-submission-evidence-matrix.json").read_text())
if len(matrix.get("matrix", [])) != 5:
    raise SystemExit("final submission evidence matrix must contain five rows")

print("AION-133 JSON examples valid")
PY

cat <<'SUMMARY'
v0.2 request pack final review result:
- v02_request_pack_final_review_passed: true
- evidence_boundary_closed_out: true
- preapproval_submission_gate_created: true
- request_pack_preview_only: true
- proposal_registry_preview_only: true
- approval_queue_preview_only: true
- request_pack_approval: false
- submission_approval: false
- preapproval_gate_bypassed: false
- runtime_implementation_approved: false
- v02_tag_created: false
- v02_release_created: false
v0.2 request pack final review PASS
SUMMARY
