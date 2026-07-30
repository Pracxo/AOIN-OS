from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/governed_learning_memory_program_final_evaluation.py"
LIVE_EVIDENCE = (
    REPO_ROOT
    / (
        "examples/governed-learning-memory/"
        "controlled-local-continual-learning-live-pilot-evidence.json"
    )
)


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion229_scenarios", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _payload(tmp_path: Path):
    harness = _load_harness()
    return harness, harness.evaluate_program(
        repo_root=REPO_ROOT,
        evaluation_id="AION-GLMPE-004",
        evaluation_base_commit="0fc95c345c1f8daada58a5b45e6f3b1fdd33d9e0",
        live_evidence_path=LIVE_EVIDENCE,
        temporary_output_directory=tmp_path,
    )


def test_final_scenario_ids_are_exact_and_unique(tmp_path: Path) -> None:
    harness, payload = _payload(tmp_path)
    assert len(harness.SCENARIO_IDS) == 28
    assert len(set(harness.SCENARIO_IDS)) == 28
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.SCENARIO_IDS
    )


def test_final_report_rejects_missing_duplicate_unknown_or_failed_gate(tmp_path: Path) -> None:
    harness, payload = _payload(tmp_path)
    missing = json.loads(json.dumps(payload))
    missing["scenario_results"] = missing["scenario_results"][:-1]
    try:
        harness.validate_evaluation_report(missing)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("missing scenario accepted")

    duplicate = json.loads(json.dumps(payload))
    duplicate["scenario_results"][-1] = duplicate["scenario_results"][0]
    try:
        harness.validate_evaluation_report(duplicate)
    except ValueError as exc:
        assert "scenario results must match" in str(exc) or "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate scenario accepted")

    unknown = json.loads(json.dumps(payload))
    unknown["scenario_results"][0]["scenario_id"] = "unknown"
    try:
        harness.validate_evaluation_report(unknown)
    except ValueError as exc:
        assert "scenario results must match" in str(exc)
    else:
        raise AssertionError("unknown scenario accepted")

    failed_gate = json.loads(json.dumps(payload))
    failed_gate["hard_gate_results"][harness.HARD_GATE_IDS[0]] = False
    try:
        harness.validate_evaluation_report(failed_gate)
    except ValueError as exc:
        assert "evaluation_passed must be derived" in str(exc)
    else:
        raise AssertionError("PASS accepted with a failed hard gate")
