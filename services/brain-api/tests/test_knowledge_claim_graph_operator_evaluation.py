from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/knowledge_intelligence_claim_graph_operator_evaluation.py"


def _load_harness():
    spec = __import__("importlib.util").util.spec_from_file_location(
        "aion210_claim_graph_operator_evaluation",
        HARNESS,
    )
    assert spec is not None and spec.loader is not None
    module = __import__("importlib.util").util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_claim_graph_operator_evaluation_executes_exact_28_scenarios(tmp_path: Path):
    harness = _load_harness()
    report = tmp_path / "AION-TCGE-001.json"

    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-TCGE-001",
            "--evaluation-base-commit",
            "f9e2438a49aae458983fc57cee5c12b5ef0ab856",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )

    assert code == 0
    payload = json.loads(report.read_text())
    assert payload["evaluation_id"] == "AION-TCGE-001"
    assert payload["evaluation_base_commit"] == "f9e2438a49aae458983fc57cee5c12b5ef0ab856"
    assert payload["scenario_count"] == 28
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.REQUIRED_SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
    assert payload["decision"] == harness.DECISION_PASS
    assert payload["evaluation_passed"] is True
    assert payload["implementation_prs"] == [121]
    assert payload["implementation_feature_commits"] == [
        "0a84080c83f87eef94b5191c432021776c6a336a",
        "d50252c84a0a02b75317c7d2051eaee4fb9dc54c",
    ]
    assert payload["implementation_merge_commits"] == [
        "f9e2438a49aae458983fc57cee5c12b5ef0ab856"
    ]
    assert payload["repository_integrity"]["source_body_bytes"] == 0
    assert payload["repository_integrity"]["persistent_graph_writes"] == 0
    assert payload["repository_integrity"]["live_network_requests"] == 0
    assert payload["repository_integrity"]["live_dns_requests"] == 0
    assert payload["repository_integrity"]["repository_unchanged"] is True
    assert payload["resource_state"]["persistent_claim_graph_write_enabled"] is False
    assert payload["runtime_state"]["knowledge_promoted"] is False
    assert payload["runtime_state"]["belief_mutated"] is False
    assert payload["conditional_next_authorization"]["authorization_transaction_id"] == (
        "AION-210-KI-0004"
    )
    harness.validate_evaluation_report(payload)


def test_claim_graph_operator_evaluation_validates_saved_report(tmp_path: Path):
    harness = _load_harness()
    report = tmp_path / "AION-TCGE-001.json"

    assert (
        harness.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--evaluation-id",
                "AION-TCGE-001",
                "--evaluation-base-commit",
                "f9e2438a49aae458983fc57cee5c12b5ef0ab856",
                "--temporary-output-directory",
                str(tmp_path),
                "--report",
                str(report),
            ]
        )
        == 0
    )
    assert harness.main(["--validate-report", str(report)]) == 0


def test_claim_graph_operator_evaluation_rejects_duplicate_unknown_and_missing_scenarios(
    tmp_path: Path,
):
    harness = _load_harness()
    payload = harness.evaluate_claim_graph(
        repo_root=REPO_ROOT,
        evaluation_id="AION-TCGE-001",
        evaluation_base_commit="f9e2438a49aae458983fc57cee5c12b5ef0ab856",
        temporary_output_directory=tmp_path,
    )

    missing = json.loads(json.dumps(payload))
    missing["scenario_results"] = missing["scenario_results"][:-1]
    try:
        harness.validate_evaluation_report(missing)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("missing scenario was accepted")

    duplicate = json.loads(json.dumps(payload))
    duplicate["scenario_results"][-1] = duplicate["scenario_results"][0]
    try:
        harness.validate_evaluation_report(duplicate)
    except ValueError as exc:
        assert "scenario results must match" in str(exc) or "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate scenario was accepted")

    unknown = json.loads(json.dumps(payload))
    unknown["scenario_results"][0]["scenario_id"] = "unknown"
    try:
        harness.validate_evaluation_report(unknown)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("unknown scenario was accepted")


def test_claim_graph_operator_evaluation_rejects_missing_hard_gate_and_manual_pass(
    tmp_path: Path,
):
    harness = _load_harness()
    payload = harness.evaluate_claim_graph(
        repo_root=REPO_ROOT,
        evaluation_id="AION-TCGE-001",
        evaluation_base_commit="f9e2438a49aae458983fc57cee5c12b5ef0ab856",
        temporary_output_directory=tmp_path,
    )

    missing_gate = json.loads(json.dumps(payload))
    missing_gate["hard_gate_results"] = missing_gate["hard_gate_results"][:-1]
    try:
        harness.validate_evaluation_report(missing_gate)
    except ValueError as exc:
        assert "hard gate results must match" in str(exc)
    else:
        raise AssertionError("missing hard gate was accepted")

    manual_pass = json.loads(json.dumps(payload))
    manual_pass["scenario_results"][0]["passed"] = False
    manual_pass["decision"] = harness.DECISION_PASS
    try:
        harness.validate_evaluation_report(manual_pass)
    except ValueError as exc:
        assert "evaluation_passed must be derived" in str(exc)
    else:
        raise AssertionError("manual PASS upgrade was accepted")


def test_claim_graph_operator_evaluation_has_no_runtime_or_network_imports():
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


def test_claim_graph_operator_evaluation_no_go_script_passes():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-210 claim graph no-go"}
    script = (
        REPO_ROOT
        / "scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh"
    )
    subprocess.run(
        [str(script)],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
