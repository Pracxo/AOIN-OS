from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/knowledge_intelligence_source_registry_operator_evaluation.py"


def _load_harness():
    spec = __import__("importlib.util").util.spec_from_file_location(
        "aion208_source_registry_operator_evaluation",
        HARNESS,
    )
    assert spec is not None and spec.loader is not None
    module = __import__("importlib.util").util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_source_registry_operator_evaluation_executes_exact_28_scenarios(tmp_path: Path):
    harness = _load_harness()
    report = tmp_path / "AION-SPRE-001.json"

    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-SPRE-001",
            "--evaluation-base-commit",
            "14c12bebfced7fd6345c8af2899988aadfa91a44",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )

    assert code == 0
    assert sorted(path.name for path in tmp_path.iterdir()) == ["AION-SPRE-001.json"]
    payload = json.loads(report.read_text())
    assert payload["evaluation_id"] == "AION-SPRE-001"
    assert payload["evaluation_base_commit"] == "14c12bebfced7fd6345c8af2899988aadfa91a44"
    assert payload["scenario_count"] == 28
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.REQUIRED_SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
    assert payload["decision"] == harness.DECISION_PASS
    assert payload["evaluation_passed"] is True
    assert payload["repository_integrity"]["live_network_requests"] == 0
    assert payload["repository_integrity"]["live_dns_requests"] == 0
    assert payload["resource_state"]["persistent_registry_writes"] == 0
    assert payload["runtime_state"]["knowledge_promoted"] is False
    assert payload["runtime_state"]["belief_mutated"] is False
    assert payload["conditional_next_authorization"]["authorization_transaction_id"] == (
        "AION-208-KI-0003"
    )
    harness.validate_evaluation_report(payload)


def test_source_registry_operator_evaluation_validates_saved_report(tmp_path: Path):
    harness = _load_harness()
    report = tmp_path / "AION-SPRE-001.json"

    assert (
        harness.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--evaluation-id",
                "AION-SPRE-001",
                "--evaluation-base-commit",
                "14c12bebfced7fd6345c8af2899988aadfa91a44",
                "--temporary-output-directory",
                str(tmp_path),
                "--report",
                str(report),
            ]
        )
        == 0
    )
    assert harness.main(["--validate-report", str(report)]) == 0


def test_source_registry_operator_evaluation_rejects_missing_scenario(tmp_path: Path):
    harness = _load_harness()
    payload = harness.evaluate_source_registry(
        repo_root=REPO_ROOT,
        evaluation_id="AION-SPRE-001",
        evaluation_base_commit="14c12bebfced7fd6345c8af2899988aadfa91a44",
        temporary_output_directory=tmp_path,
    )
    payload["scenario_results"] = payload["scenario_results"][:-1]

    try:
        harness.validate_evaluation_report(payload)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("missing scenario was accepted")


def test_source_registry_operator_evaluation_rejects_manual_pass_upgrade(tmp_path: Path):
    harness = _load_harness()
    payload = harness.evaluate_source_registry(
        repo_root=REPO_ROOT,
        evaluation_id="AION-SPRE-001",
        evaluation_base_commit="14c12bebfced7fd6345c8af2899988aadfa91a44",
        temporary_output_directory=tmp_path,
    )
    payload["scenario_results"][0]["passed"] = False
    payload["decision"] = harness.DECISION_PASS

    try:
        harness.validate_evaluation_report(payload)
    except ValueError as exc:
        assert "evaluation_passed must be derived" in str(exc)
    else:
        raise AssertionError("manual PASS upgrade was accepted")


def test_source_registry_operator_evaluation_has_no_runtime_or_network_imports():
    tree = ast.parse(HARNESS.read_text(encoding="utf-8"), filename=str(HARNESS))
    prohibited = {
        "socket",
        "requests",
        "httpx",
        "aiohttp",
        "urllib" + ".request",
        "sqlite3",
        "git",
        "github",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not {name for name in imports if name in prohibited}


def test_source_registry_operator_evaluation_no_go_script_passes():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-208 source registry no-go"}
    script = (
        REPO_ROOT
        / "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh"
    )
    subprocess.run(
        [str(script)],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
