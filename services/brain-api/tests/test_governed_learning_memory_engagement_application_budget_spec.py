from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from scripts.lib import governed_learning_memory_local_persistence_operator_evaluation as eval225

from aion_brain.contracts.governed_engagement_learning import (
    RESOURCE_LIMITS,
    EngagementApplicationBudgetDecision,
    EngagementApplicationResourceBudget,
    EngagementApplicationResourceUsage,
    build_record,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_resource_budgets_are_exact():
    auth = load_json("examples/governed-learning-memory/engagement-application-authorization.json")
    assert auth["resource_limits"] == eval225.AION226_RESOURCE_LIMITS
    assert auth["resource_limits"]["maximum_persistent_engagement_overlay_writes"] == 0
    assert auth["resource_limits"]["maximum_aion_224_store_writes"] == 0


def _budget() -> EngagementApplicationResourceBudget:
    return build_record(
        EngagementApplicationResourceBudget,
        {
            "budget_id": "budget-regression",
            "limits": dict(RESOURCE_LIMITS),
            "runtime_effect": False,
        },
        "budget_fingerprint",
    )


def _usage(**overrides) -> EngagementApplicationResourceUsage:
    payload = {
        "usage_id": "usage-regression",
        "engagement_candidates": 1,
        "signal_references_per_candidate": 1,
        "candidate_versions": 1,
        "target_components": 1,
        "approval_records": 1,
        "adaptation_plans": 1,
        "overlay_records": 1,
        "overlay_versions": 1,
        "overlay_snapshots": 1,
        "counterfactual_cases": 1,
        "metrics_per_case": 1,
        "comparisons": 1,
        "rollback_steps": 1,
        "operator_review_items": 1,
        "query_results": 0,
        "fixture_records": 1,
        "fixture_bytes": 1,
        "concurrency": 1,
        "runtime_effect": False,
    }
    payload.update(overrides)
    return build_record(EngagementApplicationResourceUsage, payload, "usage_fingerprint")


def test_engagement_budget_decision_rejects_one_over_limit_pass():
    with pytest.raises(ValidationError, match="resource budget violation"):
        build_record(
            EngagementApplicationBudgetDecision,
            {
                "decision_id": "budget-decision-over-limit",
                "budget": _budget(),
                "usage": _usage(
                    engagement_candidates=RESOURCE_LIMITS[
                        "maximum_engagement_candidates_per_batch"
                    ]
                    + 1
                ),
                "budget_passed": True,
                "reason_codes": ("engagement_resource_budget_passed",),
                "runtime_effect": False,
            },
            "decision_fingerprint",
        )


def test_engagement_budget_decision_allows_fail_closed_over_limit():
    decision = build_record(
        EngagementApplicationBudgetDecision,
        {
            "decision_id": "budget-decision-fail-closed",
            "budget": _budget(),
            "usage": _usage(
                engagement_candidates=RESOURCE_LIMITS[
                    "maximum_engagement_candidates_per_batch"
                ]
                + 1
            ),
            "budget_passed": False,
            "reason_codes": ("engagement_resource_budget_failed",),
            "runtime_effect": False,
        },
        "decision_fingerprint",
    )

    assert decision.budget_passed is False
