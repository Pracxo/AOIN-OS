#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CLAIM_GRAPH_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  return 1
}

if is_nested_gate_context; then
  echo "PASS: inherited claim graph authorization check deferred to outer gate"
else
  ./scripts/knowledge-intelligence-claim-graph-authorization-check.sh
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

root = Path(".")
program = json.loads((root / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((root / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
assert len(active) == 1
claim = active[0]
assert claim["authorization_transaction_id"] == "AION-208-KI-0003"
for key in (
    "temporal_claim_evidence_graph_implemented",
    "temporal_claim_graph_runtime_enabled",
    "persistent_claim_graph_write_enabled",
    "claim_graph_persistent_write_enabled",
    "graph_database_enabled",
    "automatic_claim_extraction_enabled",
    "source_body_parsing_enabled",
    "claim_verification_enabled",
    "truth_decision_enabled",
    "epistemic_confidence_enabled",
    "knowledge_promotion_enabled",
    "belief_mutation_enabled",
    "network_access_enabled",
    "runtime_effect",
):
    assert program.get(key, False) is False, key
    assert claim.get(key, False) is False, key
assert claim["resource_limits"]["maximum_graph_write_batch"] == 0
PY

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "knowledge intelligence claim graph runtime hold PASS"
