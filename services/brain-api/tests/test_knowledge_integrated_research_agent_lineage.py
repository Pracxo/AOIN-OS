from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py"
)


def _load_validator():
    sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_integrated_lineage_has_all_required_fingerprints() -> None:
    payload = _load_json("examples/knowledge-intelligence/integrated-knowledge-lineage.json")[
        "lineage"
    ]
    for key in (
        "research_plan_id",
        "acquisition_result_fingerprint",
        "source_snapshot_fingerprints",
        "provenance_fingerprints",
        "citation_fingerprints",
        "source_registry_integrity_fingerprint",
        "claim_identity_fingerprint",
        "claim_graph_integrity_fingerprint",
        "epistemic_assessment_fingerprint",
        "domain_mesh_session_fingerprint",
        "synthesis_fingerprint",
        "tool_verification_session_fingerprint",
        "attestation_chain_head",
        "integrated_trace_fingerprint",
        "sensitivity_trace_fingerprint",
    ):
        assert payload[key]
    assert payload["lineage_complete"] is True
    assert payload["references_resolve"] is True
    assert payload["deterministic_order"] is True
    assert payload["integrated_trace_fingerprint"] != payload["sensitivity_trace_fingerprint"]
    assert payload["source_body_included"] is False
    assert payload["raw_prompt_included"] is False
    assert payload["hidden_reasoning_included"] is False
