"""AION-182 operator-evaluation closeout document tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "scripts" / "lib"

if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

from self_improvement_shadow_activation_operator_evaluation import (  # noqa: E402
    PASS_DECISION,
    SCENARIO_IDS,
    validate_operator_evaluation_report,
)

REQUIRED_FILES = (
    "docs/self-improvement/shadow-activation-control-plane-operator-evaluation-closeout.md",
    "docs/self-improvement/shadow-activation-control-plane-operator-evaluation-report.md",
    "docs/self-improvement/shadow-activation-control-plane-evaluation-scenarios.md",
    "docs/self-improvement/actual-shadow-activation-decision-boundary.md",
    "docs/release/self-improvement-shadow-activation-control-plane-evaluation-closeout.md",
    "docs/release/self-improvement-shadow-activation-control-plane-evaluation-checklist.md",
    "docs/release/self-improvement-shadow-activation-control-plane-evaluation-evidence-matrix.md",
    "docs/release/self-improvement-shadow-activation-control-plane-evaluation-runtime-hold.md",
    "docs/adr/0167-shadow-activation-control-plane-operator-evaluation.md",
    "examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json",
    "examples/self-improvement/shadow-activation-control-plane-evaluation-scenario-summary.json",
    "examples/self-improvement/actual-shadow-activation-review-boundary.json",
    "operator-console-static/demo-data/self-improvement-shadow-activation-control-plane-evaluation.json",
    "operator-console-static/demo-data/self-improvement-actual-shadow-activation-review-boundary.json",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def test_aion_182_required_docs_and_examples_exist() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative


def test_aion_182_report_and_scenario_summary_are_consistent() -> None:
    report = _json(
        "examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json"
    )
    summary = _json(
        "examples/self-improvement/shadow-activation-control-plane-evaluation-scenario-summary.json"
    )

    validate_operator_evaluation_report(report)
    assert report["decision"] == PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 21
    assert tuple(item["scenario_id"] for item in report["scenario_results"]) == SCENARIO_IDS
    assert all(item["passed"] for item in report["scenario_results"])
    assert summary["evaluation_id"] == report["evaluation_id"]
    assert summary["decision"] == report["decision"]
    assert summary["scenario_count"] == report["scenario_count"]
    assert tuple(item["scenario_id"] for item in summary["scenarios"]) == SCENARIO_IDS


def test_aion_182_docs_record_decision_and_non_approval_boundary() -> None:
    closeout = (
        ROOT
        / "docs/self-improvement/shadow-activation-control-plane-operator-evaluation-closeout.md"
    ).read_text()
    boundary = _json("examples/self-improvement/actual-shadow-activation-review-boundary.json")
    adr_index = (ROOT / "docs/adr/README.md").read_text()
    app = (ROOT / "operator-console-static/app.js").read_text()

    assert "AION-180-SI-0007 is closed" in closeout
    assert PASS_DECISION in closeout
    assert boundary["evaluation_used_as_approval"] is False
    assert boundary["evaluation_reusable"] is False
    assert boundary["actual_activation_authorized"] is False
    assert boundary["next_authorization_must_be_separate"] is True
    assert "0167-shadow-activation-control-plane-operator-evaluation.md" in adr_index
    assert "self_improvement_shadow_activation_control_plane_evaluation" in app
    assert "self_improvement_actual_shadow_activation_review_boundary" in app
