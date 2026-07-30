#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
export AION_GLM_PROGRAM_FINAL_EVALUATION_CHECK_RUNNING=1

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 "$@"
}

./scripts/governed-learning-memory-program-final-evaluation-no-go-regression.sh

if grep -RInE 'actions/(checkout@v4|setup-python@v5)' .github/workflows; then
  echo "ERROR: deprecated Node 20-backed action remains" >&2
  exit 1
fi
test "$(grep -RhoE 'actions/(checkout|setup-python)@v6' .github/workflows | wc -l | tr -d ' ')" = "12"

tmp_dir="${TMPDIR:-/tmp}/aion-glm-program-final-evaluation-check"
rm -rf "$tmp_dir"
mkdir -m 700 "$tmp_dir"
PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
  "$ROOT_DIR/scripts/lib/governed_learning_memory_program_final_evaluation.py" \
  --repo-root "$ROOT_DIR" \
  --evaluation-id AION-GLMPE-004 \
  --evaluation-base-commit "$(git rev-parse HEAD)" \
  --live-evidence "$ROOT_DIR/examples/governed-learning-memory/controlled-local-continual-learning-live-pilot-evidence.json" \
  --temporary-output-directory "$tmp_dir" \
  --report "$tmp_dir/AION-GLMPE-004.json"

if [[ -f examples/governed-learning-memory/program-final-evaluation-report.json ]]; then
  PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
    "$ROOT_DIR/scripts/lib/governed_learning_memory_program_final_evaluation.py" \
    --validate-report examples/governed-learning-memory/program-final-evaluation-report.json
fi

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json
import os
from pathlib import Path
from governed_learning_memory_program_final_evaluation import (
    AION228_FEATURE_COMMIT,
    AION228_MERGE_COMMIT,
    AION228_MERGED_AT,
    AION228_PR,
    EVALUATION_ID,
    PASS_DECISION,
    validate_evaluation_report,
    validate_live_evidence,
)

root = Path(os.environ["AION_REPO_ROOT"])
live = json.loads((root / "examples/governed-learning-memory/controlled-local-continual-learning-live-pilot-evidence.json").read_text(encoding="utf-8"))
validate_live_evidence(live, repo_root=root)
program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text(encoding="utf-8"))
aion228 = program["aion_228_delivery"]
if aion228.get("feature_commits") not in ([], [AION228_FEATURE_COMMIT]):
    raise SystemExit("AION-228 feature commit evidence mismatch")
if aion228.get("pull_requests") not in ([], [AION228_PR]):
    raise SystemExit("AION-228 PR evidence mismatch")
if aion228.get("merge_commits") not in ([], [AION228_MERGE_COMMIT]):
    raise SystemExit("AION-228 merge evidence mismatch")
if aion228.get("completion_timestamp") not in (None, AION228_MERGED_AT):
    raise SystemExit("AION-228 timestamp mismatch")
path = root / "examples/governed-learning-memory/program-final-evaluation-report.json"
if path.exists():
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_evaluation_report(payload)
    if payload["evaluation_id"] != EVALUATION_ID or payload["decision"] != PASS_DECISION:
        raise SystemExit("unexpected AION-229 final evaluation decision")
PY

run_inherited_gate ./scripts/governed-learning-memory-continual-learning-pilot-no-go-regression.sh
run_inherited_gate ./scripts/governed-learning-memory-continual-learning-pilot-check.sh
run_inherited_gate ./scripts/governed-learning-memory-continual-learning-live-pilot-evidence-check.sh

rm -rf "$tmp_dir"

echo "governed learning memory program final evaluation PASS"
