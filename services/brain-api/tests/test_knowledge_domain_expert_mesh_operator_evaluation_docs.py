from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PASS_DECISION = (
    "DOMAIN_EXPERT_MESH_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TOOL_VERIFICATION_FABRIC_AUTHORIZATION"
)


def _load(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_domain_expert_mesh_operator_evaluation_report_is_exact_pass() -> None:
    report = _load(
        "examples/knowledge-intelligence/domain-expert-mesh-operator-evaluation-report.json"
    )

    assert report["evaluation_id"] == "AION-DEME-001"
    assert report["decision"] == PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert len(report["scenario_results"]) == 28
    assert all(item["passed"] is True for item in report["scenario_results"])
    assert all(item["passed"] is True for item in report["hard_gate_results"])
    assert report["synthetic"] is True
    assert report["read_only"] is True
    assert report["redacted"] is True
    assert report["report_is_approval"] is False


def test_domain_expert_mesh_operator_evaluation_docs_exist() -> None:
    for relative in (
        "docs/knowledge-intelligence/domain-expert-mesh-operator-evaluation-closeout.md",
        "docs/knowledge-intelligence/domain-expert-mesh-operator-evaluation-report.md",
        "docs/knowledge-intelligence/domain-expert-mesh-evaluation-scenarios.md",
        "docs/release/knowledge-intelligence-domain-expert-mesh-evaluation-closeout.md",
        "docs/release/knowledge-intelligence-domain-expert-mesh-evaluation-checklist.md",
        "docs/release/knowledge-intelligence-domain-expert-mesh-evaluation-evidence-matrix.md",
        "docs/release/knowledge-intelligence-domain-expert-mesh-evaluation-runtime-hold.md",
    ):
        assert (REPO_ROOT / relative).is_file(), relative
