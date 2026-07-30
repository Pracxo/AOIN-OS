from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/secure_runtime_foundation_operator_evaluation.py"


def _load_harness():
    spec = __import__("importlib.util").util.spec_from_file_location(
        "aion232_secure_runtime_foundation_operator_evaluation",
        HARNESS,
    )
    assert spec is not None and spec.loader is not None
    module = __import__("importlib.util").util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_secure_runtime_foundation_operator_evaluation_executes_exact_28_scenarios(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    report = tmp_path / "AION-SRIPE-001.json"

    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-SRIPE-001",
            "--evaluation-base-commit",
            "8bb9af29cc2cf960d9efdfe2ee323d7245812747",
            "--pilot-evidence",
            "examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )

    assert code == 0
    payload = json.loads(report.read_text())
    assert payload["evaluation_id"] == "AION-SRIPE-001"
    assert payload["evaluation_type"] == "secure_runtime_foundation_operator_evaluation"
    assert payload["scenario_count"] == 28
    assert payload["scenario_ids"] == list(harness.REQUIRED_SCENARIO_IDS)
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.REQUIRED_SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
    assert payload["decision"] == harness.DECISION_PASS
    assert payload["evaluation_passed"] is True
    assert payload["implementation_prs"] == [149]
    assert payload["implementation_feature_commits"] == [
        "45540009d03f60d7477330a88946e73705ee60e5"
    ]
    assert payload["implementation_merge_commits"] == [
        "8bb9af29cc2cf960d9efdfe2ee323d7245812747"
    ]
    assert payload["network_calls"] == 0
    assert payload["model_provider_calls"] == 0
    assert payload["active_sessions_after_evaluation"] == 0
    assert payload["active_requests_after_evaluation"] == 0
    assert payload["repository_unchanged"] is True
    assert payload["temporary_evaluation_data_cleaned"] is True
    harness.validate_evaluation_report(payload)


def test_secure_runtime_foundation_operator_evaluation_validates_saved_report(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    report = tmp_path / "AION-SRIPE-001.json"
    assert (
        harness.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--evaluation-id",
                "AION-SRIPE-001",
                "--evaluation-base-commit",
                "8bb9af29cc2cf960d9efdfe2ee323d7245812747",
                "--pilot-evidence",
                "examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json",
                "--temporary-output-directory",
                str(tmp_path),
                "--report",
                str(report),
            ]
        )
        == 0
    )
    assert harness.main(["--validate-report", str(report)]) == 0


def test_secure_runtime_foundation_operator_evaluation_rejects_bad_scenario_shapes(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = harness.evaluate_secure_runtime_foundation(
        repo_root=REPO_ROOT,
        evaluation_id="AION-SRIPE-001",
        evaluation_base_commit="8bb9af29cc2cf960d9efdfe2ee323d7245812747",
        pilot_evidence=(
            REPO_ROOT
            / "examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json"
        ),
        temporary_output_directory=tmp_path,
    )

    missing = json.loads(json.dumps(payload))
    missing["scenario_results"] = missing["scenario_results"][:-1]
    missing["report_fingerprint"] = harness.report_fingerprint(missing)
    try:
        harness.validate_evaluation_report(missing)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("missing scenario was accepted")

    duplicate = json.loads(json.dumps(payload))
    duplicate["scenario_results"][-1] = duplicate["scenario_results"][0]
    duplicate["report_fingerprint"] = harness.report_fingerprint(duplicate)
    try:
        harness.validate_evaluation_report(duplicate)
    except ValueError as exc:
        assert "duplicate" in str(exc) or "scenario results must match" in str(exc)
    else:
        raise AssertionError("duplicate scenario was accepted")

    unknown = json.loads(json.dumps(payload))
    unknown["scenario_results"][0]["scenario_id"] = "unknown"
    unknown["report_fingerprint"] = harness.report_fingerprint(unknown)
    try:
        harness.validate_evaluation_report(unknown)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("unknown scenario was accepted")


def test_secure_runtime_foundation_operator_evaluation_rejects_bad_hard_gate_and_pass(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = harness.evaluate_secure_runtime_foundation(
        repo_root=REPO_ROOT,
        evaluation_id="AION-SRIPE-001",
        evaluation_base_commit="8bb9af29cc2cf960d9efdfe2ee323d7245812747",
        pilot_evidence=(
            REPO_ROOT
            / "examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json"
        ),
        temporary_output_directory=tmp_path,
    )

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


def test_secure_runtime_foundation_operator_evaluation_rejects_bad_fingerprint(
    tmp_path: Path,
) -> None:
    harness = _load_harness()
    payload = harness.evaluate_secure_runtime_foundation(
        repo_root=REPO_ROOT,
        evaluation_id="AION-SRIPE-001",
        evaluation_base_commit="8bb9af29cc2cf960d9efdfe2ee323d7245812747",
        pilot_evidence=(
            REPO_ROOT
            / "examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json"
        ),
        temporary_output_directory=tmp_path,
    )
    payload["report_fingerprint"] = "0" * 64
    try:
        harness.validate_evaluation_report(payload)
    except ValueError as exc:
        assert "report fingerprint mismatch" in str(exc)
    else:
        raise AssertionError("bad report fingerprint was accepted")


def test_secure_runtime_foundation_operator_evaluation_has_no_network_or_process_imports() -> None:
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
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not {name for name in imports if name in prohibited}


def test_secure_runtime_foundation_operator_evaluation_scripts_pass_in_nested_mode() -> None:
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-232 operator evaluation"}
    for script in (
        "scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh",
        "scripts/secure-runtime-foundation-operator-evaluation-check.sh",
    ):
        subprocess.run([str(REPO_ROOT / script)], cwd=REPO_ROOT, env=env, check=True)
