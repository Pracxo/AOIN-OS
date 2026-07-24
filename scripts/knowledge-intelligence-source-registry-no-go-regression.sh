#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AION207_SOURCE = [
    ROOT / "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py",
    ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py",
    ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py",
]
for path in AION207_SOURCE:
    assert path.is_file(), path
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in {"update", "delete", "truncate", "compact", "overwrite", "save"}:
                raise SystemExit(f"prohibited mutating method in {path}: {node.name}")
        if isinstance(node, ast.Call):
            target = ""
            if isinstance(node.func, ast.Attribute):
                target = node.func.attr
            elif isinstance(node.func, ast.Name):
                target = node.func.id
            if target in {"open", "connect", "create_task", "run", "Popen"}:
                raise SystemExit(f"prohibited runtime call in {path}: {target}")

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
assert len(active) == 1
source = [
    record
    for record in auth["records"]
    if record.get("authorization_transaction_id") == "AION-206-KI-0002"
]
assert len(source) == 1
record = source[0]
assert program["source_provenance_registry_implemented"] is True
assert (
    program["source_provenance_registry_state"]
    == "implemented_append_only_in_memory_replay_persistent_write_disabled"
)
for key in (
    "source_registry_runtime_enabled",
    "source_registry_persistent_write_enabled",
    "source_body_persistence_enabled",
    "claim_verification_enabled",
    "knowledge_promotion_enabled",
    "belief_mutation_enabled",
    "network_access_enabled",
    "public_network_fetch_available",
    "runtime_effect",
):
    assert program[key] is False, key
    assert record[key] is False, key
assert record["resource_limits"]["maximum_registry_write_batch"] == 0
if record["authorization_active"] is True:
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
else:
    assert active[0]["authorization_transaction_id"] == "AION-208-KI-0003"
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_closed_by_task"] == "AION-208"
assert record["authorization_reusable"] is False
PY

echo "knowledge intelligence source registry no-go PASS"
