"""AION-194 active information-acquisition tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.information_acquisition import (
    InformationNeed,
    RetrievalCandidate,
)
from aion_brain.information_acquisition import (
    InformationAcquisitionPlanner,
    InformationStoppingPolicy,
    KnowledgeGapDetector,
)

NOW = datetime(2026, 7, 22, 1, 0, tzinfo=UTC)


def need(
    need_id: str = "need-release-evidence",
    *,
    current_uncertainty: float = 0.85,
    target_uncertainty: float = 0.15,
    decision_relevance: float = 0.9,
) -> InformationNeed:
    return InformationNeed(
        need_id=need_id,
        decision_id="decision-release-readiness",
        subject="release readiness evidence",
        decision_context="Select the next bounded local evidence request",
        current_uncertainty=current_uncertainty,
        target_uncertainty=target_uncertainty,
        decision_relevance=decision_relevance,
        urgency=0.7,
        evidence_refs=("aion://aion-194/need/release-evidence",),
        created_at=NOW,
    )


def test_information_need_contracts_are_immutable_fingerprinted_and_reference_safe() -> None:
    first = need()
    second = need()

    assert first.fingerprint == second.fingerprint
    assert first.current_uncertainty == 0.85

    with pytest.raises(ValidationError):
        first.subject = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        InformationNeed(
            need_id="need-invalid",
            decision_id="decision-invalid",
            subject="invalid target",
            decision_context="target increases uncertainty",
            current_uncertainty=0.2,
            target_uncertainty=0.4,
            decision_relevance=0.8,
            created_at=NOW,
        )
    with pytest.raises(ValidationError):
        RetrievalCandidate(
            candidate_id="candidate-arbitrary-location",
            need_id="need-invalid",
            gap_id="gap-invalid",
            request_summary="retrieve unapproved location",
            retrieval_ref="https://example.invalid/evidence",
            query_summary="unapproved location",
            created_at=NOW,
        )


def test_knowledge_gap_detector_finds_decision_relevant_uncertainty() -> None:
    gaps = KnowledgeGapDetector().detect(
        (
            need("need-high", current_uncertainty=0.8, target_uncertainty=0.2),
            need("need-low", current_uncertainty=0.12, target_uncertainty=0.1),
        )
    )

    assert len(gaps) == 1
    assert gaps[0].need_id == "need-high"
    assert gaps[0].uncertainty_delta == pytest.approx(0.6)
    assert gaps[0].decision_relevance == 0.9


def test_planner_selects_approved_request_with_best_value_deterministically() -> None:
    planner = InformationAcquisitionPlanner()

    plan = planner.create_plan(
        need=need(),
        permissions={
            "clarification": True,
            "retrieval": True,
            "observation": True,
            "experiment": True,
        },
        approved_refs={
            "retrieval": ("aion://aion-194/approved/release-evidence",),
            "observation": ("operator-approved://aion-194/local-observation",),
        },
        plan_id="aion-194-information-acquisition",
    )
    replay = planner.create_plan(
        need=need(),
        permissions={
            "experiment": True,
            "observation": True,
            "retrieval": True,
            "clarification": True,
        },
        approved_refs={
            "observation": ("operator-approved://aion-194/local-observation",),
            "retrieval": ("aion://aion-194/approved/release-evidence",),
        },
        plan_id="aion-194-information-acquisition",
    )

    assert plan.fingerprint == replay.fingerprint
    assert plan.evidence.uncertainty_detection_count == 1
    assert plan.evidence.permission_enforcement_passed is True
    assert plan.evidence.unauthorized_information_acquisition_count == 0
    assert plan.evidence.forbidden_side_effects == 0
    assert plan.stopping_decision.continue_acquisition is True
    assert plan.selected_candidate_ids == (
        "candidate-gap-need-release-evidence-retrieval",
    )
    selected_gain = next(
        gain
        for gain in plan.gain_estimates
        if gain.candidate_id == plan.selected_candidate_ids[0]
    )
    selected_cost = next(
        cost for cost in plan.costs if cost.candidate_id == plan.selected_candidate_ids[0]
    )
    selected_risk = next(
        risk for risk in plan.risks if risk.candidate_id == plan.selected_candidate_ids[0]
    )
    assert selected_gain.expected_information_gain > (
        selected_cost.total_cost + selected_risk.overall_risk
    )
    assert plan.acquisition_performed is False
    assert plan.external_call_performed is False
    assert plan.tool_execution_performed is False


def test_permission_enforcement_blocks_unapproved_candidates() -> None:
    plan = InformationAcquisitionPlanner().create_plan(
        need=need(),
        permissions={
            "clarification": False,
            "retrieval": False,
            "observation": False,
            "experiment": False,
        },
        plan_id="aion-194-unapproved-plan",
    )

    assert plan.selected_candidate_ids == ()
    assert plan.stopping_decision.continue_acquisition is False
    assert plan.stopping_decision.stopped_because_value_below_cost is True
    assert all(risk.blocked for risk in plan.risks)
    assert all(not candidate.permission_granted for candidate in plan.candidates)
    assert plan.evidence.runtime_boundary.information_acquired is False
    assert plan.evidence.runtime_boundary.unauthorized_information_acquisition == 0


def test_stopping_policy_stops_when_expected_value_falls_below_cost_and_risk() -> None:
    planner = InformationAcquisitionPlanner()
    gap = KnowledgeGapDetector().detect(
        (need(current_uncertainty=0.31, target_uncertainty=0.25, decision_relevance=0.4),)
    )[0]
    ranked = planner.rank_candidates(
        gap=gap,
        permissions={"experiment": True},
        approved_refs={"experiment": ("synthetic://aion-194/local-experiment",)},
    )
    candidate_ids = tuple(
        candidate.candidate_id
        for candidate, _gain, _cost, risk, margin in ranked
        if candidate.candidate_type == "experiment" and not risk.blocked and margin > 0
    )
    decision = InformationStoppingPolicy().decide(
        plan_id="aion-194-low-value",
        selected_candidate_ids=candidate_ids,
        gain_estimates=tuple(item[1] for item in ranked),
        costs=tuple(item[2] for item in ranked),
        risks=tuple(item[3] for item in ranked),
    )

    assert candidate_ids == ()
    assert decision.continue_acquisition is False
    assert decision.stopped_because_value_below_cost is True
    assert decision.unauthorized_information_acquisition_count == 0


def test_clarification_policy_returns_requests_without_asking_them() -> None:
    planner = InformationAcquisitionPlanner()
    plan = planner.create_plan(
        need=need(),
        permissions={"clarification": True},
        plan_id="aion-194-clarification-plan",
    )
    clarification_requests = planner.clarification_items(plan)

    assert len(clarification_requests) == 1
    assert clarification_requests[0].candidate_type == "clarification"
    assert clarification_requests[0].permission_granted is True
    assert plan.acquisition_performed is False
