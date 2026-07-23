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
  [[ "${AION_SOURCE_REGISTRY_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-source-registry-check.sh

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
    "research_runtime_enabled",
    "network_access_enabled",
    "public_network_fetch_available",
    "background_crawler_enabled",
    "scheduled_research_enabled",
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
    if suffix in {".db", ".sqlite", ".sqlite3", ".jsonl"}:
        raise SystemExit(f"tracked runtime persistence file is not allowed: {path}")
for relative in (
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_service.py",
    "services/brain-api/src/aion_brain/api/source_registry.py",
):
    assert not (ROOT / relative).exists(), relative
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.'; then
  echo "v0.2 tag exists" >&2
  exit 1
fi
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

echo "knowledge intelligence source registry runtime hold PASS"
