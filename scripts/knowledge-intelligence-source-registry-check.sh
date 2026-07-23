#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-source-registry-no-go-regression.sh
./scripts/knowledge-intelligence-source-registry-authorization-check.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AUTH_ID = "AION-206-KI-0002"
STATE = "implemented_append_only_in_memory_replay_persistent_write_disabled"

required_files = [
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py",
    "docs/knowledge-intelligence/source-registry-implementation.md",
    "docs/knowledge-intelligence/source-registry-contracts.md",
    "docs/knowledge-intelligence/source-registry-record-envelope.md",
    "docs/knowledge-intelligence/source-registry-append-only-semantics.md",
    "docs/knowledge-intelligence/source-registry-in-memory-repository.md",
    "docs/knowledge-intelligence/source-registry-fixture-replay.md",
    "docs/knowledge-intelligence/source-registry-indexes-and-queries.md",
    "docs/knowledge-intelligence/source-registry-integrity-audit.md",
    "docs/knowledge-intelligence/source-registry-versioning.md",
    "docs/knowledge-intelligence/source-registry-security-review.md",
    "docs/knowledge-intelligence/source-registry-operator-runbook.md",
    "docs/knowledge-intelligence/aion-207-checklist.md",
    "docs/release/knowledge-intelligence-source-registry-implementation.md",
    "docs/release/knowledge-intelligence-source-registry-security-evidence.md",
    "docs/adr/0171-append-only-source-provenance-registry-core.md",
]
for relative in required_files:
    assert (ROOT / relative).is_file(), relative
for relative in (
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_service.py",
    "services/brain-api/src/aion_brain/api/source_registry.py",
):
    assert not (ROOT / relative).exists(), relative

contracts = importlib.import_module("aion_brain.contracts.knowledge_source_registry")
assert contracts.SOURCE_REGISTRY_BATCH_SCHEMA_VERSION == "aion-knowledge-source-registry-batch/v1"
assert contracts.SOURCE_REGISTRY_STATE_SCHEMA_VERSION == "aion-knowledge-source-registry-state/v1"
assert contracts.SOURCE_REGISTRY_INDEX_SCHEMA_VERSION == "aion-knowledge-source-registry-index/v1"
assert contracts.SOURCE_REGISTRY_INTEGRITY_SCHEMA_VERSION == "aion-knowledge-source-registry-integrity/v1"
assert contracts.SOURCE_REGISTRY_QUERY_SCHEMA_VERSION == "aion-knowledge-source-registry-query/v1"
assert contracts.SOURCE_REGISTRY_EVIDENCE_SCHEMA_VERSION == "aion-knowledge-source-registry-evidence/v1"
assert contracts.SOURCE_REGISTRY_FIXTURE_SCHEMA_VERSION == "aion-knowledge-source-registry-fixture/v1"

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
assert len(active) == 1
record = active[0]
assert program["program_state"] == "source_provenance_registry_implemented_write_disabled_pending_closeout"
assert program["active_knowledge_implementation_authorization"] == AUTH_ID
assert program["active_knowledge_implementation_authorization_count"] == 1
assert program["active_knowledge_implementation_task"] == "AION-207"
assert program["formal_closeout_task"] == "AION-208"
assert program["source_provenance_registry_implemented"] is True
assert program["source_provenance_registry_state"] == STATE
assert record["authorization_transaction_id"] == AUTH_ID
assert record["authorization_active"] is True
assert record["authorization_consumed"] is False
assert record["authorization_expired"] is False
assert record["authorization_reusable"] is False
assert record["resource_limits"]["maximum_registry_write_batch"] == 0
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

for path in sorted((ROOT / "examples/knowledge-intelligence").glob("source-registry*.json")):
    payload = json.loads(path.read_text())
    assert payload["synthetic"] is True, path
    assert payload["read_only"] is True, path
    assert payload["redacted"] is True, path
    assert payload["authorization_transaction_id"] == AUTH_ID, path
    assert payload["source_provenance_registry_implemented"] is True, path
    assert payload["source_registry_runtime_enabled"] is False, path
    assert payload["source_registry_persistent_write_enabled"] is False, path
    assert payload["source_body_persistence_enabled"] is False, path
    assert payload["claim_verification_enabled"] is False, path
    assert payload["knowledge_promotion_enabled"] is False, path
    assert payload["belief_mutation_enabled"] is False, path
    assert payload["runtime_effect"] is False, path
PY

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_source_registry_contracts.py \
  services/brain-api/tests/test_knowledge_source_registry_record_envelope.py \
  services/brain-api/tests/test_knowledge_source_registry_projection.py \
  services/brain-api/tests/test_knowledge_source_registry_budget.py \
  services/brain-api/tests/test_knowledge_source_registry_repository.py \
  services/brain-api/tests/test_knowledge_source_registry_fixture_replay.py \
  services/brain-api/tests/test_knowledge_source_registry_indexes.py \
  services/brain-api/tests/test_knowledge_source_registry_queries.py \
  services/brain-api/tests/test_knowledge_source_registry_integrity.py \
  services/brain-api/tests/test_knowledge_source_registry_versioning.py \
  services/brain-api/tests/test_knowledge_source_registry_idempotency.py \
  services/brain-api/tests/test_knowledge_source_registry_evidence.py \
  services/brain-api/tests/test_knowledge_source_registry_no_source_body.py \
  services/brain-api/tests/test_knowledge_source_registry_no_claim_verification.py \
  services/brain-api/tests/test_knowledge_source_registry_no_knowledge_promotion.py \
  services/brain-api/tests/test_knowledge_source_registry_no_belief_mutation.py \
  services/brain-api/tests/test_knowledge_source_registry_no_persistent_write.py \
  services/brain-api/tests/test_knowledge_source_registry_no_runtime_registration.py \
  services/brain-api/tests/test_knowledge_source_registry_determinism.py \
  services/brain-api/tests/test_knowledge_source_registry_concurrency.py \
  services/brain-api/tests/test_knowledge_source_registry_performance.py \
  -q

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-closeout-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

echo "knowledge intelligence source registry PASS"
