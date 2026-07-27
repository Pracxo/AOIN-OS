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
export AION_KI_PROGRAM_FINAL_EVALUATION_CHECK_RUNNING=1

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 "$@"
}

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

require_ancestor() {
  local commit="$1"
  if git_ref_exists origin/main; then
    git merge-base --is-ancestor "$commit" origin/main
  else
    git merge-base --is-ancestor "$commit" HEAD
  fi
}

./scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh
require_ancestor 756c706299472d6f048acd4a2c6a523c36f0e119
require_ancestor d0e1807edd7b3098ce62f8d00b0bceb4ee6fd23d

if grep -RInE 'actions/(checkout@v4|setup-python@v5)' .github/workflows; then
  echo "ERROR: deprecated Node 20-backed action remains" >&2
  exit 1
fi
test "$(grep -RhoE 'actions/(checkout|setup-python)@v6' .github/workflows | wc -l | tr -d ' ')" = "12"

tmp_dir="${TMPDIR:-/tmp}/aion-knowledge-intelligence-final-evaluation-check"
rm -rf "$tmp_dir"
mkdir -p "$tmp_dir"
PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
  "$ROOT_DIR/scripts/lib/knowledge_intelligence_program_final_evaluation.py" \
  --repo-root "$ROOT_DIR" \
  --evaluation-id AION-KIPE-001 \
  --evaluation-base-commit "$(git rev-parse HEAD)" \
  --temporary-output-directory "$tmp_dir" \
  --report "$tmp_dir/AION-KIPE-001.json"

if [[ -f examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json ]]; then
  PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
    "$ROOT_DIR/scripts/lib/knowledge_intelligence_program_final_evaluation.py" \
    --validate-report examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json
fi

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json
import os
from pathlib import Path
from knowledge_intelligence_program_final_evaluation import (
    AION219_FEATURE_COMMIT,
    AION219_MERGE_COMMIT,
    AION219_MERGED_AT,
    AION219_PR,
    AUTHORIZATION_ID,
    EVALUATION_ID,
    PASS_DECISION,
    validate_evaluation_report,
    validate_live_evidence,
)

root = Path(os.environ["AION_REPO_ROOT"])
live = json.loads((root / "examples/knowledge-intelligence/public-research-pilot-live-evidence-redacted.json").read_text(encoding="utf-8"))
validate_live_evidence(live)
program = json.loads((root / "docs/knowledge-intelligence/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/knowledge-intelligence/authorization-ledger.json").read_text(encoding="utf-8"))
aion219 = next(item for item in program["records"] if item.get("task_id") == "AION-219")
if aion219.get("feature_commits") != [AION219_FEATURE_COMMIT]:
    raise SystemExit("AION-219 feature commit evidence mismatch")
if aion219.get("pull_requests") != [AION219_PR]:
    raise SystemExit("AION-219 PR evidence mismatch")
if aion219.get("merge_commits") != [AION219_MERGE_COMMIT]:
    raise SystemExit("AION-219 merge evidence mismatch")
if aion219.get("completion_timestamp") != AION219_MERGED_AT:
    raise SystemExit("AION-219 timestamp mismatch")
if aion219.get("evaluation_id") not in {None, EVALUATION_ID}:
    raise SystemExit("AION-219 evaluation ID mismatch")
active = [item for item in auth["records"] if item.get("authorization_active") is True]
if auth["active_knowledge_implementation_authorization_count"] == 0:
    if active:
        raise SystemExit("active authorization record remains")
    closed = next(item for item in auth["records"] if item.get("authorization_transaction_id") == AUTHORIZATION_ID)
    if closed.get("authorization_consumed") is not True or closed.get("authorization_expired") is not True:
        raise SystemExit("AION-218-KI-0008 is not closed")
    if program.get("program_state") != "knowledge_intelligence_program_complete":
        raise SystemExit("program state is not complete")
else:
    if len(active) != 1 or active[0].get("authorization_transaction_id") != AUTHORIZATION_ID:
        raise SystemExit("unexpected active authorization before closeout")
if "examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json":
    path = root / "examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        validate_evaluation_report(payload)
        if payload["decision"] != PASS_DECISION:
            raise SystemExit("unexpected final evaluation decision")
PY

run_inherited_gate ./scripts/knowledge-intelligence-public-research-pilot-no-go-regression.sh
run_inherited_gate ./scripts/knowledge-intelligence-public-research-pilot-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-public-research-pilot-live-evidence-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-verified-memory-operator-evaluation-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-verified-knowledge-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-tool-verification-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-domain-expert-mesh-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-claim-graph-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-research-runtime-hold.sh

./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
./scripts/repo-health.sh

rm -rf "$tmp_dir"
aion_confirm_immutable_v01_tag_history >/dev/null

echo "knowledge intelligence program final evaluation PASS"
