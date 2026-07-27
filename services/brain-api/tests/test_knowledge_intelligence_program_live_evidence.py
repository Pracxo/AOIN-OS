from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/knowledge_intelligence_program_final_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion220_live_evidence", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_committed_live_evidence_matches_aion219_counts() -> None:
    harness = _load_harness()
    evidence = json.loads(
        (
            REPO_ROOT
            / "examples/knowledge-intelligence/public-research-pilot-live-evidence-redacted.json"
        ).read_text(encoding="utf-8")
    )
    validated = harness.validate_live_evidence(evidence)
    assert validated["pilot_session_id"] == "aion-219-live-session-0001"
    assert validated["mode"] == "operator_invoked_live"
    assert validated["DNS_resolution_count"] == 4
    assert validated["public_https_request_count"] == 4
    assert validated["candidate_eligibility_statuses"] == ["eligible_for_operator_review"]
    assert validated["source_bodies_retained"] == 0
    assert validated["source_bodies_persisted"] == 0
    assert validated["automatic_promotions"] == 0
    assert validated["cognitive_memory_writes"] == 0
    assert validated["belief_mutations"] == 0
    assert validated["persistent_verified_knowledge_writes"] == 0
    assert validated["protected_material_absent"] is True
