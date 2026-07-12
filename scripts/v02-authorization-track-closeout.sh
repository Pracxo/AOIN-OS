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
  [[ "${AION_V02_AUTHORIZATION_TRACK_CLOSEOUT_SKIP_INHERITED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 "$@"
}

required_docs=(
  docs/release/v02-authorization-track-closeout-report.md
  docs/release/v02-approval-chain-master-evidence.md
  docs/release/v02-runtime-enablement-master-lock.md
  docs/release/v02-explicit-approval-record-master-ledger.md
  docs/release/v02-implementation-authorization-final-status.md
  docs/release/v02-authorization-track-closeout-no-go.md
  docs/release/v02-authorization-track-closeout-checklist.md
  docs/adr/0141-v02-authorization-track-closeout.md
)

required_examples=(
  examples/release/v02-authorization-track-closeout-report.json
  examples/release/v02-approval-chain-master-evidence.json
  examples/release/v02-runtime-enablement-master-lock.json
  examples/release/v02-explicit-approval-record-master-ledger.json
  examples/release/v02-implementation-authorization-final-status.json
  operator-console-static/demo-data/v02-authorization-track-closeout.json
  operator-console-static/demo-data/v02-runtime-enablement-master-lock.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-150 authorization track closeout artifact: $file" >&2
    exit 1
  }
done

grep -q "0141-v02-authorization-track-closeout.md" docs/adr/README.md || {
  echo "ADR 0141 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 authorization track closeout inherited gates deferred to outer aggregate gate"
else
  run_inherited_gate ./scripts/v02-implementation-authorization-final-review.sh
  run_inherited_gate ./scripts/v02-runtime-enablement-guard-final-freeze.sh
  ./scripts/v02-implementation-authorization-final-no-go-regression.sh
  run_inherited_gate ./scripts/v02-implementation-authorization-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-implementation-authorization-preview-check.sh
  run_inherited_gate ./scripts/v02-runtime-approval-board-final-review.sh
  run_inherited_gate ./scripts/v02-approval-docket-final-review.sh
  run_inherited_gate ./scripts/v02-decision-package-final-review.sh
  run_inherited_gate ./scripts/v02-review-board-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-request-pack-final-review.sh
  run_inherited_gate ./scripts/v02-planning-track-closeout.sh
  run_inherited_gate ./scripts/v02-final-planning-release-gate.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

./scripts/v02-authorization-track-closeout-no-go-regression.sh

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-150" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-150: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-150 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-150 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-150 must not add or change SDK resources or CLI implementations" >&2
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
    root / "examples/release/v02-authorization-track-closeout-report.json",
    root / "examples/release/v02-approval-chain-master-evidence.json",
    root / "examples/release/v02-runtime-enablement-master-lock.json",
    root / "examples/release/v02-explicit-approval-record-master-ledger.json",
    root / "examples/release/v02-implementation-authorization-final-status.json",
    root / "operator-console-static/demo-data/v02-authorization-track-closeout.json",
    root / "operator-console-static/demo-data/v02-runtime-enablement-master-lock.json",
]
true_keys = {
    "v02_authorization_track_closeout_passed",
    "authorization_governance_baseline_complete",
    "implementation_authorization_preview_only",
    "explicit_approval_record_created",
    "runtime_enablement_master_lock_created",
    "runtime_enablement_guard_created",
    "runtime_enablement_guard_final_lock_created",
    "implementation_no_go_status",
}
false_keys = {
    "implementation_authorization_approved",
    "implementation_authorization_stabilization_approval",
    "implementation_authorization_final_review_approval",
    "explicit_approval_record_approval",
    "explicit_approval_record_freeze_approval",
    "explicit_approval_record_closeout_approval",
    "runtime_enablement_master_lock_release_approved",
    "runtime_enablement_guard_release_approved",
    "runtime_enablement_guard_final_lock_release_approved",
    "runtime_approval_board_decision_approved",
    "runtime_approval_board_final_review_approval",
    "approval_vote_record_approval",
    "approval_vote_record_closeout_approval",
    "approval_vote_record_runtime_effect",
    "implementation_go_status",
    "implementation_go_final_approval",
    "go_no_go_ledger_runtime_effect",
    "approval_docket_item_approved",
    "implementation_decision_record_approval",
    "implementation_decision_record_closeout_approval",
    "runtime_approval_review_approved",
    "runtime_approval_lock_release_approved",
    "decision_package_approval",
    "approval_readiness_approved",
    "review_board_decision_approval",
    "routing_decision_approval",
    "reviewer_signoff_implementation_approval",
    "request_pack_approval",
    "submission_approval",
    "preapproval_queue_item_approved",
    "runtime_implementation_approved",
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
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
}
content_safety = {
    "no secrets",
    "no tokens",
    "no credentials",
    "no endpoints",
    "no raw prompts",
    "no hidden reasoning",
}

for path in paths:
    payload: dict[str, Any] = json.loads(path.read_text())
    if payload.get("task_id") != "AION-150":
        raise SystemExit(f"{path} must identify AION-150")
    if payload.get("synthetic") is not True:
        raise SystemExit(f"{path} must be synthetic")
    if payload.get("read_only") is not True:
        raise SystemExit(f"{path} must be read-only")
    for key in true_keys:
        if payload.get(key) is not True:
            raise SystemExit(f"{key} must be true in {path}")
    for key in false_keys:
        if payload.get(key) is not False:
            raise SystemExit(f"{key} must be false in {path}")
    if not content_safety <= set(payload.get("content_safety", [])):
        raise SystemExit(f"{path} content safety markers are incomplete")
PY

cat <<'SUMMARY'
v0.2 authorization track closeout result:
- authorization governance baseline complete: true
- runtime implementation approved: false
- implementation authorization approved: false
- explicit approval record approval: false
- runtime enablement guard release approved: false
- runtime enablement master-lock release approved: false
- implementation go status: false
- implementation no-go status: true
- external calls added: false
- credential or token storage added: false
- sandbox execution added: false
- v0.2 tag created: false
- v0.2 release created: false
v0.2 authorization track closeout PASS
SUMMARY
