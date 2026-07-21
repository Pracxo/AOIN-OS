"""AION-192 hierarchical counterfactual planning tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.planning import (
    ActionProposal,
    StrategicGoal,
    StrategyOption,
)
from aion_brain.contracts.world_model import TransitionEvidence, WorldActionReference, WorldState
from aion_brain.planning import ReplanningService, StrategicPlanner
from aion_brain.world_model import ProbabilisticTransitionModel

NOW = datetime(2026, 7, 21, 10, 0, tzinfo=UTC)


def state(state_id: str, **features: str | int | float | bool) -> WorldState:
    return WorldState(
        state_id=state_id,
        features=features,
        provenance_refs=(f"aion://world-state/{state_id}",),
        observed_at=NOW,
    )


def action(
    action_id: str,
    name: str,
    *,
    reversible: bool = True,
    irreversible_effect: bool = False,
) -> WorldActionReference:
    return WorldActionReference(
        action_id=action_id,
        name=name,
        reversible=reversible,
        irreversible_effect=irreversible_effect,
        evidence_refs=(f"aion://world-action/{action_id}",),
        created_at=NOW,
    )


def transition(
    evidence_id: str,
    source: WorldState,
    world_action: WorldActionReference,
    outcome: WorldState,
) -> TransitionEvidence:
    return TransitionEvidence(
        evidence_id=evidence_id,
        source_state=source,
        action=world_action,
        outcome_state=outcome,
        evidence_refs=(f"aion://transition/{evidence_id}",),
        observed_at=NOW,
    )


def synthetic_evidence() -> tuple[TransitionEvidence, ...]:
    idle = state("state-idle", location="hub", status="idle", load=1)
    ready = state("state-ready", location="hub", status="ready", load=2)
    retry = state("state-retry", location="hub", status="retry", load=1)
    locked = state("state-locked", location="vault", status="locked", load=2)
    inspect = action("action-inspect", "inspect")
    lock = action("action-lock", "lock", reversible=False, irreversible_effect=True)
    return (
        transition("evidence-inspect-1", idle, inspect, ready),
        transition("evidence-inspect-2", idle, inspect, ready),
        transition("evidence-inspect-3", idle, inspect, ready),
        transition("evidence-inspect-4", idle, inspect, retry),
        transition("evidence-lock-1", idle, lock, locked),
        transition("evidence-lock-2", idle, lock, locked),
    )


def planning_fixture() -> tuple[
    StrategicGoal,
    StrategyOption,
    StrategyOption,
    WorldState,
    ProbabilisticTransitionModel,
]:
    evidence = synthetic_evidence()
    idle = evidence[0].source_state
    inspect = evidence[0].action
    lock = evidence[-1].action
    goal = StrategicGoal(
        goal_id="goal-prepare-hub",
        description="Prepare the hub workspace for review",
        priority=90,
        success_criteria=("hub location remains available",),
        required_state_features={"location": "hub"},
        evidence_refs=("aion://goal/prepare-hub",),
        created_at=NOW,
    )
    safe_strategy = StrategyOption(
        strategy_id="inspect-hub",
        goal_id=goal.goal_id,
        title="Inspect the hub",
        rationale="Inspecting is reversible and keeps the workspace available.",
        actions=(inspect,),
        expected_information_gain=0.6,
        expected_goal_progress=0.9,
        evidence_refs=("aion://strategy/inspect-hub",),
        created_at=NOW,
    )
    unsafe_strategy = StrategyOption(
        strategy_id="lock-vault",
        goal_id=goal.goal_id,
        title="Lock the vault",
        rationale="Locking appears decisive but creates an irreversible unsafe branch.",
        actions=(lock,),
        expected_information_gain=0.2,
        expected_goal_progress=1.0,
        evidence_refs=("aion://strategy/lock-vault",),
        created_at=NOW,
    )
    return (
        goal,
        safe_strategy,
        unsafe_strategy,
        idle,
        ProbabilisticTransitionModel(evidence=evidence),
    )


def test_planning_contracts_are_immutable_fingerprinted_and_proposal_only() -> None:
    inspect = action("action-contract-inspect", "inspect")
    goal = StrategicGoal(
        goal_id="goal-contract",
        description="Prepare a bounded local plan",
        priority=50,
        required_state_features={"location": "hub"},
        created_at=NOW,
    )
    same_goal = StrategicGoal(
        goal_id="goal-contract",
        description="Prepare a bounded local plan",
        priority=50,
        required_state_features={"location": "hub"},
        created_at=NOW,
    )

    assert goal.fingerprint == same_goal.fingerprint
    assert goal.required_state_features["location"] == "hub"

    with pytest.raises(ValidationError):
        goal.goal_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        goal.required_state_features["location"] = "vault"
    with pytest.raises(ValidationError):
        StrategicGoal(
            goal_id="goal-secret",
            description="Prepare",
            priority=10,
            required_state_features={"api_key": "sk-test"},
            created_at=NOW,
        )
    with pytest.raises(ValidationError):
        ActionProposal(
            proposal_id="proposal-execute",
            strategy_id="strategy-contract",
            action=inspect,
            sequence=1,
            execution_allowed=True,
            created_at=NOW,
        )


def test_hierarchical_plan_selects_safe_counterfactual_branch_deterministically() -> None:
    goal, safe_strategy, unsafe_strategy, idle, model = planning_fixture()
    planner = StrategicPlanner()

    plan = planner.create_plan(
        goal=goal,
        start_state=idle,
        strategies=(unsafe_strategy, safe_strategy),
        model=model,
        plan_id="plan-prepare-hub",
    )
    replay = planner.create_plan(
        goal=goal,
        start_state=idle,
        strategies=(safe_strategy, unsafe_strategy),
        model=model,
        plan_id="plan-prepare-hub",
    )

    selected = next(branch for branch in plan.branches if branch.selected)
    unsafe = next(branch for branch in plan.branches if branch.strategy.strategy_id == "lock-vault")

    assert plan.fingerprint == replay.fingerprint
    assert (
        plan.evidence.deterministic_plan_replay_hash
        == replay.evidence.deterministic_plan_replay_hash
    )
    assert selected.strategy.strategy_id == "inspect-hub"
    assert selected.score_vector["expected_goal_progress"] >= 0.8
    assert plan.evidence.synthetic_goal_completion_plan_success_rate >= 0.8
    assert plan.evidence.policy_violation_count == 0
    assert plan.evidence.budget_overrun_count == 0
    assert plan.evidence.irreversible_unsafe_plan_selection_count == 0
    assert plan.evidence.deterministic_plan_replay_rate == 1.0
    assert plan.evidence.forbidden_side_effects == 0
    assert unsafe.blocked is True
    assert unsafe.selected is False
    assert unsafe.risk.irreversible_unsafe_plan_selection_count == 1
    assert unsafe.reversibility.irreversible_unsafe is True
    for task in plan.tasks:
        for proposal in task.action_proposals:
            assert proposal.execution_allowed is False
            assert proposal.dispatch_performed is False
            assert proposal.external_call_performed is False
            assert proposal.status == "proposed"


def test_policy_and_safety_override_utility_gain() -> None:
    goal, safe_strategy, unsafe_strategy, idle, model = planning_fixture()
    blocked_policy_strategy = StrategyOption(
        strategy_id="policy-blocked",
        goal_id=goal.goal_id,
        title="Policy blocked path",
        rationale="The path is explicitly not policy eligible.",
        actions=safe_strategy.actions,
        expected_information_gain=1.0,
        expected_goal_progress=1.0,
        policy_eligible=False,
        created_at=NOW,
    )

    branches = StrategicPlanner().rank_strategies(
        goal=goal,
        start_state=idle,
        strategies=(unsafe_strategy, blocked_policy_strategy, safe_strategy),
        model=model,
    )

    assert branches[0].strategy.strategy_id == "inspect-hub"
    assert branches[0].blocked is False
    assert branches[1].blocked is True
    assert branches[2].blocked is True
    assert {branch.strategy.strategy_id for branch in branches[1:]} == {
        "lock-vault",
        "policy-blocked",
    }


def test_replanning_service_keeps_safe_plan_and_flags_blocked_branches() -> None:
    goal, safe_strategy, unsafe_strategy, idle, model = planning_fixture()
    plan = StrategicPlanner().create_plan(
        goal=goal,
        start_state=idle,
        strategies=(safe_strategy, unsafe_strategy),
        model=model,
        plan_id="plan-replanning",
    )
    unsafe = next(branch for branch in plan.branches if branch.strategy.strategy_id == "lock-vault")
    service = ReplanningService()

    keep = service.decide(plan)
    replan = service.decide(plan, blocked_branch_ids=(unsafe.branch_id,))
    blocked = service.decide(plan, blocked_branch_ids=(plan.selected_branch_id,))

    assert keep.status == "keep_plan"
    assert keep.blocked_branch_ids == ()
    assert replan.status == "replan_required"
    assert replan.blocked_branch_ids == (unsafe.branch_id,)
    assert blocked.status == "blocked"
    assert blocked.blocked_branch_ids == (plan.selected_branch_id,)
