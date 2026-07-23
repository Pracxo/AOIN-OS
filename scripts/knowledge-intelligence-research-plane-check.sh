#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
required = [
    "services/brain-api/src/aion_brain/contracts/knowledge_research.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_adapters.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_snapshot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_provenance.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_deduplication.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_budget.py",
]
for path in required:
    assert (ROOT / path).is_file(), path
for path in sorted((ROOT / "examples/knowledge-intelligence").glob("*.json")):
    data = json.loads(path.read_text())
    assert data["synthetic"] is True
    assert data["read_only"] is True
    assert data["redacted"] is True
    assert data["research_plane_implemented"] is True
    assert data["research_runtime_enabled"] is False
    assert data["network_access_enabled"] is False
program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
assert program["program_state"] in {
    "research_plane_implemented_disabled_pending_closeout",
    "source_provenance_registry_authorized_not_implemented",
}
assert program["research_plane_implemented"] is True
assert program["research_runtime_enabled"] is False
assert program["public_network_fetch_available"] is False
active = [record for record in auth["records"] if record.get("authorization_active") is True]
assert len(active) == 1
if program["program_state"] == "source_provenance_registry_authorized_not_implemented":
    assert auth["active_knowledge_implementation_authorization"] == "AION-206-KI-0002"
    assert auth["active_knowledge_implementation_task"] == "AION-207"
    closed = [
        record
        for record in auth["records"]
        if record.get("authorization_transaction_id") == "AION-204-KI-0001"
    ][0]
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_reusable"] is False
else:
    assert auth["active_knowledge_implementation_authorization"] == "AION-204-KI-0001"
    assert auth["active_knowledge_implementation_task"] == "AION-205"
    record = active[0]
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_reusable"] is False
    assert record["research_plane_implemented"] is True
    assert record["public_network_fetch_available"] is False
    assert record["system_http_transport_available"] is False
PY

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_research_contracts.py \
  services/brain-api/tests/test_knowledge_research_query.py \
  services/brain-api/tests/test_knowledge_research_plan.py \
  services/brain-api/tests/test_knowledge_research_url_policy.py \
  services/brain-api/tests/test_knowledge_research_domain_allowlist.py \
  services/brain-api/tests/test_knowledge_research_destination_policy.py \
  services/brain-api/tests/test_knowledge_research_redirect_policy.py \
  services/brain-api/tests/test_knowledge_research_content_policy.py \
  services/brain-api/tests/test_knowledge_research_character_encoding.py \
  services/brain-api/tests/test_knowledge_research_safe_headers.py \
  services/brain-api/tests/test_knowledge_research_budget.py \
  services/brain-api/tests/test_knowledge_research_search_adapters.py \
  services/brain-api/tests/test_knowledge_research_fetch_adapters.py \
  services/brain-api/tests/test_knowledge_research_local_fixture_adapter.py \
  services/brain-api/tests/test_knowledge_research_http_policy_adapter.py \
  services/brain-api/tests/test_knowledge_source_snapshot.py \
  services/brain-api/tests/test_knowledge_source_provenance.py \
  services/brain-api/tests/test_knowledge_source_deduplication.py \
  services/brain-api/tests/test_knowledge_research_citation_reference.py \
  services/brain-api/tests/test_knowledge_research_evidence.py \
  services/brain-api/tests/test_knowledge_research_service.py \
  services/brain-api/tests/test_knowledge_research_prompt_injection_boundary.py \
  services/brain-api/tests/test_knowledge_research_no_knowledge_promotion.py \
  services/brain-api/tests/test_knowledge_research_no_belief_mutation.py \
  services/brain-api/tests/test_knowledge_research_no_runtime_registration.py \
  services/brain-api/tests/test_knowledge_research_no_network_by_default.py \
  services/brain-api/tests/test_knowledge_research_determinism.py \
  services/brain-api/tests/test_knowledge_research_concurrency.py \
  services/brain-api/tests/test_knowledge_research_performance.py \
  -q

./scripts/knowledge-intelligence-research-plane-no-go-regression.sh
./scripts/knowledge-intelligence-research-authorization-check.sh
./scripts/cognitive-local-offline-pilot-closeout-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

echo "knowledge intelligence research plane PASS"
