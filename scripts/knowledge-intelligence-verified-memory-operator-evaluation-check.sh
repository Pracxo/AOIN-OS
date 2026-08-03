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

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_VERIFIED_MEMORY_OPERATOR_EVALUATION_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh
PYTHONPATH="$ROOT_DIR/scripts/lib:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json
import os
from pathlib import Path
from knowledge_intelligence_verified_memory_operator_evaluation import _validate_report
root = Path(os.environ["AION_REPO_ROOT"])
report = json.loads((root / "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json").read_text(encoding="utf-8"))
_validate_report(report)
closeout = report["authorization_closeout"]
if closeout.get("authorization_transaction_id") != "AION-216-KI-0007" or closeout.get("authorization_active") is not False:
    raise SystemExit("AION-216 closeout missing from report")
if report["decision"].endswith("PUBLIC_RESEARCH_PILOT_AUTHORIZATION"):
    print("knowledge intelligence verified memory operator evaluation PASS")
else:
    print("knowledge intelligence verified memory operator evaluation FAIL RECORDED")
PY

if is_nested_gate_context; then
  echo "PASS: inherited AION-218 downstream repository gates deferred to outer gate"
  exit 0
fi

export AION_VERIFIED_MEMORY_OPERATOR_EVALUATION_CHECK_RUNNING=1

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 "$@"
}

run_inherited_gate ./scripts/knowledge-intelligence-verified-knowledge-no-go-regression.sh
run_inherited_gate ./scripts/knowledge-intelligence-verified-knowledge-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-verified-knowledge-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-tool-verification-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-domain-expert-mesh-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-claim-graph-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-research-runtime-hold.sh
run_inherited_gate ./scripts/cognitive-local-offline-pilot-closeout-check.sh
run_inherited_gate ./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -v '^aion-v0\.2\.0-rc\.1$' | rg -n '.+'; then echo "ERROR: v0.2 tag exists" >&2; exit 1; fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then echo "ERROR: v0.2 release exists" >&2; exit 1; fi
fi
if [[ "${AION_VERIFIED_MEMORY_OPERATOR_EVALUATION_SKIP_FULL_CHECK:-}" == "1" ]]; then
  echo "PASS: full repository check explicitly deferred"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi
