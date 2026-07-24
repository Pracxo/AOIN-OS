from __future__ import annotations

import json
import os
import subprocess

from knowledge_source_registry_test_helpers import ROOT, read_json

DECISION = (
    "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION"
)

REQUIRED_FILES = [
    "docs/knowledge-intelligence/source-registry-operator-evaluation-closeout.md",
    "docs/knowledge-intelligence/source-registry-operator-evaluation-report.md",
    "docs/knowledge-intelligence/source-registry-evaluation-scenarios.md",
    "docs/release/knowledge-intelligence-source-registry-evaluation-closeout.md",
    "docs/release/knowledge-intelligence-source-registry-evaluation-checklist.md",
    "docs/release/knowledge-intelligence-source-registry-evaluation-evidence-matrix.md",
    "docs/release/knowledge-intelligence-source-registry-evaluation-runtime-hold.md",
    "examples/knowledge-intelligence/source-registry-operator-evaluation-report.json",
    "examples/knowledge-intelligence/source-registry-evaluation-scenario-summary.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-evaluation.json",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh",
]


def test_source_registry_operator_evaluation_required_files_and_report():
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), relative

    report = read_json(
        "examples/knowledge-intelligence/source-registry-operator-evaluation-report.json"
    )
    assert report["evaluation_id"] == "AION-SPRE-001"
    assert report["decision"] == DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert len(report["scenario_results"]) == 28
    assert all(item["passed"] is True for item in report["scenario_results"])
    assert all(item["passed"] is True for item in report["hard_gate_results"])
    assert report["corrective_prs"] == []
    assert report["report_is_approval"] is False
    assert report["report_reusable"] is False
    rendered = json.dumps(report, sort_keys=True).lower()
    for marker in ("sk-", "ghp_", "gho_", "xoxb-", "bearer "):
        assert marker not in rendered


def test_source_registry_operator_evaluation_no_go_script_passes():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-208 operator evaluation no-go"}
    script = (
        ROOT
        / "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh"
    )
    subprocess.run(
        [str(script)],
        cwd=ROOT,
        env=env,
        check=True,
    )
