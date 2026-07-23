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
  [[ "${AION_KNOWLEDGE_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-research-plane-check.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import subprocess
from pathlib import Path

root = Path(".")
program = json.loads((root / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((root / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
record = auth["records"][0]
assert program["research_plane_implemented"] is True
assert program["research_plane_state"] == "implemented_operator_invoked_disabled"
for key in (
    "research_runtime_enabled",
    "network_access_enabled",
    "public_network_fetch_available",
    "background_crawler_enabled",
    "scheduled_research_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "knowledge_promotion_enabled",
    "automatic_belief_creation_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "runtime_effect",
):
    assert program[key] is False, key
assert record["authorization_active"] is True
assert record["authorization_consumed"] is False
assert record["authorization_reusable"] is False
assert record["system_http_transport_available"] is False
assert (root / "services/brain-api/src/aion_brain/knowledge_intelligence").is_dir()
assert (root / "services/brain-api/src/aion_brain/contracts/knowledge_research.py").is_file()
assert (
    subprocess.check_output(["git", "rev-parse", "aion-v0.1.0^{commit}"], text=True).strip()
    == "105fe29348160a2218ac095cfffadcb6f234421f"
)
assert subprocess.check_output(["git", "tag", "--list", "v0.2*", "aion-v0.2*"], text=True).strip() == ""
PY

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "knowledge intelligence research runtime hold PASS"
