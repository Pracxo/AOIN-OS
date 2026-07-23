import json
import os
import subprocess

from knowledge_source_registry_test_helpers import DECISION, EVALUATED_MAIN, ROOT, read_json

REQUIRED_FILES = [
    "docs/knowledge-intelligence/research-plane-operator-evaluation-closeout.md",
    "docs/knowledge-intelligence/research-plane-operator-evaluation-report.md",
    "docs/knowledge-intelligence/research-plane-evaluation-scenarios.md",
    "docs/release/knowledge-intelligence-research-evaluation-closeout.md",
    "docs/release/knowledge-intelligence-research-evaluation-checklist.md",
    "docs/release/knowledge-intelligence-research-evaluation-evidence-matrix.md",
    "docs/release/knowledge-intelligence-research-evaluation-runtime-hold.md",
    "examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json",
    "examples/knowledge-intelligence/research-acquisition-evaluation-scenario-summary.json",
    "scripts/knowledge-intelligence-research-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
]


def test_operator_evaluation_required_files_and_report():
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), relative
    report = read_json(
        "examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json"
    )
    assert report["evaluation_id"] == "AION-RAE-001"
    assert report["evaluation_base_commit"] == EVALUATED_MAIN
    assert report["decision"] == DECISION
    assert report["scenario_count"] == 28
    assert len(report["scenario_results"]) == 28
    assert all(item["passed"] for item in report["scenario_results"])
    assert all(report["hard_gate_results"].values())
    assert report["corrective_prs"] == [117]
    assert report["repository_integrity"]["live_network_requests"] == 0
    assert report["repository_integrity"]["live_dns_requests"] == 0
    assert report["claim_verification_performed"] is False
    assert report["knowledge_promoted"] is False
    assert report["belief_mutated"] is False
    rendered = json.dumps(report, sort_keys=True).lower()
    for marker in ("sk-", "ghp_", "gho_", "bearer "):
        assert marker not in rendered


def test_operator_evaluation_no_go_script_passes():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-206 operator evaluation no-go"}
    subprocess.run(
        [
            str(
                ROOT
                / "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh"
            )
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
