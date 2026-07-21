"""Planning contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.cognitive_state import (
    FrozenDict,
    fingerprint_model,
    fingerprint_payload,
    freeze_payload,
)
from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.world_model import (
    CounterfactualRollout,
    WorldActionReference,
    WorldFeatureValue,
)

SCHEMA_VERSION = "counterfactual-planning/v1"
CANONICALIZATION_VERSION = "counterfactual-planning-canonical-json/v1"
AUTHORIZATION_ID = "AION-191-CA-0005"
IMPLEMENTATION_TASK = "AION-192"

SCORE_DIMENSIONS = (
    "expected_goal_progress",
    "expected_information_gain",
    "confidence",
    "risk",
    "resource_cost",
    "reversibility",
    "policy_eligibility",
    "uncertainty",
    "time_horizon",
)

GoalStatus = Literal["active", "paused", "complete", "blocked"]
StrategyStatus = Literal["candidate", "selected", "rejected", "blocked"]
MilestoneStatus = Literal["planned", "blocked", "complete"]
TaskStatus = Literal["planned", "blocked", "complete"]
ActionProposalStatus = Literal["proposed", "rejected", "blocked"]
RiskSeverity = Literal["low", "medium", "high", "critical"]
ReplanningStatus = Literal["keep_plan", "replan_required", "blocked"]


class PlanStep(BaseModel):
    """A deterministic, policy-checkable plan step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    action_type: str
    capability_required: str | None
    risk_level: str
    status: str


class PlanGraph(BaseModel):
    """A policy-checkable plan graph."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    intent_id: str
    goal: str
    steps: list[PlanStep]
    dependencies: list[dict[str, Any]]
    risk_level: str
    approval_required: bool
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CounterfactualPlanningModel(BaseModel):
    """Base model for immutable counterfactual-planning contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class CounterfactualPlanningFingerprintedModel(CounterfactualPlanningModel):
    """Immutable planning model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical planning payload")
        return self


class PlanningRuntimeBoundary(CounterfactualPlanningFingerprintedModel):
    """Explicit proof that planning contracts remain offline proposal records."""

    boundary_id: str = Field(min_length=1)
    runtime_effect: bool = False
    direct_action_execution: bool = False
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    model_call_made: bool = False
    production_exposure: bool = False
    model_weights_changed: bool = False
    source_rewrite: bool = False
    background_planning_loop: bool = False
    git_mutation: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("boundary_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "planning boundary id")
        return value.strip()

    @model_validator(mode="after")
    def runtime_flags_must_remain_disabled(self) -> Self:
        for key in (
            "runtime_effect",
            "direct_action_execution",
            "model_call_made",
            "production_exposure",
            "model_weights_changed",
            "source_rewrite",
            "background_planning_loop",
            "git_mutation",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        for key in ("network_calls", "connector_calls", "model_provider_calls"):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class StrategicGoal(CounterfactualPlanningFingerprintedModel):
    """A bounded goal that can be decomposed into strategy and action proposals."""

    goal_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: int = Field(ge=0, le=100)
    success_criteria: tuple[str, ...] = Field(default_factory=tuple)
    required_state_features: dict[str, WorldFeatureValue] = Field(default_factory=dict)
    status: GoalStatus = "active"
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("goal_id", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "strategic goal text")
        return value.strip()

    @field_validator("success_criteria", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "strategic goal ref")
        return value

    @field_validator("required_state_features", mode="after")
    @classmethod
    def features_must_be_safe(
        cls,
        value: dict[str, WorldFeatureValue],
    ) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "strategic goal feature key")
            if isinstance(nested, str):
                reject_hidden_or_secret_text(nested, "strategic goal feature value")
        return cast(FrozenDict, freeze_payload(value))


class StrategyOption(CounterfactualPlanningFingerprintedModel):
    """A candidate strategy for satisfying a strategic goal."""

    strategy_id: str = Field(min_length=1)
    goal_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    actions: tuple[WorldActionReference, ...]
    expected_information_gain: float = Field(ge=0.0, le=1.0)
    expected_goal_progress: float = Field(ge=0.0, le=1.0)
    risk_tolerance: RiskSeverity = "low"
    policy_eligible: bool = True
    resource_budget: dict[str, int] = Field(default_factory=dict)
    status: StrategyStatus = "candidate"
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("strategy_id", "goal_id", "title", "rationale")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "strategy option text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "strategy option ref")
        return value

    @field_validator("resource_budget", mode="after")
    @classmethod
    def budget_must_be_safe(cls, value: dict[str, int]) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "strategy budget key")
            if nested < 0:
                raise ValueError("strategy budget values must be non-negative")
        return cast(FrozenDict, freeze_payload(value))

    @model_validator(mode="after")
    def actions_are_required(self) -> Self:
        if not self.actions:
            raise ValueError("strategy options require at least one action reference")
        return self


class MilestonePlan(CounterfactualPlanningFingerprintedModel):
    """One deterministic milestone in a hierarchical plan."""

    milestone_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    goal_progress_target: float = Field(ge=0.0, le=1.0)
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    status: MilestoneStatus = "planned"
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("milestone_id", "strategy_id", "title")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "milestone text")
        return value.strip()

    @field_validator("dependencies", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "milestone ref")
        return value


class ActionProposal(CounterfactualPlanningFingerprintedModel):
    """A proposed action reference; it is never executed or dispatched."""

    proposal_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    action: WorldActionReference
    sequence: int = Field(ge=1)
    status: ActionProposalStatus = "proposed"
    execution_allowed: bool = False
    dispatch_performed: bool = False
    external_call_performed: bool = False
    proposed_payload: dict[str, WorldFeatureValue] = Field(default_factory=dict)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("proposal_id", "strategy_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "action proposal text")
        return value.strip()

    @field_validator("proposed_payload", mode="after")
    @classmethod
    def payload_must_be_safe(
        cls,
        value: dict[str, WorldFeatureValue],
    ) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "action proposal payload key")
            if isinstance(nested, str):
                reject_hidden_or_secret_text(nested, "action proposal payload value")
        return cast(FrozenDict, freeze_payload(value))

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "action proposal ref")
        return value

    @model_validator(mode="after")
    def proposals_must_not_execute(self) -> Self:
        if self.execution_allowed:
            raise ValueError("execution_allowed must be false")
        if self.dispatch_performed:
            raise ValueError("dispatch_performed must be false")
        if self.external_call_performed:
            raise ValueError("external_call_performed must be false")
        return self


class TaskPlan(CounterfactualPlanningFingerprintedModel):
    """A bounded task group under one milestone."""

    task_plan_id: str = Field(min_length=1)
    milestone_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    action_proposals: tuple[ActionProposal, ...]
    status: TaskStatus = "planned"
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("task_plan_id", "milestone_id", "title")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "task plan text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "task plan ref")
        return value

    @model_validator(mode="after")
    def task_requires_proposals(self) -> Self:
        if not self.action_proposals:
            raise ValueError("task plans require at least one action proposal")
        return self


class ExpectedOutcome(CounterfactualPlanningFingerprintedModel):
    """Expected outcome summary for a bounded counterfactual branch."""

    outcome_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    terminal_state_id: str = Field(min_length=1)
    probability: float = Field(ge=0.0, le=1.0)
    goal_progress: float = Field(ge=0.0, le=1.0)
    information_gain: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("outcome_id", "branch_id", "terminal_state_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "expected outcome text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "expected outcome ref")
        return value


class PlanRisk(CounterfactualPlanningFingerprintedModel):
    """Risk classification for one branch."""

    risk_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    severity: RiskSeverity
    policy_violation_count: int = Field(ge=0)
    safety_violation_count: int = Field(ge=0)
    irreversible_unsafe_plan_selection_count: int = Field(ge=0)
    rationale: str = Field(min_length=1)
    hard_policy_override_applied: bool = False
    hard_safety_override_applied: bool = False
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("risk_id", "branch_id", "rationale")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "plan risk text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "plan risk ref")
        return value

    @model_validator(mode="after")
    def overrides_must_reflect_violations(self) -> Self:
        if self.policy_violation_count and not self.hard_policy_override_applied:
            raise ValueError("policy violations require a hard policy override")
        if (
            self.safety_violation_count or self.irreversible_unsafe_plan_selection_count
        ) and not self.hard_safety_override_applied:
            raise ValueError("safety violations require a hard safety override")
        if self.severity in {"low", "medium"} and (
            self.policy_violation_count
            or self.safety_violation_count
            or self.irreversible_unsafe_plan_selection_count
        ):
            raise ValueError("violating branches must be high or critical risk")
        return self


class PlanResourceEstimate(CounterfactualPlanningFingerprintedModel):
    """Resource budget proof for one branch."""

    estimate_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    estimated_steps: int = Field(ge=0)
    time_horizon: int = Field(ge=1)
    resource_cost: float = Field(ge=0.0, le=1.0)
    budget_overrun_count: int = Field(default=0, ge=0)
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    source_rewrite_operations: int = Field(default=0, ge=0)
    action_execution: int = Field(default=0, ge=0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("estimate_id", "branch_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "resource estimate text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "resource estimate ref")
        return value

    @model_validator(mode="after")
    def external_resource_counters_must_be_zero(self) -> Self:
        for key in (
            "budget_overrun_count",
            "network_calls",
            "connector_calls",
            "model_provider_calls",
            "git_operations",
            "source_rewrite_operations",
            "action_execution",
        ):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class PlanReversibility(CounterfactualPlanningFingerprintedModel):
    """Reversibility proof for one branch."""

    reversibility_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    reversible_action_count: int = Field(ge=0)
    irreversible_action_count: int = Field(ge=0)
    irreversible_unsafe: bool = False
    selected_safe: bool = True
    rationale: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("reversibility_id", "branch_id", "rationale")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "plan reversibility text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "plan reversibility ref")
        return value

    @model_validator(mode="after")
    def unsafe_irreversible_branches_are_not_safe(self) -> Self:
        if self.irreversible_unsafe and self.selected_safe:
            raise ValueError("irreversible unsafe branches cannot be selected safe")
        if self.irreversible_unsafe and self.irreversible_action_count == 0:
            raise ValueError("irreversible unsafe branches require irreversible actions")
        return self


class CounterfactualBranch(CounterfactualPlanningFingerprintedModel):
    """One scored strategy branch backed by a world-model rollout."""

    branch_id: str = Field(min_length=1)
    strategy: StrategyOption
    action_proposals: tuple[ActionProposal, ...]
    rollout: CounterfactualRollout
    expected_outcomes: tuple[ExpectedOutcome, ...]
    risk: PlanRisk
    resource_estimate: PlanResourceEstimate
    reversibility: PlanReversibility
    score_vector: dict[str, float]
    total_score: float
    selected: bool = False
    blocked: bool = False
    policy_eligible: bool = True
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("branch_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "branch id")
        return value.strip()

    @field_validator("score_vector", mode="after")
    @classmethod
    def score_vector_must_be_safe(cls, value: dict[str, float]) -> FrozenDict:
        reject_secret_like_payload(value)
        missing = set(SCORE_DIMENSIONS).difference(value)
        if missing:
            raise ValueError(f"missing score dimensions: {sorted(missing)}")
        extra = set(value).difference(SCORE_DIMENSIONS)
        if extra:
            raise ValueError(f"unknown score dimensions: {sorted(extra)}")
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "score dimension")
            if not 0.0 <= nested <= 1.0:
                raise ValueError("score dimensions must be between 0.0 and 1.0")
        return cast(FrozenDict, freeze_payload(value))

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "branch evidence ref")
        return value

    @model_validator(mode="after")
    def branch_consistency_must_hold(self) -> Self:
        if not self.action_proposals:
            raise ValueError("branches require action proposals")
        if not self.expected_outcomes:
            raise ValueError("branches require expected outcomes")
        if set(self.score_vector) != set(SCORE_DIMENSIONS):
            raise ValueError("score vector must match score dimensions")
        has_policy_or_safety_failure = (
            self.risk.policy_violation_count > 0
            or self.risk.safety_violation_count > 0
            or self.risk.irreversible_unsafe_plan_selection_count > 0
            or self.reversibility.irreversible_unsafe
            or self.resource_estimate.budget_overrun_count > 0
        )
        if has_policy_or_safety_failure and self.selected:
            raise ValueError("unsafe or policy-violating branches cannot be selected")
        if has_policy_or_safety_failure and not self.blocked:
            raise ValueError("unsafe or policy-violating branches must be blocked")
        if not self.policy_eligible and not self.blocked:
            raise ValueError("policy-ineligible branches must be blocked")
        if self.rollout.forbidden_side_effects != 0:
            raise ValueError("branch rollouts must not create side effects")
        return self


class PlanEvidence(CounterfactualPlanningFingerprintedModel):
    """Benchmark evidence for an offline hierarchical plan."""

    evidence_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    authorization_id: str = AUTHORIZATION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    score_dimensions: tuple[str, ...] = SCORE_DIMENSIONS
    synthetic_goal_completion_plan_success_rate: float = Field(ge=0.0, le=1.0)
    policy_violation_count: int = Field(default=0, ge=0)
    budget_overrun_count: int = Field(default=0, ge=0)
    irreversible_unsafe_plan_selection_count: int = Field(default=0, ge=0)
    deterministic_plan_replay_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    deterministic_plan_replay_hash: str = Field(min_length=64, max_length=64)
    forbidden_side_effects: int = Field(default=0, ge=0)
    runtime_boundary: PlanningRuntimeBoundary
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("evidence_id", "plan_id", "authorization_id", "implementation_task")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "plan evidence text")
        return value.strip()

    @field_validator("score_dimensions")
    @classmethod
    def score_dimensions_must_match(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(value) != SCORE_DIMENSIONS:
            raise ValueError("score_dimensions must match AION-192 score dimensions")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "plan evidence ref")
        return value

    @model_validator(mode="after")
    def hard_pass_metrics_must_hold(self) -> Self:
        if self.authorization_id != AUTHORIZATION_ID:
            raise ValueError(f"authorization_id must be {AUTHORIZATION_ID}")
        if self.implementation_task != IMPLEMENTATION_TASK:
            raise ValueError(f"implementation_task must be {IMPLEMENTATION_TASK}")
        if self.synthetic_goal_completion_plan_success_rate < 0.8:
            raise ValueError("synthetic goal completion must meet 0.8 threshold")
        if self.policy_violation_count != 0:
            raise ValueError("policy_violation_count must be zero")
        if self.budget_overrun_count != 0:
            raise ValueError("budget_overrun_count must be zero")
        if self.irreversible_unsafe_plan_selection_count != 0:
            raise ValueError("irreversible unsafe selections must be zero")
        if self.deterministic_plan_replay_rate != 1.0:
            raise ValueError("deterministic replay rate must be 1.0")
        if self.forbidden_side_effects != 0:
            raise ValueError("forbidden_side_effects must be zero")
        return self


class HierarchicalPlan(CounterfactualPlanningFingerprintedModel):
    """A goal, strategy, milestone, task, and action-proposal hierarchy."""

    plan_id: str = Field(min_length=1)
    goal: StrategicGoal
    strategies: tuple[StrategyOption, ...]
    milestones: tuple[MilestonePlan, ...]
    tasks: tuple[TaskPlan, ...]
    branches: tuple[CounterfactualBranch, ...]
    selected_branch_id: str = Field(min_length=1)
    evidence: PlanEvidence
    action_execution_performed: bool = False
    source_rewrite_performed: bool = False
    hidden_mutation_performed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("plan_id", "selected_branch_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "hierarchical plan text")
        return value.strip()

    @model_validator(mode="after")
    def selected_branch_must_be_safe(self) -> Self:
        if self.evidence.plan_id != self.plan_id:
            raise ValueError("plan evidence must refer to this plan")
        if not self.strategies:
            raise ValueError("hierarchical plans require strategies")
        if not self.milestones:
            raise ValueError("hierarchical plans require milestones")
        if not self.tasks:
            raise ValueError("hierarchical plans require tasks")
        matches = [
            branch
            for branch in self.branches
            if branch.branch_id == self.selected_branch_id
        ]
        if len(matches) != 1:
            raise ValueError("selected_branch_id must identify exactly one branch")
        selected = matches[0]
        if not selected.selected:
            raise ValueError("selected branch must be marked selected")
        if selected.blocked:
            raise ValueError("selected branch must not be blocked")
        if not selected.policy_eligible:
            raise ValueError("selected branch must be policy eligible")
        if selected.risk.policy_violation_count:
            raise ValueError("selected branch must have no policy violations")
        if selected.risk.safety_violation_count:
            raise ValueError("selected branch must have no safety violations")
        if selected.resource_estimate.budget_overrun_count:
            raise ValueError("selected branch must not exceed budget")
        if selected.reversibility.irreversible_unsafe:
            raise ValueError("selected branch must not be irreversible unsafe")
        for key in (
            "action_execution_performed",
            "source_rewrite_performed",
            "hidden_mutation_performed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        return self


class ReplanningDecision(CounterfactualPlanningFingerprintedModel):
    """Decision on whether a plan should be retained or replanned."""

    decision_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    status: ReplanningStatus
    reason: str = Field(min_length=1)
    blocked_branch_ids: tuple[str, ...] = Field(default_factory=tuple)
    selected_branch_id: str | None = None
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("decision_id", "plan_id", "reason", "selected_branch_id")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "replanning decision text")
        return value.strip() if value is not None else None

    @field_validator("blocked_branch_ids", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "replanning decision ref")
        return value

    @model_validator(mode="after")
    def decision_must_match_status(self) -> Self:
        if self.status == "keep_plan" and self.blocked_branch_ids:
            raise ValueError("keep_plan decisions must not include blocked branches")
        if self.status != "keep_plan" and not self.blocked_branch_ids:
            raise ValueError("replan or blocked decisions require blocked branches")
        return self


def planning_replay_hash(payload: object) -> str:
    """Return a deterministic planning replay hash for immutable evidence."""

    return fingerprint_payload(payload)


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "SCHEMA_VERSION",
    "SCORE_DIMENSIONS",
    "ActionProposal",
    "CounterfactualBranch",
    "CounterfactualPlanningFingerprintedModel",
    "CounterfactualPlanningModel",
    "ExpectedOutcome",
    "HierarchicalPlan",
    "MilestonePlan",
    "PlanEvidence",
    "PlanGraph",
    "PlanResourceEstimate",
    "PlanReversibility",
    "PlanRisk",
    "PlanStep",
    "PlanningRuntimeBoundary",
    "ReplanningDecision",
    "StrategicGoal",
    "StrategyOption",
    "TaskPlan",
    "planning_replay_hash",
]
