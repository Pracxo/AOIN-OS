from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_domain_expert_mesh_synthesis_preserves_uncertainty_and_dissent():
    synthesis = json.loads(
        (REPO_ROOT / "examples/knowledge-intelligence/expert-mesh-synthesis.json").read_text()
    )
    assert synthesis["alignment_state"] == "unresolved_disagreement"
    assert synthesis["explicit_abstention"] is True
    assert synthesis["operator_review_required"] is True
    assert synthesis["truth_decision"] is False
    assert synthesis["automatic_action"] is False
    assert synthesis["knowledge_promoted"] is False
    assert synthesis["belief_mutated"] is False
    assert synthesis["confidence_amplified"] is False
    assert Decimal(synthesis["synthesis_confidence_cap"]) <= Decimal(
        synthesis["underlying_assessment_confidence_cap"]
    )
    assert synthesis["runtime_effect"] is False


def test_disagreement_record_remains_unresolved_and_visible():
    disagreement = json.loads(
        (REPO_ROOT / "examples/knowledge-intelligence/expert-disagreement-item.json").read_text()
    )
    assert disagreement["unresolved"] is True
    assert disagreement["resolution_attempted"] is False
    assert disagreement["dissent_preserved"] is True
    assert disagreement["minority_report_deleted"] is False
    assert disagreement["runtime_effect"] is False
