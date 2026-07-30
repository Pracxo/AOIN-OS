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
    spec = importlib.util.spec_from_file_location("aion229_program_final_evaluation", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_program_final_evaluation_executes_exact_28_scenarios(tmp_path: Path) -> None:
    harness = _load_harness()
    report = tmp_path / "AION-GLMPE-004.json"
    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-GLMPE-004",
            "--evaluation-base-commit",
            "0fc95c345c1f8daada58a5b45e6f3b1fdd33d9e0",
            "--live-evidence",
            str(LIVE_EVIDENCE),
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )
    assert code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["evaluation_id"] == "AION-GLMPE-004"
    assert payload["decision"] == harness.PASS_DECISION
    assert payload["evaluation_passed"] is True
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert set(payload["hard_gate_results"]) == set(harness.HARD_GATE_IDS)
    assert all(payload["hard_gate_results"].values())
    assert payload["network_calls"] == 0
    assert payload["repository_unchanged"] is True
    harness.validate_evaluation_report(payload)


def test_program_final_evaluation_validates_saved_report_when_present() -> None:
    harness = _load_harness()
    report = REPO_ROOT / "examples/governed-learning-memory/program-final-evaluation-report.json"
    if report.exists():
        assert harness.main(["--validate-report", str(report)]) == 0
