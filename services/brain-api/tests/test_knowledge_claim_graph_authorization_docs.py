from __future__ import annotations

import os
import subprocess

from knowledge_source_registry_test_helpers import ROOT, read_json, read_text

REQUIRED_FILES = [
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-architecture.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-boundary.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-data-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-relations.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-time-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-jurisdiction-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-version-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-resource-budgets.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-threat-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-roadmap.md",
    "docs/release/knowledge-intelligence-claim-graph-authorization-transaction.md",
    "docs/release/knowledge-intelligence-claim-graph-explicit-approval-record.md",
    "docs/release/knowledge-intelligence-claim-graph-scope.md",
    "docs/release/knowledge-intelligence-claim-graph-runtime-hold.md",
    "docs/release/knowledge-intelligence-claim-graph-no-go.md",
    "docs/release/knowledge-intelligence-claim-graph-checklist.md",
    "docs/release/knowledge-intelligence-claim-graph-evidence-matrix.md",
    "docs/adr/0172-source-provenance-registry-evaluation-and-temporal-claim-evidence-graph-authorization.md",
    "examples/knowledge-intelligence/claim-graph-authorization.json",
    "examples/knowledge-intelligence/unverified-claim-assertion.json",
    "examples/knowledge-intelligence/claim-evidence-binding.json",
    "examples/knowledge-intelligence/claim-relation-edge.json",
    "examples/knowledge-intelligence/temporal-claim-evidence-graph.json",
    "examples/knowledge-intelligence/claim-graph-resource-budget.json",
    "examples/knowledge-intelligence/claim-graph-runtime-hold.json",
    "examples/knowledge-intelligence/claim-graph-operator-review-item.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-runtime-hold.json",
    "scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-claim-graph-authorization-check.sh",
    "scripts/knowledge-intelligence-claim-graph-runtime-hold.sh",
]


def test_claim_graph_authorization_required_files_exist():
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), relative
    assert "0172-source-provenance-registry-evaluation" in read_text("docs/adr/README.md")
    assert (
        read_json("examples/knowledge-intelligence/claim-graph-authorization.json")[
            "authorization_transaction_id"
        ]
        == "AION-208-KI-0003"
    )


def test_claim_graph_authorization_scripts_pass_in_nested_mode():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-208 claim graph smoke"}
    for script in (
        "scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-claim-graph-authorization-check.sh",
        "scripts/knowledge-intelligence-claim-graph-runtime-hold.sh",
    ):
        subprocess.run([str(ROOT / script)], cwd=ROOT, env=env, check=True)
