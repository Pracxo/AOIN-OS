from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def public_auth() -> dict[str, object]:
    return load_json("examples/knowledge-intelligence/public-research-pilot-authorization.json")


def test_public_research_pilot_integrates_pipeline_without_promotion() -> None:
    auth = public_auth()
    for key in (
        "source_snapshot_creation_approved",
        "source_provenance_creation_approved",
        "source_registry_projection_approved",
        "claim_graph_projection_approved",
        "epistemic_assessment_pipeline_approved",
        "domain_expert_mesh_pipeline_approved",
        "simulation_only_tool_verification_pipeline_approved",
        "verified_candidate_evaluation_pipeline_approved",
    ):
        assert auth["authorized_capabilities"][key] is True
    assert auth["automatic_verified_knowledge_promotion_enabled"] is False
    assert auth["persistent_verified_knowledge_write_enabled"] is False
