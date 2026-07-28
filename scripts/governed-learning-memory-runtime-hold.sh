#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_GLM_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/governed-learning-memory-promotion-transaction-check.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text(encoding="utf-8"))
runtime = json.loads((root / "examples/governed-learning-memory/runtime-hold.json").read_text(encoding="utf-8"))
static = json.loads((root / "operator-console-static/demo-data/governed-learning-memory-runtime-hold.json").read_text(encoding="utf-8"))

for label, payload in (("program", program), ("runtime", runtime), ("static", static)):
    if payload.get("program_id") != "AION-GOVERNED-LEARNING-MEMORY-001":
        raise SystemExit(f"{label} program mismatch")

required_false = [
    "runtime_enabled",
    "persistent_knowledge_write_enabled",
    "cognitive_memory_write_enabled",
    "cognitive_belief_mutation_enabled",
    "automatic_knowledge_promotion_enabled",
    "engagement_factual_effect_enabled",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
]
for key in required_false:
    if runtime.get(key) is not False:
        raise SystemExit(f"runtime hold flag must remain false: {key}")
if runtime.get("network_calls_enabled") is not False:
    raise SystemExit("network must remain disabled")
if runtime.get("aion_222_source_present") is not True:
    raise SystemExit("AION-222 source must be present")
if runtime.get("knowledge_promotion_transaction_core_implemented") is not True:
    raise SystemExit("AION-222 implementation flag missing")
if runtime.get("knowledge_promotion_transaction_core_state") != "implemented_deterministic_approval_bound_dry_run_in_memory_persistent_write_disabled":
    raise SystemExit("AION-222 implementation state mismatch")
if program.get("active_glm_implementation_authorization") != "AION-221-GLM-0001":
    raise SystemExit("GLM authorization missing")
if program.get("active_glm_implementation_task") != "AION-222":
    raise SystemExit("AION-222 is not the active GLM task")
PY

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "governed learning memory runtime hold PASS"
