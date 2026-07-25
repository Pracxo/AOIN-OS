from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_domain_expert_mesh_panel_policy_requires_independent_core_roles():
    panel = json.loads(
        (REPO_ROOT / "examples/knowledge-intelligence/expert-panel-plan.json").read_text()
    )
    assert "domain_analyst" in panel["required_roles"]
    assert "evidence_auditor" in panel["required_roles"]
    assert "methodological_skeptic" in panel["required_roles"]
    assert "risk_reviewer" in panel["required_roles"]
    assert panel["panel_size"] <= panel["maximum_panel_size"]
    assert panel["independence_group_count"] == 4
    assert panel["panel_size_confidence_amplification_enabled"] is False
    assert panel["majority_alignment_establishes_truth"] is False
    assert panel["dissent_preservation_required"] is True
    assert panel["self_review_rejected"] is True
    assert panel["circular_critique_rejected"] is True
