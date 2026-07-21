"""Offline hierarchical counterfactual planning services."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Literal

from aion_brain.contracts.planning import (
    SCORE_DIMENSIONS,
    ActionProposal,
    CounterfactualBranch,
    ExpectedOutcome,
    HierarchicalPlan,
    MilestonePlan,
    PlanEvidence,
    PlanningRuntimeBoundary,
    PlanResourceEstimate,
    PlanReversibility,
    PlanRisk,
    ReplanningDecision,
    StrategicGoal,
    StrategyOption,
    TaskPlan,
    planning_replay_hash,
)
from aion_brain.contracts.world_model import (
    CounterfactualRollout,
    CounterfactualScenario,
    OutcomePrediction,
    TransitionPrediction,
    WorldFeatureValue,
    WorldState,
)
from aion_brain.world_model import CounterfactualSimulator, TransitionModel

GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)
PlanRiskSeverity = Literal["low", "medium", "high", "critical"]


class StrategicPlanner:
    """Create deterministic proposal-only hierarchical plans."""

    def __init__(
        self,
        *,
        tactical_planner: TacticalPlanner | None = None,
        action_planner: ActionPlanner | None = None,
        counterfactual_evaluator: CounterfactualPlanEvaluator | None = None,
        risk_evaluator: PlanRiskEvaluator | None = None,
        reversibility_evaluator: ReversibilityEvaluator | None = None,
        resource_evaluator: ResourceBudgetEvaluator | None = None,
    ) -> None:
        self._tactical_planner = tactical_planner or TacticalPlanner()
        self._action_planner = action_planner or ActionPlanner()
        self._counterfactual_evaluator = (
            counterfactual_evaluator or CounterfactualPlanEvaluator()
        )
        self._risk_evaluator = risk_evaluator or PlanRiskEvaluator()
        self._reversibility_evaluator = reversibility_evaluator or ReversibilityEvaluator()
        self._resource_evaluator = resource_evaluator or ResourceBudgetEvaluator()

    def rank_strategies(
        self,
        *,
        goal: StrategicGoal,
        start_state: WorldState,
        strategies: Iterable[StrategyOption],
        model: TransitionModel,
    ) -> tuple[CounterfactualBranch, ...]:
        """Return branches sorted by policy eligibility, score, and stable id."""

        branches = [
            self._evaluate_strategy(
                goal=goal,
                start_state=start_state,
                strategy=strategy,
                model=model,
            )
            for strategy in sorted(strategies, key=lambda item: item.strategy_id)
        ]
        return tuple(
            sorted(
                branches,
                key=lambda branch: (
                    branch.blocked,
                    not branch.policy_eligible,
                    -branch.total_score,
                    branch.branch_id,
                ),
            )
        )

    def create_plan(
        self,
        *,
        goal: StrategicGoal,
        start_state: WorldState,
        strategies: Iterable[StrategyOption],
        model: TransitionModel,
        plan_id: str = "hierarchical-plan",
    ) -> HierarchicalPlan:
        """Build a deterministic plan without action dispatch or runtime effects."""

        ranked = self.rank_strategies(
            goal=goal,
            start_state=start_state,
            strategies=strategies,
            model=model,
        )
        eligible = [branch for branch in ranked if not branch.blocked and branch.policy_eligible]
        if not eligible:
            raise ValueError("no policy-eligible counterfactual branch is available")

        selected_branch_id = eligible[0].branch_id
        branches = tuple(
            self._mark_selected(branch, selected=branch.branch_id == selected_branch_id)
            for branch in ranked
        )
        selected_branch = next(branch for branch in branches if branch.selected)
        milestones = self._tactical_planner.create_milestones(
            goal=goal,
            strategy=selected_branch.strategy,
        )
        tasks = (
            self._action_planner.create_task_plan(
                milestone=milestones[0],
                strategy=selected_branch.strategy,
            ),
        )
        replay_hash = planning_replay_hash(
            {
                "plan_id": plan_id,
                "goal": goal,
                "branches": tuple(branch.fingerprint for branch in branches),
                "selected_branch_id": selected_branch_id,
                "milestones": milestones,
                "tasks": tasks,
            }
        )
        evidence = PlanEvidence(
            evidence_id=f"plan-evidence-{plan_id}",
            plan_id=plan_id,
            synthetic_goal_completion_plan_success_rate=selected_branch.score_vector[
                "expected_goal_progress"
            ],
            deterministic_plan_replay_hash=replay_hash,
            runtime_boundary=PlanningRuntimeBoundary(
                boundary_id=f"planning-boundary-{plan_id}",
                created_at=GENERATED_AT,
            ),
            evidence_refs=(
                f"aion://authorization/{goal.goal_id}",
                f"aion://planning/{selected_branch_id}",
            ),
            created_at=GENERATED_AT,
        )
        return HierarchicalPlan(
            plan_id=plan_id,
            goal=goal,
            strategies=tuple(
                sorted(
                    (branch.strategy for branch in branches),
                    key=lambda item: item.strategy_id,
                )
            ),
            milestones=milestones,
            tasks=tasks,
            branches=branches,
            selected_branch_id=selected_branch_id,
            evidence=evidence,
            created_at=GENERATED_AT,
        )

    def _evaluate_strategy(
        self,
        *,
        goal: StrategicGoal,
        start_state: WorldState,
        strategy: StrategyOption,
        model: TransitionModel,
    ) -> CounterfactualBranch:
        action_proposals = self._action_planner.create_action_proposals(strategy)
        rollout, expected_outcomes = self._counterfactual_evaluator.evaluate(
            goal=goal,
            start_state=start_state,
            strategy=strategy,
            model=model,
        )
        branch_id = f"branch-{strategy.strategy_id}"
        reversibility = self._reversibility_evaluator.evaluate(
            branch_id=branch_id,
            action_proposals=action_proposals,
        )
        risk = self._risk_evaluator.evaluate(
            branch_id=branch_id,
            strategy=strategy,
            rollout_failed_closed=not rollout.terminal_distribution,
            reversibility=reversibility,
        )
        resource_estimate = self._resource_evaluator.estimate(
            branch_id=branch_id,
            action_count=len(action_proposals),
        )
        score_vector = _score_vector(
            strategy=strategy,
            expected_outcomes=expected_outcomes,
            risk=risk,
            resource_estimate=resource_estimate,
            reversibility=reversibility,
            rollout_uncertainty=_mean_prediction_uncertainty(rollout.predictions),
        )
        blocked = _branch_blocked(
            strategy=strategy,
            risk=risk,
            resource_estimate=resource_estimate,
            reversibility=reversibility,
        )
        total_score = 0.0 if blocked else _total_score(score_vector)
        return CounterfactualBranch(
            branch_id=branch_id,
            strategy=strategy,
            action_proposals=action_proposals,
            rollout=rollout,
            expected_outcomes=expected_outcomes,
            risk=risk,
            resource_estimate=resource_estimate,
            reversibility=reversibility,
            score_vector=score_vector,
            total_score=total_score,
            blocked=blocked,
            policy_eligible=strategy.policy_eligible and risk.policy_violation_count == 0,
            evidence_refs=(f"aion://planning/{branch_id}",),
            created_at=GENERATED_AT,
        )

    def _mark_selected(
        self,
        branch: CounterfactualBranch,
        *,
        selected: bool,
    ) -> CounterfactualBranch:
        data = branch.model_dump(mode="python", exclude={"fingerprint"})
        data["selected"] = selected
        return CounterfactualBranch(**data)


class TacticalPlanner:
    """Decompose a selected strategy into bounded milestones."""

    def create_milestones(
        self,
        *,
        goal: StrategicGoal,
        strategy: StrategyOption,
    ) -> tuple[MilestonePlan, ...]:
        """Create one deterministic milestone for the selected strategy."""

        return (
            MilestonePlan(
                milestone_id=f"milestone-{strategy.strategy_id}-1",
                strategy_id=strategy.strategy_id,
                title=f"Advance {goal.goal_id} with {strategy.strategy_id}",
                sequence=1,
                goal_progress_target=strategy.expected_goal_progress,
                evidence_refs=(
                    f"aion://goal/{goal.goal_id}",
                    f"aion://strategy/{strategy.strategy_id}",
                ),
                created_at=GENERATED_AT,
            ),
        )


class ActionPlanner:
    """Create proposed action records without action execution."""

    def create_action_proposals(self, strategy: StrategyOption) -> tuple[ActionProposal, ...]:
        """Return one proposal for each referenced action."""

        return tuple(
            ActionProposal(
                proposal_id=f"proposal-{strategy.strategy_id}-{index}",
                strategy_id=strategy.strategy_id,
                action=action,
                sequence=index,
                proposed_payload=dict(action.parameters),
                evidence_refs=(
                    f"aion://strategy/{strategy.strategy_id}",
                    f"aion://world-action/{action.action_id}",
                ),
                created_at=GENERATED_AT,
            )
            for index, action in enumerate(strategy.actions, start=1)
        )

    def create_task_plan(
        self,
        *,
        milestone: MilestonePlan,
        strategy: StrategyOption,
    ) -> TaskPlan:
        """Create a deterministic task wrapper for action proposals."""

        return TaskPlan(
            task_plan_id=f"workitem-{strategy.strategy_id}-1",
            milestone_id=milestone.milestone_id,
            title=f"Prepare proposals for {strategy.strategy_id}",
            sequence=1,
            action_proposals=self.create_action_proposals(strategy),
            evidence_refs=(f"aion://milestone/{milestone.milestone_id}",),
            created_at=GENERATED_AT,
        )


class CounterfactualPlanEvaluator:
    """Evaluate branches through bounded world-model rollouts only."""

    def evaluate(
        self,
        *,
        goal: StrategicGoal,
        start_state: WorldState,
        strategy: StrategyOption,
        model: TransitionModel,
    ) -> tuple[CounterfactualRollout, tuple[ExpectedOutcome, ...]]:
        """Return a rollout and deterministic expected outcomes for a strategy."""

        scenario = CounterfactualScenario(
            scenario_id=f"scenario-{strategy.strategy_id}",
            start_state=start_state,
            actions=strategy.actions,
            max_depth=max(1, len(strategy.actions)),
            evidence_refs=(f"aion://strategy/{strategy.strategy_id}",),
            created_at=GENERATED_AT,
        )
        rollout = CounterfactualSimulator(model).simulate(scenario)
        outcomes = _expected_outcomes(
            goal=goal,
            branch_id=f"branch-{strategy.strategy_id}",
            terminal_distribution=rollout.terminal_distribution,
            fallback_state=start_state,
            fallback_progress=strategy.expected_goal_progress,
        )
        return rollout, outcomes


class PlanRiskEvaluator:
    """Apply hard policy and safety overrides before branch ranking."""

    def evaluate(
        self,
        *,
        branch_id: str,
        strategy: StrategyOption,
        rollout_failed_closed: bool,
        reversibility: PlanReversibility,
    ) -> PlanRisk:
        """Return fail-closed risk metadata for one branch."""

        policy_violation_count = 0 if strategy.policy_eligible else 1
        irreversible_count = 1 if reversibility.irreversible_unsafe else 0
        safety_violation_count = int(rollout_failed_closed or reversibility.irreversible_unsafe)
        severity = _risk_severity(
            policy_violation_count=policy_violation_count,
            safety_violation_count=safety_violation_count,
            irreversible_count=irreversible_count,
        )
        return PlanRisk(
            risk_id=f"planriskbranch-{branch_id}",
            branch_id=branch_id,
            severity=severity,
            policy_violation_count=policy_violation_count,
            safety_violation_count=safety_violation_count,
            irreversible_unsafe_plan_selection_count=irreversible_count,
            rationale=_risk_rationale(
                policy_violation_count=policy_violation_count,
                safety_violation_count=safety_violation_count,
                irreversible_count=irreversible_count,
            ),
            hard_policy_override_applied=policy_violation_count > 0,
            hard_safety_override_applied=safety_violation_count > 0 or irreversible_count > 0,
            evidence_refs=(f"aion://planning/{branch_id}",),
            created_at=GENERATED_AT,
        )


class ReversibilityEvaluator:
    """Classify irreversible unsafe proposals before selection."""

    def evaluate(
        self,
        *,
        branch_id: str,
        action_proposals: tuple[ActionProposal, ...],
    ) -> PlanReversibility:
        """Return reversibility metadata for a branch."""

        irreversible_count = sum(
            1
            for proposal in action_proposals
            if proposal.action.irreversible_effect
        )
        reversible_count = sum(1 for proposal in action_proposals if proposal.action.reversible)
        irreversible_unsafe = irreversible_count > 0
        return PlanReversibility(
            reversibility_id=f"reversibility-{branch_id}",
            branch_id=branch_id,
            reversible_action_count=reversible_count,
            irreversible_action_count=irreversible_count,
            irreversible_unsafe=irreversible_unsafe,
            selected_safe=not irreversible_unsafe,
            rationale=(
                "all action proposals are reversible"
                if not irreversible_unsafe
                else "irreversible unsafe action proposals are rejected"
            ),
            evidence_refs=(f"aion://planning/{branch_id}",),
            created_at=GENERATED_AT,
        )


class ResourceBudgetEvaluator:
    """Create zero-external-resource budget estimates."""

    def estimate(self, *, branch_id: str, action_count: int) -> PlanResourceEstimate:
        """Return a bounded resource estimate with all external counters at zero."""

        time_horizon = max(1, action_count)
        return PlanResourceEstimate(
            estimate_id=f"resource-{branch_id}",
            branch_id=branch_id,
            estimated_steps=action_count,
            time_horizon=time_horizon,
            resource_cost=min(1.0, action_count / 20),
            evidence_refs=(f"aion://planning/{branch_id}",),
            created_at=GENERATED_AT,
        )


class ReplanningService:
    """Decide whether an offline plan should be retained or replanned."""

    def decide(
        self,
        plan: HierarchicalPlan,
        *,
        blocked_branch_ids: tuple[str, ...] = (),
        reason: str | None = None,
    ) -> ReplanningDecision:
        """Return a deterministic replanning decision without side effects."""

        if blocked_branch_ids:
            branch_ids = {branch.branch_id for branch in plan.branches}
            missing = sorted(set(blocked_branch_ids).difference(branch_ids))
            if missing:
                raise ValueError(f"unknown blocked branches: {missing}")
            selected_blocked = plan.selected_branch_id in blocked_branch_ids
            return ReplanningDecision(
                decision_id=f"replanning-{plan.plan_id}",
                plan_id=plan.plan_id,
                status="blocked" if selected_blocked else "replan_required",
                reason=reason
                or (
                    "selected branch is blocked"
                    if selected_blocked
                    else "alternative branch is blocked"
                ),
                blocked_branch_ids=blocked_branch_ids,
                selected_branch_id=plan.selected_branch_id,
                evidence_refs=(f"aion://planning/{plan.plan_id}",),
                created_at=GENERATED_AT,
            )
        selected = next(
            branch
            for branch in plan.branches
            if branch.branch_id == plan.selected_branch_id
        )
        if selected.blocked or selected.risk.severity in {"high", "critical"}:
            return ReplanningDecision(
                decision_id=f"replanning-{plan.plan_id}",
                plan_id=plan.plan_id,
                status="blocked",
                reason=reason or "selected branch is not safe to retain",
                blocked_branch_ids=(selected.branch_id,),
                selected_branch_id=selected.branch_id,
                evidence_refs=(f"aion://planning/{plan.plan_id}",),
                created_at=GENERATED_AT,
            )
        return ReplanningDecision(
            decision_id=f"replanning-{plan.plan_id}",
            plan_id=plan.plan_id,
            status="keep_plan",
            reason=reason or "selected branch remains policy eligible and reversible",
            selected_branch_id=selected.branch_id,
            evidence_refs=(f"aion://planning/{plan.plan_id}",),
            created_at=GENERATED_AT,
        )


def _expected_outcomes(
    *,
    goal: StrategicGoal,
    branch_id: str,
    terminal_distribution: tuple[OutcomePrediction, ...],
    fallback_state: WorldState,
    fallback_progress: float,
) -> tuple[ExpectedOutcome, ...]:
    if not terminal_distribution:
        return (
            ExpectedOutcome(
                outcome_id=f"outcome-{branch_id}-fail-closed",
                branch_id=branch_id,
                terminal_state_id=fallback_state.state_id,
                probability=1.0,
                goal_progress=0.0,
                information_gain=0.0,
                confidence=0.0,
                uncertainty=1.0,
                evidence_refs=(f"aion://planning/{branch_id}",),
                created_at=GENERATED_AT,
            ),
        )
    outcomes: list[ExpectedOutcome] = []
    for index, outcome in enumerate(terminal_distribution, start=1):
        progress = _goal_progress(
            outcome.state.features,
            goal.required_state_features,
            fallback=fallback_progress,
        )
        outcomes.append(
            ExpectedOutcome(
                outcome_id=f"outcome-{branch_id}-{index}",
                branch_id=branch_id,
                terminal_state_id=outcome.state.state_id,
                probability=outcome.probability,
                goal_progress=progress,
                information_gain=1.0 - outcome.confidence,
                confidence=outcome.confidence,
                uncertainty=1.0 - outcome.confidence,
                evidence_refs=outcome.evidence_refs,
                created_at=GENERATED_AT,
            )
        )
    return tuple(outcomes)


def _goal_progress(
    features: dict[str, WorldFeatureValue],
    required_features: dict[str, WorldFeatureValue],
    *,
    fallback: float,
) -> float:
    if not required_features:
        return fallback
    matches = sum(1 for key, value in required_features.items() if features.get(key) == value)
    return matches / len(required_features)


def _weighted_average_outcome(
    outcomes: tuple[ExpectedOutcome, ...],
    attribute: str,
) -> float:
    return min(
        1.0,
        max(
            0.0,
            sum(outcome.probability * float(getattr(outcome, attribute)) for outcome in outcomes),
        ),
    )


def _mean_prediction_uncertainty(predictions: tuple[TransitionPrediction, ...]) -> float:
    if not predictions:
        return 1.0
    return sum(
        prediction.uncertainty.uncertainty_score
        for prediction in predictions
    ) / len(predictions)


def _score_vector(
    *,
    strategy: StrategyOption,
    expected_outcomes: tuple[ExpectedOutcome, ...],
    risk: PlanRisk,
    resource_estimate: PlanResourceEstimate,
    reversibility: PlanReversibility,
    rollout_uncertainty: float,
) -> dict[str, float]:
    vector = {
        "expected_goal_progress": _weighted_average_outcome(
            expected_outcomes,
            "goal_progress",
        ),
        "expected_information_gain": max(
            strategy.expected_information_gain,
            _weighted_average_outcome(expected_outcomes, "information_gain"),
        ),
        "confidence": _weighted_average_outcome(expected_outcomes, "confidence"),
        "risk": _risk_score(risk),
        "resource_cost": 1.0 - resource_estimate.resource_cost,
        "reversibility": 0.0 if reversibility.irreversible_unsafe else 1.0,
        "policy_eligibility": 1.0 if strategy.policy_eligible else 0.0,
        "uncertainty": 1.0 - min(1.0, max(0.0, rollout_uncertainty)),
        "time_horizon": 1.0 / resource_estimate.time_horizon,
    }
    return {dimension: vector[dimension] for dimension in SCORE_DIMENSIONS}


def _total_score(score_vector: dict[str, float]) -> float:
    return sum(score_vector.values()) / len(SCORE_DIMENSIONS)


def _risk_score(risk: PlanRisk) -> float:
    if risk.policy_violation_count or risk.safety_violation_count:
        return 0.0
    return {
        "low": 1.0,
        "medium": 0.75,
        "high": 0.25,
        "critical": 0.0,
    }[risk.severity]


def _risk_severity(
    *,
    policy_violation_count: int,
    safety_violation_count: int,
    irreversible_count: int,
) -> PlanRiskSeverity:
    if policy_violation_count:
        return "critical"
    if safety_violation_count or irreversible_count:
        return "high"
    return "low"


def _risk_rationale(
    *,
    policy_violation_count: int,
    safety_violation_count: int,
    irreversible_count: int,
) -> str:
    if policy_violation_count:
        return "policy failure overrides utility gain"
    if safety_violation_count or irreversible_count:
        return "safety failure overrides utility gain"
    return "no policy or safety violation detected"


def _branch_blocked(
    *,
    strategy: StrategyOption,
    risk: PlanRisk,
    resource_estimate: PlanResourceEstimate,
    reversibility: PlanReversibility,
) -> bool:
    return (
        not strategy.policy_eligible
        or risk.policy_violation_count > 0
        or risk.safety_violation_count > 0
        or risk.irreversible_unsafe_plan_selection_count > 0
        or resource_estimate.budget_overrun_count > 0
        or reversibility.irreversible_unsafe
    )


__all__ = [
    "ActionPlanner",
    "CounterfactualPlanEvaluator",
    "GENERATED_AT",
    "PlanRiskEvaluator",
    "ResourceBudgetEvaluator",
    "ReplanningService",
    "ReversibilityEvaluator",
    "StrategicPlanner",
    "TacticalPlanner",
]
