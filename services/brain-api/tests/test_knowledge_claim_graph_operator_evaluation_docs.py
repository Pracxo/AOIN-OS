from __future__ import annotations

import json
import os
import subprocess

from knowledge_claim_graph_evaluation_test_helpers import (
    DECISION,
    ROOT,
    evaluation_report,
    read_json,
)

REQUIRED_FILES = [
    "docs/knowledge-intelligence/claim-graph-operator-evaluation-closeout.md",
    "docs/knowledge-intelligence/claim-graph-operator-evaluation-report.md",
    "docs/knowledge-intelligence/claim-graph-evaluation-scenarios.md",
    "docs/release/knowledge-intelligence-claim-graph-evaluation-closeout.md",
    "docs/release/knowledge-intelligence-claim-graph-evaluation-checklist.md",
    "docs/release/knowledge-intelligence-claim-graph-evaluation-evidence-matrix.md",
    "docs/release/knowledge-intelligence-claim-graph-evaluation-runtime-hold.md",
    "examples/knowledge-intelligence/claim-graph-operator-evaluation-report.json",
    "examples/knowledge-intelligence/claim-graph-evaluation-scenario-summary.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-evaluation.json",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh",
]


def test_claim_graph_operator_evaluation_required_files_and_report():
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), relative
    report = evaluation_report()
    assert report["evaluation_id"] == "AION-TCGE-001"
    assert report["decision"] == DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert len(report["scenario_results"]) == 28
    assert all(item["passed"] is True for item in report["scenario_results"])
    assert all(item["passed"] is True for item in report["hard_gate_results"])
    assert report["report_is_approval"] is False
    assert report["report_reusable"] is False
    rendered = json.dumps(report, sort_keys=True).lower()
    for marker in ("sk-", "ghp_", "gho_", "xoxb-", "bearer "):
        assert marker not in rendered
    summary = read_json(
        "examples/knowledge-intelligence/claim-graph-evaluation-scenario-summary.json"
    )
    assert summary["scenario_count"] == 28


def test_claim_graph_operator_evaluation_scripts_pass_in_nested_mode():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-210 claim graph docs"}
    for script in (
        "scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh",
    ):
        subprocess.run([str(ROOT / script)], cwd=ROOT, env=env, check=True)
