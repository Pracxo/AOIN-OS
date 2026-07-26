from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py"
)


def _load_harness():
    spec = __import__("importlib.util").util.spec_from_file_location(
        "aion216_integrated_research_agent_operator_evaluation",
        HARNESS,
    )
    assert spec is not None and spec.loader is not None
    module = __import__("importlib.util").util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_integrated_research_agent_operator_evaluation_executes_exact_28_scenarios(
    tmp_path: Path,
):
    harness = _load_harness()
    report = tmp_path / "AION-IRAE-001.json"

    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-IRAE-001",
            "--evaluation-base-commit",
            "2988b8f389f7ee3a141f74e351432f4ea79c6eae",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )

    assert code == 0
    payload = json.loads(report.read_text())
    assert payload["evaluation_id"] == "AION-IRAE-001"
    assert payload["evaluation_type"] == "read_only_integrated_research_agent_operator_evaluation"
    assert payload["scenario_count"] == 28
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.REQUIRED_SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
    assert [item["plane_id"] for item in payload["plane_validation_results"]] == list(
        harness.PLANE_IDS
    )
    assert all(item["passed"] is True for item in payload["plane_validation_results"])
    assert payload["decision"] == harness.DECISION_PASS
    assert payload["evaluation_passed"] is True
    assert payload["implementation_prs"] == [129]
    assert payload["implementation_feature_commits"] == [
        "c9a35cc853ee1587cb9e149a020e2f767ca80881"
    ]
    assert payload["implementation_merge_commits"] == [
        "2988b8f389f7ee3a141f74e351432f4ea79c6eae"
    ]
    for key, value in harness.ZERO_EFFECT_FIELDS.items():
        assert payload[key] == value
    assert payload["authorization_closeout"]["authorization_transaction_id"] == (
        "AION-214-KI-0006"
    )
    next_auth = payload["conditional_next_authorization"]
    assert next_auth["authorization_transaction_id"] == "AION-216-KI-0007"
    assert next_auth["implementation_task"] == "AION-217"
    assert next_auth["formal_closeout_task"] == "AION-218"
    assert next_auth["resource_limits"]["maximum_persistent_verified_knowledge_write_batch"] == 0
    assert payload["integrated_lineage"]["lineage_complete"] is True
    assert payload["integrated_lineage"]["integrated_trace_fingerprint"] != (
        payload["integrated_lineage"]["sensitivity_trace_fingerprint"]
    )
    harness.validate_evaluation_report(payload)


def test_integrated_research_agent_operator_evaluation_validates_saved_report(
    tmp_path: Path,
):
    harness = _load_harness()
    report = tmp_path / "AION-IRAE-001.json"

    assert (
        harness.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--evaluation-id",
                "AION-IRAE-001",
                "--evaluation-base-commit",
                "2988b8f389f7ee3a141f74e351432f4ea79c6eae",
                "--temporary-output-directory",
                str(tmp_path),
                "--report",
                str(report),
            ]
        )
        == 0
    )
    assert harness.main(["--validate-report", str(report)]) == 0


def test_integrated_research_agent_operator_evaluation_rejects_duplicate_unknown_and_missing_scenarios(
    tmp_path: Path,
):
    harness = _load_harness()
    payload = harness.evaluate_integrated_research_agent(
        repo_root=REPO_ROOT,
        evaluation_id="AION-IRAE-001",
        evaluation_base_commit="2988b8f389f7ee3a141f74e351432f4ea79c6eae",
        temporary_output_directory=tmp_path,
    )

    missing = json.loads(json.dumps(payload, default=str))
    missing["scenario_results"] = missing["scenario_results"][:-1]
    try:
        harness.validate_evaluation_report(missing)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("missing scenario was accepted")

    duplicate = json.loads(json.dumps(payload, default=str))
    duplicate["scenario_results"][-1] = duplicate["scenario_results"][0]
    try:
        harness.validate_evaluation_report(duplicate)
    except ValueError as exc:
        assert "scenario results must match" in str(exc) or "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate scenario was accepted")

    unknown = json.loads(json.dumps(payload, default=str))
    unknown["scenario_results"][0]["scenario_id"] = "unknown"
    try:
        harness.validate_evaluation_report(unknown)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("unknown scenario was accepted")


def test_integrated_research_agent_operator_evaluation_rejects_missing_hard_gate_and_manual_decision(
    tmp_path: Path,
):
    harness = _load_harness()
    payload = harness.evaluate_integrated_research_agent(
        repo_root=REPO_ROOT,
        evaluation_id="AION-IRAE-001",
        evaluation_base_commit="2988b8f389f7ee3a141f74e351432f4ea79c6eae",
        temporary_output_directory=tmp_path,
    )

    missing_gate = json.loads(json.dumps(payload, default=str))
    missing_gate["hard_gate_results"] = missing_gate["hard_gate_results"][:-1]
    try:
        harness.validate_evaluation_report(missing_gate)
    except ValueError as exc:
        assert "hard gate results must match" in str(exc)
    else:
        raise AssertionError("missing hard gate was accepted")

    manual_pass = json.loads(json.dumps(payload, default=str))
    manual_pass["scenario_results"][0]["passed"] = False
    manual_pass["decision"] = harness.DECISION_PASS
    try:
        harness.validate_evaluation_report(manual_pass)
    except ValueError as exc:
        assert "evaluation_passed must be derived" in str(exc) or "PASS cannot be reported" in str(exc)
    else:
        raise AssertionError("manual PASS upgrade was accepted")

    manual_fail = json.loads(json.dumps(payload, default=str))
    manual_fail["decision"] = harness.DECISION_FAIL
    manual_fail["evaluation_passed"] = False
    try:
        harness.validate_evaluation_report(manual_fail)
    except ValueError as exc:
        assert "evaluation_passed must be derived" in str(exc) or "FAIL cannot be upgraded" in str(exc)
    else:
        raise AssertionError("manual FAIL downgrade was accepted")


def test_integrated_research_agent_operator_evaluation_rejects_report_outside_temp(
    tmp_path: Path,
):
    harness = _load_harness()
    report = REPO_ROOT / "examples/knowledge-intelligence/forbidden-temp-report.json"

    assert (
        harness.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--evaluation-id",
                "AION-IRAE-001",
                "--evaluation-base-commit",
                "2988b8f389f7ee3a141f74e351432f4ea79c6eae",
                "--temporary-output-directory",
                str(tmp_path),
                "--report",
                str(report),
            ]
        )
        == 2
    )
    assert not report.exists()


def test_integrated_research_agent_operator_evaluation_has_no_forbidden_runtime_imports():
    tree = ast.parse(HARNESS.read_text(encoding="utf-8"), filename=str(HARNESS))
    prohibited = {
        "socket",
        "requests",
        "httpx",
        "aiohttp",
        "urllib.request",
        "sqlite3",
        "subprocess",
        "git",
        "github",
        "selenium",
        "playwright",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not {name for name in imports if name in prohibited}


def test_integrated_research_agent_operator_evaluation_no_go_script_passes():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-216 integrated no-go"}
    script = (
        REPO_ROOT
        / (
            "scripts/knowledge-intelligence-integrated-research-agent-operator-"
            "evaluation-no-go-regression.sh"
        )
    )
    subprocess.run([str(script)], cwd=REPO_ROOT, env=env, check=True)
