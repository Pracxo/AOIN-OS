from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/knowledge_intelligence_program_final_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion220_program_final_evaluation", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_program_final_evaluation_executes_exact_28_scenarios(tmp_path: Path) -> None:
    harness = _load_harness()
    report = tmp_path / "AION-KIPE-001.json"
    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-KIPE-001",
            "--evaluation-base-commit",
            "d0e1807edd7b3098ce62f8d00b0bceb4ee6fd23d",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )
    assert code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["evaluation_id"] == "AION-KIPE-001"
    assert payload["decision"] == harness.PASS_DECISION
    assert payload["evaluation_passed"] is True
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert set(payload["hard_gate_results"]) == set(harness.HARD_GATE_IDS)
    assert all(payload["hard_gate_results"].values())
    assert payload["evaluation_network_requests"] == 0
    assert payload["repository_unchanged_by_evaluation"] is True
    harness.validate_evaluation_report(payload)


def test_program_final_evaluation_validates_saved_report_when_present() -> None:
    harness = _load_harness()
    report = (
        REPO_ROOT
        / "examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json"
    )
    if report.exists():
        assert harness.main(["--validate-report", str(report)]) == 0
