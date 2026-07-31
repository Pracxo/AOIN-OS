from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/model_gateway_operator_evaluation.py"
SAVED_REPORT = (
    REPO_ROOT / "examples/secure-runtime-integration/model-gateway-operator-evaluation-report.json"
)


def _load_harness():
    spec = __import__("importlib.util").util.spec_from_file_location(
        "aion234_model_gateway_operator_evaluation",
        HARNESS,
    )
    assert spec is not None and spec.loader is not None
    module = __import__("importlib.util").util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _saved_or_generated_report(harness, tmp_path: Path) -> dict[str, object]:
    if SAVED_REPORT.exists():
        payload = json.loads(SAVED_REPORT.read_text(encoding="utf-8"))
        harness.validate_evaluation_report(payload)
        return payload

    report = tmp_path / "AION-SRIPE-002.json"
    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-SRIPE-002",
            "--evaluation-base-commit",
            "48e9daebcac77aa48aa2336323c40eae948f3ac2",
            "--pilot-evidence",
            "examples/secure-runtime-integration/model-gateway-local-simulation-pilot-evidence.json",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )
    assert code == 0
    return json.loads(report.read_text(encoding="utf-8"))


def test_model_gateway_operator_evaluation_executes_exact_28_scenarios(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)
    assert payload["evaluation_id"] == "AION-SRIPE-002"
    assert payload["evaluation_type"] == "controlled_model_gateway_operator_evaluation"
    assert payload["scenario_count"] == 28
    assert payload["scenario_ids"] == list(harness.REQUIRED_SCENARIO_IDS)
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.REQUIRED_SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
    assert payload["decision"] == harness.DECISION_PASS
    assert payload["evaluation_passed"] is True
    assert payload["implementation_prs"] == [151, 152]
    assert payload["implementation_feature_commits"] == list(
        harness.IMPLEMENTATION_FEATURE_COMMITS
    )
    assert payload["implementation_merge_commits"] == list(harness.IMPLEMENTATION_MERGE_COMMITS)
    assert payload["network_calls"] == 0
    assert payload["model_provider_calls"] == 0
    assert payload["connector_calls"] == 0
    assert payload["actual_tool_executions"] == 0
    assert payload["active_gateway_sessions_after_evaluation"] == 0
    assert payload["active_requests_after_evaluation"] == 0
    assert payload["repository_unchanged"] is True
    assert payload["temporary_evaluation_data_cleaned"] is True
    harness.validate_evaluation_report(payload)


def test_model_gateway_operator_evaluation_validates_saved_report(tmp_path: Path) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)
    report = SAVED_REPORT if SAVED_REPORT.exists() else tmp_path / "AION-SRIPE-002.json"
    if not report.exists():
        report.write_text(json.dumps(payload), encoding="utf-8")
    assert harness.main(["--validate-report", str(report)]) == 0


def test_model_gateway_operator_evaluation_rejects_bad_shapes(tmp_path: Path) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)

    missing = json.loads(json.dumps(payload))
    missing["scenario_results"] = missing["scenario_results"][:-1]
    missing["report_fingerprint"] = harness.report_fingerprint(missing)
    try:
        harness.validate_evaluation_report(missing)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("missing scenario was accepted")

    missing_gate = json.loads(json.dumps(payload))
    missing_gate["hard_gate_results"] = missing_gate["hard_gate_results"][:-1]
    missing_gate["report_fingerprint"] = harness.report_fingerprint(missing_gate)
    try:
        harness.validate_evaluation_report(missing_gate)
    except ValueError as exc:
        assert "hard gate results must match" in str(exc)
    else:
        raise AssertionError("missing hard gate was accepted")

    manual_pass = json.loads(json.dumps(payload))
    manual_pass["hard_gate_results"][0]["passed"] = False
    manual_pass["decision"] = harness.DECISION_PASS
    manual_pass["evaluation_passed"] = True
    manual_pass["report_fingerprint"] = harness.report_fingerprint(manual_pass)
    try:
        harness.validate_evaluation_report(manual_pass)
    except ValueError as exc:
        assert "evaluation_passed must be derived" in str(exc) or "PASS cannot" in str(exc)
    else:
        raise AssertionError("manual PASS was accepted")


def test_model_gateway_operator_evaluation_rejects_bad_fingerprint(tmp_path: Path) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)
    payload["report_fingerprint"] = "0" * 64
    try:
        harness.validate_evaluation_report(payload)
    except ValueError as exc:
        assert "report fingerprint mismatch" in str(exc)
    else:
        raise AssertionError("bad report fingerprint was accepted")


def test_model_gateway_operator_evaluation_has_no_network_or_process_imports() -> None:
    tree = ast.parse(HARNESS.read_text(encoding="utf-8"), filename=str(HARNESS))
    prohibited = {
        "socket",
        "requests",
        "httpx",
        "aiohttp",
        "urllib.request",
        "subprocess",
        "webbrowser",
        "git",
        "github",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name for alias in node.names}
            assert not names.intersection(prohibited)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in prohibited


def test_model_gateway_operator_evaluation_scripts_pass_in_nested_mode() -> None:
    result = subprocess.run(
        ["./scripts/model-gateway-operator-evaluation-check.sh"],
        cwd=REPO_ROOT,
        env={
            "PATH": str(Path("/usr/bin")) + ":" + str(Path("/bin")),
            "PYTEST_CURRENT_TEST": "1",
        },
        capture_output=True,
        text=True,
        check=True,
    )
    assert "controlled model gateway operator evaluation PASS" in result.stdout
