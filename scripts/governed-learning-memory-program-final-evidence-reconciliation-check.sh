#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from governed_learning_memory_program_final_evaluation import EVALUATION_ID, PASS_DECISION

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/governed-learning-memory/authorization-ledger.json").read_text(encoding="utf-8"))
delivery = program.get("aion_229_delivery", {})
reconciliation = delivery.get("evidence_reconciliation", {})

if program.get("program_state") != "governed_learning_memory_program_complete":
    raise SystemExit("program is not complete")
if program.get("governed_learning_memory_program_complete") is not True:
    raise SystemExit("program complete flag false")
if program.get("governed_learning_memory_program_evaluation_id") != EVALUATION_ID:
    raise SystemExit("final evaluation id mismatch")
if program.get("governed_learning_memory_program_evaluation_decision") != PASS_DECISION:
    raise SystemExit("final evaluation decision mismatch")
if auth.get("active_authorizations") != []:
    raise SystemExit("active authorizations remain")
for key in (
    "active_glm_implementation_authorization",
    "active_glm_implementation_task",
    "formal_closeout_task",
    "next_glm_implementation_authorization",
    "next_glm_implementation_task",
):
    if program.get(key) is not None or auth.get(key) is not None:
        raise SystemExit(f"pending field remains: {key}")
if program.get("final_completed_task") != "AION-229":
    raise SystemExit("final completed task mismatch")
required_delivery = {
    "task_id": "AION-229",
    "branch": "phase/governed-learning-memory-program-final-evaluation-closeout",
    "ci_result": "pass",
    "evaluation_id": EVALUATION_ID,
    "evaluation_decision": PASS_DECISION,
    "authorization_transaction": None,
    "authorization_state": "no_active_glm_authorization",
    "next_task": None,
    "runtime_state": "governed_learning_memory_program_complete",
}
for key, value in required_delivery.items():
    if delivery.get(key) != value:
        raise SystemExit(f"AION-229 delivery mismatch {key}: {delivery.get(key)!r}")
for key in (
    "harness_commit",
    "closeout_commit",
    "pull_requests",
    "merge_commits",
    "completion_timestamp",
):
    if not delivery.get(key):
        raise SystemExit(f"AION-229 delivery missing {key}")
for key in (
    "primary_pr",
    "primary_merge_commit",
    "primary_merged_at",
    "reconciliation_pr",
    "reconciliation_commit",
    "reconciliation_merge_commit",
    "reconciliation_merged_at",
    "final_main_sha",
    "final_origin_main_sha",
):
    if not reconciliation.get(key):
        raise SystemExit(f"AION-229 reconciliation missing {key}")
if reconciliation["final_main_sha"] != reconciliation["final_origin_main_sha"]:
    raise SystemExit("final main and origin/main differ in evidence")
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
origin = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=root, text=True).strip()
if head != origin:
    raise SystemExit("local HEAD is not origin/main")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "governed learning memory program final evidence reconciliation PASS"
