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
  [[ "${AION_SOURCE_REGISTRY_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-source-registry-authorization-check.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
assert len(active) == 1
record = active[0]
assert record["authorization_transaction_id"] == "AION-206-KI-0002"
assert program["source_provenance_registry_authorized"] is True
assert program["source_provenance_registry_implemented"] is False
for key in (
    "research_runtime_enabled",
    "network_access_enabled",
    "public_network_fetch_available",
    "source_body_persistence_enabled",
    "claim_verification_enabled",
    "knowledge_promotion_enabled",
    "belief_mutation_enabled",
    "background_crawler_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
    "automatic_merge_enabled",
    "deployment_enabled",
    "model_weight_training_enabled",
    "runtime_effect",
):
    assert program[key] is False, key
    assert record[key] is False, key
tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
for path in tracked:
    suffix = Path(path).suffix.lower()
    if suffix in {".db", ".sqlite", ".sqlite3"}:
        raise SystemExit(f"tracked runtime persistence file is not allowed: {path}")
PY

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "knowledge intelligence source registry runtime hold PASS"
