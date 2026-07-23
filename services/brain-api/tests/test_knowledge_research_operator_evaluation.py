from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/knowledge_intelligence_research_operator_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion206_research_operator_evaluation", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_operator_evaluation_executes_exact_28_scenarios(tmp_path: Path):
    harness = _load_harness()
    report = tmp_path / "AION-RAE-001.json"

    code = harness.main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--evaluation-id",
            "AION-RAE-001",
            "--evaluation-base-commit",
            "45d473fe2a07b62acd6f6957f5419fa78dcc6fc2",
            "--temporary-output-directory",
            str(tmp_path),
            "--report",
            str(report),
        ]
    )

    assert code == 0
    payload = json.loads(report.read_text())
    assert payload["evaluation_id"] == "AION-RAE-001"
    assert payload["scenario_count"] == 28
    assert [item["scenario_id"] for item in payload["scenario_results"]] == list(
        harness.SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert payload["decision"] == harness.PASS_DECISION
    assert payload["evaluation_passed"] is True
    assert payload["repository_integrity"]["live_network_requests"] == 0
    assert payload["repository_integrity"]["live_dns_requests"] == 0
    assert payload["knowledge_promoted"] is False
    assert payload["belief_mutated"] is False
    harness.validate_report(payload)


def test_operator_evaluation_rejects_missing_scenario(tmp_path: Path):
    harness = _load_harness()
    payload = harness.run_evaluation(
        repo_root=REPO_ROOT,
        evaluation_id="AION-RAE-001",
        evaluation_base_commit="45d473fe2a07b62acd6f6957f5419fa78dcc6fc2",
        temporary_output_directory=tmp_path,
    )
    payload["scenario_results"] = payload["scenario_results"][:-1]

    try:
        harness.validate_report(payload)
    except ValueError as exc:
        assert "scenario list mismatch" in str(exc)
    else:
        raise AssertionError("missing scenario was accepted")
