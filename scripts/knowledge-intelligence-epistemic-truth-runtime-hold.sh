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
  [[ "${AION_EPISTEMIC_TRUTH_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-epistemic-assessment-check.sh

"$PYTHON_BIN" - <<'PYSCRIPT'
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
runtime = json.loads((ROOT / "examples/knowledge-intelligence/epistemic-assessment-runtime-hold.json").read_text())
payload = runtime["payload"]
assert program["epistemic_truth_engine_implemented"] is True
assert program["epistemic_truth_engine_runtime_enabled"] is False
assert program["persistent_assessment_write_enabled"] is False
assert program["assessment_database_enabled"] is False
assert program["absolute_truth_oracle_enabled"] is False
assert program["automatic_claim_acceptance_enabled"] is False
assert program["automatic_claim_rejection_enabled"] is False
assert program["contradiction_resolution_enabled"] is False
assert program["knowledge_promotion_enabled"] is False
assert program["cognitive_belief_mutation_enabled"] is False
assert program["network_access_enabled"] is False
assert program["runtime_effect"] is False
assert payload["epistemic_truth_engine_implemented"] is True
assert payload["epistemic_truth_engine_runtime_enabled"] is False
assert payload["persistent_assessment_write_enabled"] is False
assert payload["assessment_database_enabled"] is False
assert payload["background_assessment_worker_enabled"] is False
assert payload["api_route_enabled"] is False
assert payload["installed_cli_command_enabled"] is False
assert payload["network_access_enabled"] is False
assert payload["runtime_effect"] is False
assert not (ROOT / "services/brain-api/src/aion_brain/api/epistemic_assessment.py").exists()
assert not (ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_runtime.py").exists()
assert not (ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/absolute_truth.py").exists()
assert not (ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py").exists()
assert not (ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/belief_mutation.py").exists()
PYSCRIPT

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

echo "knowledge intelligence epistemic truth runtime hold PASS"
