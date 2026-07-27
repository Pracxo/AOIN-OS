from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_public_research_pilot_docs_examples_and_release_evidence_exist() -> None:
    for relative in (
        "docs/knowledge-intelligence/public-research-pilot-architecture.md",
        "docs/knowledge-intelligence/public-research-pilot-boundary.md",
        "docs/knowledge-intelligence/public-research-pilot-network-policy.md",
        "docs/knowledge-intelligence/public-research-pilot-dns-pinning.md",
        "docs/knowledge-intelligence/public-research-pilot-tls-policy.md",
        "docs/knowledge-intelligence/public-research-pilot-redirect-policy.md",
        "docs/knowledge-intelligence/public-research-pilot-threat-model.md",
        ("docs/release/knowledge-intelligence-public-research-pilot-authorization-transaction.md"),
        "examples/knowledge-intelligence/public-research-pilot-authorization.json",
        "examples/knowledge-intelligence/public-research-pilot-runtime-hold.json",
        (
            "operator-console-static/demo-data/"
            "knowledge-intelligence-public-research-pilot-authorization.json"
        ),
    ):
        assert (REPO_ROOT / relative).is_file(), relative
