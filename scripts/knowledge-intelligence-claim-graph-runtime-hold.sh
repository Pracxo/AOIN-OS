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
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CLAIM_GRAPH_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  return 1
}

if is_nested_gate_context; then
  echo "PASS: claim graph implementation check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-claim-graph-check.sh
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
if active[0]["authorization_transaction_id"] == "AION-208-KI-0003":
    claim = active[0]
else:
    assert active[0]["authorization_transaction_id"] == "AION-210-KI-0004"
    matches = [
        record
        for record in auth["records"]
        if record.get("authorization_transaction_id") == "AION-208-KI-0003"
    ]
    assert len(matches) == 1
    claim = matches[0]
    assert claim["authorization_active"] is False
    assert claim["authorization_consumed"] is True
    assert claim["authorization_expired"] is True
    assert claim["authorization_closed_by_task"] == "AION-210"
assert claim["authorization_transaction_id"] == "AION-208-KI-0003"
assert program["temporal_claim_evidence_graph_implemented"] is True
assert program["persistent_claim_graph_write_enabled"] is False
assert program["claim_graph_runtime_enabled"] is False
for key in (
    "graph_database_enabled",
    "automatic_claim_extraction_enabled",
    "source_body_parsing_enabled",
    "claim_verification_enabled",
    "truth_decision_enabled",
    "epistemic_confidence_enabled",
    "contradiction_resolution_enabled",
    "knowledge_promotion_enabled",
    "belief_mutation_enabled",
    "network_access_enabled",
    "runtime_effect",
):
    assert program.get(key, False) is False, key
    assert claim.get(key, False) is False, key
assert claim["resource_limits"]["maximum_graph_write_batch"] == 0
assert not (root / "services/brain-api/src/aion_brain/api/claim_graph.py").exists()
assert not (root / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_runtime.py").exists()
PY

if rg -n 'claim_graph_runtime_enabled[[:space:]]*=|persistent_claim_graph_write_enabled[[:space:]]*=|graph_database_enabled[[:space:]]*=|startup|scheduler|background worker|BackgroundTasks|sqlite3|aiosqlite|sqlalchemy|create_engine|APIRouter|FastAPI|@router|@app' \
  services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph*.py; then
  echo "ERROR: claim graph runtime, scheduler, database, or persistent write surface detected" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "v0.2 release exists" >&2
    exit 1
  fi
fi

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "knowledge intelligence claim graph runtime hold PASS"
