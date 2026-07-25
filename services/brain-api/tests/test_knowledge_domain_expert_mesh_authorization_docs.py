from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_domain_expert_mesh_required_docs_exist_and_record_boundaries():
    docs = (
        "domain-expert-mesh-architecture.md",
        "domain-expert-mesh-boundary.md",
        "domain-taxonomy-model.md",
        "domain-expert-profile-model.md",
        "domain-expert-case-model.md",
        "domain-expert-routing-model.md",
        "domain-expert-panel-policy.md",
        "domain-expert-independence.md",
        "domain-expert-report-model.md",
        "domain-expert-critique-model.md",
        "domain-expert-disagreement-model.md",
        "domain-expert-synthesis-policy.md",
        "domain-expert-high-stakes-policy.md",
        "domain-expert-resource-budgets.md",
        "domain-expert-threat-model.md",
        "domain-expert-mesh-roadmap.md",
    )
    for name in docs:
        text = (REPO_ROOT / "docs/knowledge-intelligence" / name).read_text()
        assert "AION-212-KI-0005" in text
        assert "Runtime effect: `false`" in text


def test_domain_expert_mesh_release_evidence_exists():
    release_docs = (
        "knowledge-intelligence-domain-expert-mesh-authorization-transaction.md",
        "knowledge-intelligence-domain-expert-mesh-explicit-approval-record.md",
        "knowledge-intelligence-domain-expert-mesh-scope.md",
        "knowledge-intelligence-domain-expert-mesh-runtime-hold.md",
        "knowledge-intelligence-domain-expert-mesh-no-go.md",
        "knowledge-intelligence-domain-expert-mesh-checklist.md",
        "knowledge-intelligence-domain-expert-mesh-evidence-matrix.md",
    )
    for name in release_docs:
        text = (REPO_ROOT / "docs/release" / name).read_text()
        assert "AION-212-KI-0005" in text
        assert "AION-213" in text
