from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_tool_verification_authorization_docs_exist() -> None:
    for relative in (
        "docs/knowledge-intelligence/tool-verification-fabric-architecture.md",
        "docs/knowledge-intelligence/tool-verification-fabric-boundary.md",
        "docs/knowledge-intelligence/tool-verification-policy.md",
        "docs/knowledge-intelligence/tool-verification-threat-model.md",
        "docs/release/knowledge-intelligence-tool-verification-authorization-transaction.md",
        "docs/release/knowledge-intelligence-tool-verification-explicit-approval-record.md",
        "docs/release/knowledge-intelligence-tool-verification-scope.md",
        "docs/release/knowledge-intelligence-tool-verification-runtime-hold.md",
        "docs/release/knowledge-intelligence-tool-verification-no-go.md",
        "docs/release/knowledge-intelligence-tool-verification-checklist.md",
        "docs/release/knowledge-intelligence-tool-verification-evidence-matrix.md",
        "docs/adr/0178-domain-expert-mesh-evaluation-and-tool-verification-authorization.md",
    ):
        assert (REPO_ROOT / relative).is_file(), relative


def test_adr_0178_is_indexed() -> None:
    index = (REPO_ROOT / "docs/adr/README.md").read_text(encoding="utf-8")
    assert "0178-domain-expert-mesh-evaluation-and-tool-verification-authorization.md" in index
