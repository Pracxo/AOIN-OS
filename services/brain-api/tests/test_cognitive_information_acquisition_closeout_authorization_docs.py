"""AION-195 information-acquisition closeout and learning authorization tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from aion_brain.contracts.information_acquisition import InformationNeed
from aion_brain.information_acquisition import InformationAcquisitionPlanner

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION193_AUTHORIZATION_ID,
    AION194_MERGE_COMMIT,
    AION194_PR,
    AION194_TASK_ID,
    AION195_AUTHORIZATION_ID,
    AION195_EVALUATION_ID,
    AION196_SCOPE,
    AION196_TASK_ID,
    AION197_EVALUATION_ID,
    AION197_TASK_ID,
    AION198_AUTHORIZATION_ID,
    AION200_EVALUATION_ID,
    AION200_TASK_ID,
    AION201_AUTHORIZATION_ID,
    CONTINUAL_LEARNING_REQUIRED_CONTRACTS,
    CONTINUAL_LEARNING_REQUIRED_SERVICES,
    PROGRAM_ID,
    validate_aion195_authorization_payload,
    validate_aion195_evaluation_payload,
    validate_information_acquisition_closeout,
    validate_information_acquisition_closeout_no_go,
)

NOW = datetime(2026, 7, 22, 2, 0, tzinfo=UTC)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-195.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json",
    "examples/cognitive-architecture/aion-195-continual-learning-authorization.json",
    "services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py",
    "scripts/cognitive-information-acquisition-closeout-check.sh",
    "scripts/cognitive-information-acquisition-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _aion_196_implemented() -> bool:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    return any(
        item.get("implementation_task") == AION196_TASK_ID
        for item in program["records"]
    )


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
        evidence_refs=("aion://aion-195/need/release-evidence",),
        created_at=NOW,
    )


def _evaluation_plans():
    planner = InformationAcquisitionPlanner()
    primary = planner.create_plan(
        need=need(),
        permissions={
            "clarification": True,
            "retrieval": True,
            "observation": True,
            "experiment": True,
        },
        approved_refs={
            "retrieval": ("aion://aion-195/approved/release-evidence",),
            "observation": ("operator-approved://aion-195/local-observation",),
        },
        plan_id="aion-195-information-acquisition-evaluation",
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
            "observation": ("operator-approved://aion-195/local-observation",),
            "retrieval": ("aion://aion-195/approved/release-evidence",),
        },
        plan_id="aion-195-information-acquisition-evaluation",
    )
    blocked = planner.create_plan(
        need=need("need-permission-block"),
        permissions={
            "clarification": False,
            "retrieval": False,
            "observation": False,
            "experiment": False,
        },
        plan_id="aion-195-permission-block",
    )
    low_value = planner.create_plan(
        need=need(
            "need-low-value",
            current_uncertainty=0.31,
            target_uncertainty=0.25,
            decision_relevance=0.4,
        ),
        permissions={"experiment": True},
        approved_refs={"experiment": ("synthetic://aion-195/local-experiment",)},
        plan_id="aion-195-low-value",
    )
    clarification = planner.create_plan(
        need=need("need-clarification"),
        permissions={"clarification": True},
        plan_id="aion-195-clarification",
    )
    return planner, primary, replay, blocked, low_value, clarification


def _evaluation_metrics() -> dict[str, float | int]:
    planner, primary, replay, blocked, low_value, clarification = _evaluation_plans()
    selected_id = primary.selected_candidate_ids[0]
    selected_gain = next(
        gain for gain in primary.gain_estimates if gain.candidate_id == selected_id
    )
    selected_cost = next(cost for cost in primary.costs if cost.candidate_id == selected_id)
    selected_risk = next(risk for risk in primary.risks if risk.candidate_id == selected_id)
    clarification_requests = planner.clarification_items(clarification)
    plans = (primary, blocked, low_value, clarification)
    forbidden_side_effects = any(
        plan.acquisition_performed
        or plan.external_call_performed
        or plan.tool_execution_performed
        or plan.hidden_mutation_performed
        or plan.evidence.runtime_boundary.runtime_effect
        or plan.evidence.runtime_boundary.network_calls
        or plan.evidence.runtime_boundary.connector_calls
        or plan.evidence.runtime_boundary.model_provider_calls
        or plan.evidence.runtime_boundary.tool_execution
        or plan.evidence.runtime_boundary.information_acquired
        or plan.evidence.runtime_boundary.background_loop
        or plan.evidence.runtime_boundary.source_rewrite
        or plan.evidence.runtime_boundary.git_mutation
        or plan.evidence.runtime_boundary.production_exposure
        or plan.evidence.runtime_boundary.model_weights_changed
        for plan in plans
    )
    unauthorized_count = sum(
        plan.evidence.unauthorized_information_acquisition_count
        + plan.evidence.runtime_boundary.unauthorized_information_acquisition
        for plan in plans
    )
    permission_violations = len(blocked.selected_candidate_ids) + sum(
        1 for candidate in blocked.candidates if candidate.permission_granted
    )
    cost_risk_violations = int(
        selected_gain.expected_information_gain
        <= selected_cost.total_cost + selected_risk.overall_risk
    )
    return {
        "uncertainty_detection_rate": 1.0
        if primary.evidence.uncertainty_detection_count == 1
        else 0.0,
        "expected_information_gain_positive_rate": 1.0
        if all(gain.expected_information_gain > 0 for gain in primary.gain_estimates)
        else 0.0,
        "candidate_ranking_deterministic_rate": 1.0
        if primary.fingerprint == replay.fingerprint
        and primary.selected_candidate_ids == replay.selected_candidate_ids
        else 0.0,
        "cost_risk_constraint_violation_count": cost_risk_violations,
        "clarification_quality_rate": 1.0
        if len(clarification_requests) == 1
        and clarification_requests[0].permission_granted
        and "approved local evidence" in clarification_requests[0].clarification_question
        and not clarification.acquisition_performed
        else 0.0,
        "stopping_decision_accuracy": 1.0
        if primary.stopping_decision.continue_acquisition
        and not blocked.stopping_decision.continue_acquisition
        and not low_value.stopping_decision.continue_acquisition
        and low_value.stopping_decision.stopped_because_value_below_cost
        else 0.0,
        "permission_enforcement_violation_count": permission_violations,
        "unauthorized_information_acquisition_count": unauthorized_count,
        "forbidden_side_effects": 1 if forbidden_side_effects else 0,
    }


def test_aion_195_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.exists(), f"missing {relative}"
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), f"not executable: {relative}"


def test_aion_195_ledgers_examples_and_no_go_validate() -> None:
    validate_information_acquisition_closeout(ROOT)
    validate_information_acquisition_closeout_no_go(ROOT)
    validate_aion195_evaluation_payload(
        _json("examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json")
    )
    validate_aion195_authorization_payload(
        _json("examples/cognitive-architecture/aion-195-continual-learning-authorization.json")
    )

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")

    assert program["program_id"] == PROGRAM_ID
    aion197_closed = any(
        item.get("task_id") == AION197_TASK_ID
        and item.get("evaluation_id") == AION197_EVALUATION_ID
        for item in program["records"]
    )
    aion198_authorized = any(
        item.get("authorization_id") == AION198_AUTHORIZATION_ID
        for item in program["records"]
    )
    aion200_evaluated = any(
        item.get("task_id") == AION200_TASK_ID
        and item.get("evaluation_id") == AION200_EVALUATION_ID
        for item in program["records"]
    )
    aion201_authorized = any(
        item.get("authorization_id") == AION201_AUTHORIZATION_ID
        for item in program["records"]
    )
    if aion197_closed:
        expected_active = (
            AION201_AUTHORIZATION_ID
            if aion201_authorized
            else None
            if aion200_evaluated
            else AION198_AUTHORIZATION_ID
            if aion198_authorized
            else None
        )
        expected_count = (
            1
            if aion201_authorized
            else 0
            if aion200_evaluated
            else 1
            if aion198_authorized
            else 0
        )
        assert program["active_cognitive_implementation_authorization"] == expected_active
        assert authorization["active_cognitive_implementation_authorization"] == expected_active
        assert program["active_cognitive_implementation_authorization_count"] == expected_count
        assert (
            authorization["active_cognitive_implementation_authorization_count"]
            == expected_count
        )
    else:
        assert program["active_cognitive_implementation_authorization"] == AION195_AUTHORIZATION_ID
        assert (
            authorization["active_cognitive_implementation_authorization"]
            == AION195_AUTHORIZATION_ID
        )
        assert authorization["active_cognitive_implementation_authorization_count"] == 1

    implementation = next(
        item for item in program["records"] if item.get("implementation_task") == AION194_TASK_ID
    )
    assert implementation["pr"] == AION194_PR
    assert implementation["merge_commit"] == AION194_MERGE_COMMIT
    assert implementation["task_state"] == "merged_evaluated_passed"

    closed = next(
        item
        for item in authorization["records"]
        if item["authorization_id"] == AION193_AUTHORIZATION_ID
    )
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False
    assert closed["authorization_closeout_evaluation"] == AION195_EVALUATION_ID
    assert closed["implementation_pr"] == AION194_PR
    assert closed["implementation_merge_commit"] == AION194_MERGE_COMMIT

    active = next(
        item
        for item in authorization["records"]
        if item["authorization_id"] == AION195_AUTHORIZATION_ID
    )
    assert active["authorization_active"] is not aion197_closed
    assert active["authorization_consumed"] is aion197_closed
    assert active["authorization_expired"] is aion197_closed
    if aion197_closed:
        assert active["authorization_closed_by_task"] == AION197_TASK_ID
        assert active["authorization_closeout_evaluation"] == AION197_EVALUATION_ID
    assert active["implementation_task"] == AION196_TASK_ID
    assert active["scope"] == AION196_SCOPE
    assert set(CONTINUAL_LEARNING_REQUIRED_CONTRACTS).issubset(active["required_contracts"])
    assert set(CONTINUAL_LEARNING_REQUIRED_SERVICES).issubset(active["required_services"])


def test_aion_195_information_acquisition_evaluation_meets_thresholds() -> None:
    payload = _json(
        "examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json"
    )
    planner, primary, replay, blocked, low_value, clarification = _evaluation_plans()
    metrics = _evaluation_metrics()

    assert metrics == payload["hard_pass_conditions"]
    assert set(payload["evaluation_matrix"].values()) == {"PASS"}
    assert primary.fingerprint == replay.fingerprint
    assert primary.selected_candidate_ids == (
        "candidate-gap-need-release-evidence-retrieval",
    )
    assert primary.evidence.permission_enforcement_passed is True
    assert primary.evidence.unauthorized_information_acquisition_count == 0
    assert primary.evidence.forbidden_side_effects == 0
    assert blocked.selected_candidate_ids == ()
    assert all(risk.blocked for risk in blocked.risks)
    assert low_value.stopping_decision.stopped_because_value_below_cost is True
    assert not low_value.stopping_decision.continue_acquisition
    assert len(planner.clarification_items(clarification)) == 1
    assert all(
        not plan.acquisition_performed for plan in (primary, blocked, low_value, clarification)
    )


def test_aion_195_does_not_implement_aion_196_runtime_surface() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/continual_learning.py").exists()
    if _aion_196_implemented():
        assert (ROOT / "services/brain-api/src/aion_brain/continual_learning").is_dir()
        assert (
            ROOT / "services/brain-api/src/aion_brain/contracts/continual_learning.py"
        ).is_file()
    else:
        assert not (ROOT / "services/brain-api/src/aion_brain/continual_learning").exists()
        assert not (
            ROOT / "services/brain-api/src/aion_brain/contracts/continual_learning.py"
        ).exists()

    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "ExperienceReplayService" not in text
        assert "aion_brain.continual_learning" not in text


def test_aion_195_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-195 focused script test",
    }
    scripts = (
        "scripts/cognitive-information-acquisition-closeout-no-go-regression.sh",
        "scripts/cognitive-information-acquisition-closeout-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
