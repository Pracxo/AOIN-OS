from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/external_cognition_foundation_operator_evaluation.py"
SAVED_REPORT = (
    REPO_ROOT
    / "examples/adaptive-intelligence/external-cognition-foundation-operator-evaluation-report.json"
)


def _load_harness():
    spec = __import__("importlib.util").util.spec_from_file_location(
        "aion247_external_cognition_foundation_operator_evaluation",
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

    report = tmp_path / "AION-ECGPE-001.json"
    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-ECGPE-001",
            "--implementation-main-commit",
            "27d6ad15a043940bf537caec72cf7de7c74f6dc2",
            "--implementation-commit",
            "dd1f7b34cb2a25dfd409cf72667f073af9e8e965",
            "--pilot-evidence",
            "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json",
            "--evaluation-base-commit",
            "test-evaluation-base",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )
    assert code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    harness.validate_evaluation_report(payload)
    return payload


def test_external_cognition_operator_evaluation_executes_exact_32_hard_gates(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)

    assert payload["evaluation_id"] == "AION-ECGPE-001"
    assert payload["evaluation_type"] == (
        "controlled_external_cognition_gateway_foundation_operator_evaluation"
    )
    assert payload["scenario_count"] == 32
    assert payload["hard_gate_count"] == 32
    assert payload["scenario_ids"] == list(harness.SCENARIO_IDS)
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.SCENARIO_IDS
    )
    assert [item["scenario_id"] for item in payload["hard_gate_results"]] == list(
        harness.SCENARIO_IDS
    )
    assert all(item["hard_gate"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
    assert payload["decision"] == harness.PASS_DECISION
    assert payload["evaluation_passed"] is True
    assert payload["implementation_prs"] == [166]
    assert payload["implementation_feature_commits"] == list(
        harness.IMPLEMENTATION_FEATURE_COMMITS
    )
    assert payload["implementation_merge_commits"] == [harness.PRIMARY_MERGE_COMMIT]


def test_external_cognition_operator_evaluation_preserves_zero_effects(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)

    for key in harness.REPORT_ZERO_COUNTERS:
        assert payload[key] == 0
    assert payload["repository_unchanged"] is True
    assert payload["temporary_evaluation_data_cleaned"] is True
    assert payload["read_only"] is True
    assert payload["redacted"] is True
    assert payload["production_runtime_authorized"] is False
    assert payload["pilot_validation"]["report_fingerprint"] == (
        "2f9a05f78d4afb40f390ace3cafbb2f997e46525063cd80fe6cab131e8be9aad"
    )
    assert all(
        value == 0
        for value in payload["pilot_validation"]["prohibited_effect_counters"].values()
    )


def test_external_cognition_operator_evaluation_authorizes_only_future_openai_pilot(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)
    decision = payload["live_pilot_architecture_decision"]

    assert decision["authorization_transaction_id"] == "AION-247-AI-0002"
    assert decision["provider_id"] == "openai"
    assert decision["provider_api_family"] == "responses"
    assert decision["allowed_endpoint_host"] == "api.openai.com"
    assert decision["allowed_endpoint_path"] == "/v1/responses"
    assert decision["model_family_boundary"] == "gpt-5.6"
    assert decision["maximum_selected_models"] == 1
    assert decision["request_policy"] == {
        "store": False,
        "background": False,
        "stream": False,
        "tools": False,
        "files": False,
        "previous_response_id": False,
        "synthetic_text_only": True,
    }
    assert all(decision["approved_capabilities"].values())
    assert not any(decision["prohibited_capabilities"].values())
    assert decision["resource_limits"]["maximum_live_provider_calls"] == 6
    assert decision["resource_limits"]["maximum_provider_tool_calls"] == 0


def test_external_cognition_operator_evaluation_rejects_bad_shapes(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = _saved_or_generated_report(harness, tmp_path)

    missing = json.loads(json.dumps(payload))
    missing["scenario_results"] = missing["scenario_results"][:-1]
    missing["report_fingerprint"] = harness.report_fingerprint(missing)
    try:
        harness.validate_evaluation_report(missing)
    except ValueError as exc:
        assert "scenario_results must match" in str(exc)
    else:
        raise AssertionError("missing scenario was accepted")

    manual_pass = json.loads(json.dumps(payload))
    manual_pass["hard_gate_results"][0]["passed"] = False
    manual_pass["decision"] = harness.PASS_DECISION
    manual_pass["evaluation_passed"] = True
    manual_pass["report_fingerprint"] = harness.report_fingerprint(manual_pass)
    try:
        harness.validate_evaluation_report(manual_pass)
    except ValueError as exc:
        assert "evaluation_passed must be derived" in str(exc) or "PASS cannot" in str(exc)
    else:
        raise AssertionError("manual PASS was accepted")

    bad_fingerprint = json.loads(json.dumps(payload))
    bad_fingerprint["report_fingerprint"] = "0" * 64
    try:
        harness.validate_evaluation_report(bad_fingerprint)
    except ValueError as exc:
        assert "report fingerprint mismatch" in str(exc)
    else:
        raise AssertionError("bad report fingerprint was accepted")


def test_external_cognition_operator_evaluation_has_no_network_or_process_imports() -> None:
    tree = ast.parse(HARNESS.read_text(encoding="utf-8"), filename=str(HARNESS))
    prohibited = {
        "aiohttp",
        "httpx",
        "openai",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "urllib.request",
        "webbrowser",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name for alias in node.names}
            assert not names.intersection(prohibited)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in prohibited


def test_external_cognition_operator_evaluation_scripts_pass_in_nested_mode() -> None:
    env = {**os.environ, "AION_BRAIN_PYTHON": sys.executable, "PYTEST_CURRENT_TEST": "1"}
    result = subprocess.run(
        ["./scripts/external-cognition-foundation-operator-evaluation-check.sh"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "external cognition foundation operator evaluation PASS" in result.stdout

    result = subprocess.run(
        ["./scripts/live-provider-pilot-runtime-hold.sh"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "live provider pilot runtime hold PASS" in result.stdout
