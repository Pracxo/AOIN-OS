from __future__ import annotations

import os
import subprocess

from knowledge_claim_graph_evaluation_test_helpers import (
    EPISTEMIC_AUTH_ID,
    ROOT,
    read_json,
    read_text,
)

REQUIRED_FILES = [
    "docs/knowledge-intelligence/epistemic-truth-engine-architecture.md",
    "docs/knowledge-intelligence/epistemic-truth-engine-boundary.md",
    "docs/knowledge-intelligence/epistemic-assessment-data-model.md",
    "docs/knowledge-intelligence/epistemic-corroboration-model.md",
    "docs/knowledge-intelligence/epistemic-contradiction-model.md",
    "docs/knowledge-intelligence/epistemic-freshness-model.md",
    "docs/knowledge-intelligence/epistemic-confidence-scorecard.md",
    "docs/knowledge-intelligence/epistemic-abstention-policy.md",
    "docs/knowledge-intelligence/epistemic-resource-budgets.md",
    "docs/knowledge-intelligence/epistemic-threat-model.md",
    "docs/knowledge-intelligence/epistemic-truth-engine-roadmap.md",
    "docs/release/knowledge-intelligence-epistemic-truth-authorization-transaction.md",
    "docs/release/knowledge-intelligence-epistemic-truth-explicit-approval-record.md",
    "docs/release/knowledge-intelligence-epistemic-truth-scope.md",
    "docs/release/knowledge-intelligence-epistemic-truth-runtime-hold.md",
    "docs/release/knowledge-intelligence-epistemic-truth-no-go.md",
    "docs/release/knowledge-intelligence-epistemic-truth-checklist.md",
    "docs/release/knowledge-intelligence-epistemic-truth-evidence-matrix.md",
    "docs/adr/0174-temporal-claim-evidence-graph-evaluation-and-epistemic-truth-engine-authorization.md",
    "examples/knowledge-intelligence/epistemic-truth-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-truth-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-runtime-hold.json",
    "scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh",
    "scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh",
]


def test_epistemic_truth_authorization_required_files_exist():
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), relative
    assert "0174-temporal-claim-evidence-graph-evaluation" in read_text("docs/adr/README.md")
    assert (
        read_json("examples/knowledge-intelligence/epistemic-truth-authorization.json")[
            "authorization_transaction_id"
        ]
        == EPISTEMIC_AUTH_ID
    )


def test_epistemic_truth_authorization_scripts_pass_in_nested_mode():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-210 epistemic truth docs"}
    for script in (
        "scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh",
        "scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh",
    ):
        subprocess.run([str(ROOT / script)], cwd=ROOT, env=env, check=True)
