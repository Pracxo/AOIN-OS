from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py"
)
REPORT = (
    REPO_ROOT
    / "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json"
)
SUMMARY = (
    REPO_ROOT
    / "examples/knowledge-intelligence/epistemic-assessment-evaluation-scenario-summary.json"
)


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion212_eval", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_operator_evaluation_report_and_docs_record_exact_pass_decision():
    harness = _load_harness()
    payload = json.loads(REPORT.read_text())

    harness.validate_evaluation_report(payload)
    assert payload["decision"] == harness.DECISION_PASS
    assert payload["scenario_count"] == 28
    assert (
        payload["conditional_next_authorization"]["authorization_transaction_id"]
        == "AION-212-KI-0005"
    )

    report_doc = (
        REPO_ROOT / "docs/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.md"
    ).read_text()
    closeout_doc = (
        REPO_ROOT
        / "docs/knowledge-intelligence/epistemic-assessment-operator-evaluation-closeout.md"
    ).read_text()
    assert "AION-EAE-001" in report_doc
    assert harness.DECISION_PASS in report_doc
    assert "AION-210-KI-0004 is closed" in report_doc
    assert "AION-212-KI-0005" in closeout_doc


def test_scenario_summary_matches_report_order():
    harness = _load_harness()
    report = json.loads(REPORT.read_text())
    summary = json.loads(SUMMARY.read_text())

    assert summary["evaluation_id"] == "AION-EAE-001"
    assert summary["scenario_count"] == 28
    assert summary["scenario_ids"] == list(harness.REQUIRED_SCENARIO_IDS)
    assert [item["scenario_id"] for item in report["scenario_results"]] == summary[
        "scenario_ids"
    ]
