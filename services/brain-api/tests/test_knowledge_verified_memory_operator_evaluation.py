from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))

from knowledge_intelligence_verified_memory_operator_evaluation import (
    EVALUATION_ID,
    FAIL_DECISION,
    PASS_DECISION,
    SCENARIO_IDS,
    build_report,
)


def test_verified_memory_operator_evaluation_runs_all_required_scenarios(
    tmp_path: Path,
) -> None:
    report = build_report(
        repo_root=REPO_ROOT,
        evaluation_id=EVALUATION_ID,
        evaluation_base_commit="f1812bc2bc5f2af1a4fdc2eeaac12ab3c9aa4a1d",
        temporary_output_directory=tmp_path,
    )

    assert report["decision"] in {PASS_DECISION, FAIL_DECISION}
    assert report["evaluation_passed"] is (report["decision"] == PASS_DECISION)
    assert report["scenario_count"] == 28
    assert [item["scenario_id"] for item in report["scenario_results"]] == SCENARIO_IDS
    assert all(item["executed"] is True for item in report["scenario_results"])
    if report["evaluation_passed"]:
        assert all(item["passed"] is True for item in report["scenario_results"])
        assert all(report["hard_gate_results"].values())
    else:
        assert any(item["passed"] is False for item in report["scenario_results"])
        assert any(value is False for value in report["hard_gate_results"].values())


def test_verified_memory_operator_evaluation_report_is_redacted_and_zero_effect(
    tmp_path: Path,
) -> None:
    report = build_report(
        repo_root=REPO_ROOT,
        evaluation_id=EVALUATION_ID,
        evaluation_base_commit="f1812bc2bc5f2af1a4fdc2eeaac12ab3c9aa4a1d",
        temporary_output_directory=tmp_path,
    )
    encoded = json.dumps(report, sort_keys=True)

    assert report["synthetic"] is True
    assert report["read_only"] is True
    assert report["redacted"] is True
    assert report["repository_unchanged"] is True
    assert "source_body" not in encoded
    assert "raw_prompt" not in encoded
    assert "hidden_reasoning" not in encoded
    assert "credential:" not in encoded
    for key in (
        "public_network_requests",
        "dns_resolutions",
        "search_provider_calls",
        "connector_calls",
        "model_provider_calls",
        "actual_tool_executions",
        "shell_executions",
        "subprocess_executions",
        "browser_actions",
        "filesystem_mutations",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "deployments",
        "model_weight_changes",
        "persistent_verified_knowledge_writes",
        "automatic_knowledge_promotions",
        "cognitive_memory_writes",
        "belief_mutations",
        "engagement_fact_promotions",
        "engagement_confidence_effects",
    ):
        assert report[key] == 0, key
