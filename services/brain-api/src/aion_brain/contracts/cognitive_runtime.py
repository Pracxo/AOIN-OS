"""Integrated cognitive shadow-runtime contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.cognitive_state import (
    CognitiveStateSnapshot,
    FrozenDict,
    ObservedActionEffect,
    fingerprint_model,
    fingerprint_payload,
    freeze_payload,
)
from aion_brain.contracts.continual_learning import (
    LearningCandidate,
    LearningEpisode,
    LearningEvaluation,
    LearningRollbackPlan,
    PromotionRequest,
)
from aion_brain.contracts.information_acquisition import (
    InformationAcquisitionPlan,
    InformationNeed,
)
from aion_brain.contracts.memory_consolidation import (
    ConsolidationOutcome,
    EpisodicMemoryReference,
)
from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.planning import HierarchicalPlan, StrategicGoal, StrategyOption
from aion_brain.contracts.workspace import CognitiveCycleState, WorkspaceSnapshot
from aion_brain.contracts.world_model import (
    TransitionEvidence,
    TransitionPrediction,
    WorldActionReference,
    WorldState,
)

SCHEMA_VERSION = "cognitive-runtime/v1"
CANONICALIZATION_VERSION = "cognitive-runtime-canonical-json/v1"
AUTHORIZATION_ID = "AION-198-CA-0008"
IMPLEMENTATION_TASK = "AION-199"
CANDIDATE_ID = "integrated-cognitive-shadow-runtime"
SCOPE = "operator-invoked-local-offline-integrated-cognitive-shadow-runtime"

REQUIRED_CYCLE_STEPS = (
    "validate_manifest_and_authorization",
    "load_approved_persistent_state",
    "accept_one_approved_observation",
    "update_belief_and_uncertainty",
    "retrieve_approved_memory_references",
    "generate_world_model_predictions",
    "run_workspace_arbitration",
    "generate_hierarchical_plan_proposals",
    "generate_information_acquisition_requests",
    "record_simulated_outcomes",
    "create_consolidation_candidates",
    "create_learning_candidates",
    "return_operator_review_evidence",
    "persist_approved_local_cognitive_state",
    "perform_no_consequential_external_action",
)

SessionInputKind = Literal["synthetic", "redacted"]
RuntimeStatus = Literal["ready", "operator_review_required", "blocked", "killed"]
IncidentSeverity = Literal["low", "medium", "high", "critical"]
PermissionMap = dict[str, bool]
ApprovedRefs = dict[str, tuple[str, ...]]


class CognitiveRuntimeModel(BaseModel):
    """Base model for immutable cognitive-runtime contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class CognitiveRuntimeFingerprintedModel(CognitiveRuntimeModel):
    """Immutable model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical runtime payload")
        return self


class CognitiveRuntimeBudget(CognitiveRuntimeFingerprintedModel):
    """Bounded local resource budget for one operator invocation."""

    budget_id: str = Field(default="aion-199-runtime-budget", min_length=1)
    max_cycles_per_invocation: int = Field(default=100, ge=1, le=100)
    max_wall_clock_seconds: int = Field(default=1800, ge=1, le=1800)
    max_workspace_items: int = Field(default=5, ge=1, le=16)
    max_memory_refs: int = Field(default=8, ge=1, le=64)
    max_learning_episodes: int = Field(default=8, ge=1, le=64)
    concurrency_maximum: int = Field(default=1, ge=1, le=1)
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    approval_creation: int = Field(default=0, ge=0)
    merge_operations: int = Field(default=0, ge=0)
    deployment_operations: int = Field(default=0, ge=0)
    source_rewrite_operations: int = Field(default=0, ge=0)
    model_weight_training: int = Field(default=0, ge=0)
    consequential_action_execution: int = Field(default=0, ge=0)

    @field_validator("budget_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "runtime budget id")
        return value.strip()

    @model_validator(mode="after")
    def external_resource_counters_must_be_zero(self) -> Self:
        for key in (
            "network_calls",
            "connector_calls",
            "model_provider_calls",
            "git_operations",
            "approval_creation",
            "merge_operations",
            "deployment_operations",
            "source_rewrite_operations",
            "model_weight_training",
            "consequential_action_execution",
        ):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class CognitiveRuntimeDiagnostics(CognitiveRuntimeFingerprintedModel):
    """Sanitized diagnostics for one local shadow-runtime cycle."""

    diagnostics_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    status: RuntimeStatus
    cycle_steps_completed: tuple[str, ...] = Field(default_factory=tuple)
    cycle_count: int = Field(ge=0)
    budget_exceeded: bool = False
    kill_switch_engaged: bool = False
    operator_review_required: bool = True
    production_input: bool = False
    user_traffic: bool = False
    runtime_effect: bool = False
    api_route_added: bool = False
    kernel_registration_added: bool = False
    startup_registration: bool = False
    scheduler_started: bool = False
    background_loop_added: bool = False
    cli_installation: bool = False
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    approval_creation: int = Field(default=0, ge=0)
    merge_operations: int = Field(default=0, ge=0)
    deployment_operations: int = Field(default=0, ge=0)
    source_rewrite_operations: int = Field(default=0, ge=0)
    model_weight_training: int = Field(default=0, ge=0)
    consequential_action_execution: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("diagnostics_id", "session_id", "cycle_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "runtime diagnostics text")
        return value.strip()

    @field_validator("cycle_steps_completed")
    @classmethod
    def steps_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "runtime cycle step")
        return value

    @model_validator(mode="after")
    def runtime_boundaries_must_remain_disabled(self) -> Self:
        for key in (
            "production_input",
            "user_traffic",
            "runtime_effect",
            "api_route_added",
            "kernel_registration_added",
            "startup_registration",
            "scheduler_started",
            "background_loop_added",
            "cli_installation",
            "budget_exceeded",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        for key in (
            "network_calls",
            "connector_calls",
            "model_provider_calls",
            "git_operations",
            "approval_creation",
            "merge_operations",
            "deployment_operations",
            "source_rewrite_operations",
            "model_weight_training",
            "consequential_action_execution",
        ):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        if self.status == "operator_review_required":
            if tuple(self.cycle_steps_completed) != REQUIRED_CYCLE_STEPS:
                raise ValueError("completed runtime cycles must record the required step list")
            if not self.operator_review_required:
                raise ValueError("completed runtime cycles require operator review")
        return self


class CognitiveRuntimeIncident(CognitiveRuntimeFingerprintedModel):
    """Fail-closed incident record for rejected runtime invocation attempts."""

    incident_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    cycle_id: str | None = None
    severity: IncidentSeverity
    reason_code: str = Field(min_length=1)
    blocked: bool = True
    operator_review_required: bool = True
    external_effect_performed: bool = False
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("incident_id", "session_id", "cycle_id", "reason_code")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "runtime incident text")
            return value.strip()
        return value

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "runtime incident ref")
        return value

    @model_validator(mode="after")
    def incident_must_fail_closed(self) -> Self:
        if not self.blocked:
            raise ValueError("runtime incidents must be blocked")
        if not self.operator_review_required:
            raise ValueError("runtime incidents require operator review")
        if self.external_effect_performed:
            raise ValueError("runtime incidents must not perform external effects")
        return self


class ApprovedCognitiveObservation(CognitiveRuntimeFingerprintedModel):
    """Exactly one synthetic or redacted observation accepted into a cycle."""

    observation_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    belief_statement: str = Field(min_length=1)
    belief_confidence: float = Field(ge=0.0, le=1.0)
    uncertainty_subject: str = Field(min_length=1)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    world_state: WorldState
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    operator_approved: bool = True
    synthetic_or_redacted: bool = True
    production_input: bool = False
    user_traffic: bool = False
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("observation_id", "summary", "belief_statement", "uncertainty_subject")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "runtime observation text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "runtime observation ref")
        return value

    @model_validator(mode="after")
    def observation_must_be_approved_and_non_production(self) -> Self:
        if not self.operator_approved:
            raise ValueError("runtime observations require operator approval")
        if not self.synthetic_or_redacted:
            raise ValueError("runtime observations must be synthetic or redacted")
        if self.production_input:
            raise ValueError("production input is prohibited")
        if self.user_traffic:
            raise ValueError("user traffic is prohibited")
        return self


class CognitiveSessionManifest(CognitiveRuntimeFingerprintedModel):
    """Operator-supplied manifest for one local offline runtime invocation."""

    session_id: str = Field(min_length=1)
    operator_id: str = Field(min_length=1)
    authorization_id: str = AUTHORIZATION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    candidate_id: str = CANDIDATE_ID
    scope: str = SCOPE
    input_kind: SessionInputKind
    state_repository_ref: str = Field(min_length=1)
    approved_specialist_ids: tuple[str, ...] = Field(default=("shadow-runtime",))
    budget: CognitiveRuntimeBudget = Field(default_factory=CognitiveRuntimeBudget)
    required_cycle_steps: tuple[str, ...] = REQUIRED_CYCLE_STEPS
    operator_invoked: bool = True
    local_offline: bool = True
    production_runtime_enabled: bool = False
    network_access: bool = False
    connector_access: bool = False
    provider_access: bool = False
    api_route_added: bool = False
    kernel_registration_added: bool = False
    startup_registration: bool = False
    scheduler_started: bool = False
    background_loop_added: bool = False
    cli_installation: bool = False
    consequential_action_execution: bool = False
    kill_switch_engaged: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("session_id", "operator_id", "state_repository_ref")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "runtime manifest text")
        return value.strip()

    @field_validator("approved_specialist_ids", "required_cycle_steps")
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "runtime manifest tuple")
        return value

    @model_validator(mode="after")
    def manifest_must_match_authorization(self) -> Self:
        if self.authorization_id != AUTHORIZATION_ID:
            raise ValueError(f"authorization_id must be {AUTHORIZATION_ID}")
        if self.implementation_task != IMPLEMENTATION_TASK:
            raise ValueError(f"implementation_task must be {IMPLEMENTATION_TASK}")
        if self.candidate_id != CANDIDATE_ID:
            raise ValueError(f"candidate_id must be {CANDIDATE_ID}")
        if self.scope != SCOPE:
            raise ValueError(f"scope must be {SCOPE}")
        if tuple(self.required_cycle_steps) != REQUIRED_CYCLE_STEPS:
            raise ValueError("required cycle steps must match AION-198 authorization")
        if not self.operator_invoked:
            raise ValueError("runtime must be explicitly operator-invoked")
        if not self.local_offline:
            raise ValueError("runtime must remain local offline")
        for key in (
            "production_runtime_enabled",
            "network_access",
            "connector_access",
            "provider_access",
            "api_route_added",
            "kernel_registration_added",
            "startup_registration",
            "scheduler_started",
            "background_loop_added",
            "cli_installation",
            "consequential_action_execution",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        return self


class CognitiveSessionState(CognitiveRuntimeFingerprintedModel):
    """Current local session state loaded from the approved repository."""

    session_id: str = Field(min_length=1)
    manifest: CognitiveSessionManifest
    snapshot: CognitiveStateSnapshot
    state_snapshot_hash: str = Field(min_length=64, max_length=64)
    status: RuntimeStatus = "ready"
    cycle_count: int = Field(default=0, ge=0)
    last_cycle_id: str | None = None
    approved_state_loaded: bool = True
    persisted_approved_local_state: bool = True
    operator_review_required: bool = True
    kill_switch_engaged: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("session_id", "last_cycle_id", "state_snapshot_hash")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "runtime session state text")
            return value.strip()
        return value

    @model_validator(mode="after")
    def state_must_match_manifest_and_snapshot(self) -> Self:
        if self.session_id != self.manifest.session_id:
            raise ValueError("session state must match manifest session_id")
        if self.state_snapshot_hash != self.snapshot.content_hash:
            raise ValueError("state_snapshot_hash must match snapshot content hash")
        if self.cycle_count > self.manifest.budget.max_cycles_per_invocation:
            raise ValueError("cycle count exceeds manifest budget")
        if not self.approved_state_loaded:
            raise ValueError("runtime state must load approved local state")
        if not self.persisted_approved_local_state:
            raise ValueError("runtime state must persist approved local state")
        return self


class CognitiveCycleInput(CognitiveRuntimeFingerprintedModel):
    """One bounded local cycle request with exactly one approved observation."""

    cycle_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    observation: ApprovedCognitiveObservation
    candidate_actions: tuple[WorldActionReference, ...]
    transition_evidence: tuple[TransitionEvidence, ...] = Field(default_factory=tuple)
    goal: StrategicGoal
    strategies: tuple[StrategyOption, ...]
    information_need: InformationNeed
    approved_memory_refs: tuple[EpisodicMemoryReference, ...]
    learning_episodes: tuple[LearningEpisode, ...]
    permissions: PermissionMap = Field(default_factory=dict)
    approved_information_refs: ApprovedRefs = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1)
    operator_approved: bool = True
    external_action_requested: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("cycle_id", "idempotency_key")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "runtime cycle input text")
        return value.strip()

    @field_validator("permissions", mode="after")
    @classmethod
    def permissions_must_be_safe(cls, value: PermissionMap) -> FrozenDict:
        reject_secret_like_payload(dict(value))
        return cast(FrozenDict, freeze_payload(dict(value)))

    @field_validator("approved_information_refs", mode="after")
    @classmethod
    def approved_refs_must_be_safe(cls, value: ApprovedRefs) -> FrozenDict:
        payload = {key: tuple(values) for key, values in dict(value).items()}
        reject_secret_like_payload(payload)
        for key, values in payload.items():
            reject_hidden_or_secret_text(key, "runtime approved ref key")
            for item in values:
                reject_hidden_or_secret_text(item, "runtime approved ref")
        return cast(FrozenDict, freeze_payload(payload))

    @model_validator(mode="after")
    def cycle_input_must_be_bounded(self) -> Self:
        if not self.operator_approved:
            raise ValueError("cycle input requires operator approval")
        if self.external_action_requested:
            raise ValueError("external action execution is prohibited")
        if not self.candidate_actions:
            raise ValueError("cycle input requires at least one candidate action")
        if not self.strategies:
            raise ValueError("cycle input requires at least one strategy")
        if not self.approved_memory_refs:
            raise ValueError("cycle input requires approved memory references")
        if not self.learning_episodes:
            raise ValueError("cycle input requires approved learning episodes")
        return self


class CognitiveRuntimeEvidence(CognitiveRuntimeFingerprintedModel):
    """Operator-review evidence returned by one completed shadow cycle."""

    evidence_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    authorization_id: str = AUTHORIZATION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    cycle_steps_completed: tuple[str, ...] = REQUIRED_CYCLE_STEPS
    state_before_hash: str = Field(min_length=64, max_length=64)
    state_after_hash: str = Field(min_length=64, max_length=64)
    workspace_snapshot_hash: str = Field(min_length=64, max_length=64)
    plan_fingerprint: str = Field(min_length=64, max_length=64)
    information_plan_fingerprint: str = Field(min_length=64, max_length=64)
    consolidation_checkpoint_fingerprint: str = Field(min_length=64, max_length=64)
    learning_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    simulated_outcome_ids: tuple[str, ...] = Field(default_factory=tuple)
    operator_review_required: bool = True
    deterministic_replay_hash: str | None = None
    forbidden_side_effects: int = Field(default=0, ge=0)
    policy_violations: int = Field(default=0, ge=0)
    unauthorized_promotions: int = Field(default=0, ge=0)
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    approval_creation: int = Field(default=0, ge=0)
    merge_operations: int = Field(default=0, ge=0)
    deployment_operations: int = Field(default=0, ge=0)
    source_rewrite_operations: int = Field(default=0, ge=0)
    model_weight_training: int = Field(default=0, ge=0)
    consequential_action_execution: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("evidence_id", "session_id", "cycle_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "runtime evidence text")
        return value.strip()

    @field_validator("learning_candidate_ids", "simulated_outcome_ids", "cycle_steps_completed")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "runtime evidence ref")
        return value

    @model_validator(mode="after")
    def evidence_must_match_authorization_and_hash(self) -> Self:
        if self.authorization_id != AUTHORIZATION_ID:
            raise ValueError(f"authorization_id must be {AUTHORIZATION_ID}")
        if self.implementation_task != IMPLEMENTATION_TASK:
            raise ValueError(f"implementation_task must be {IMPLEMENTATION_TASK}")
        if tuple(self.cycle_steps_completed) != REQUIRED_CYCLE_STEPS:
            raise ValueError("runtime evidence must include the required cycle steps")
        if not self.operator_review_required:
            raise ValueError("runtime evidence requires operator review")
        for key in (
            "forbidden_side_effects",
            "policy_violations",
            "unauthorized_promotions",
            "network_calls",
            "connector_calls",
            "model_provider_calls",
            "git_operations",
            "approval_creation",
            "merge_operations",
            "deployment_operations",
            "source_rewrite_operations",
            "model_weight_training",
            "consequential_action_execution",
        ):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        expected = fingerprint_payload(
            {
                "authorization_id": self.authorization_id,
                "implementation_task": self.implementation_task,
                "session_id": self.session_id,
                "cycle_id": self.cycle_id,
                "cycle_steps_completed": self.cycle_steps_completed,
                "state_before_hash": self.state_before_hash,
                "state_after_hash": self.state_after_hash,
                "workspace_snapshot_hash": self.workspace_snapshot_hash,
                "plan_fingerprint": self.plan_fingerprint,
                "information_plan_fingerprint": self.information_plan_fingerprint,
                "consolidation_checkpoint_fingerprint": (
                    self.consolidation_checkpoint_fingerprint
                ),
                "learning_candidate_ids": self.learning_candidate_ids,
                "simulated_outcome_ids": self.simulated_outcome_ids,
            }
        )
        if self.deterministic_replay_hash is None:
            object.__setattr__(self, "deterministic_replay_hash", expected)
        elif self.deterministic_replay_hash != expected:
            raise ValueError("deterministic_replay_hash must match runtime evidence")
        object.__setattr__(self, "fingerprint", fingerprint_model(self, exclude={"fingerprint"}))
        return self


class CognitiveCycleOutput(CognitiveRuntimeFingerprintedModel):
    """Complete operator-review output from one local shadow cycle."""

    session_state: CognitiveSessionState
    cycle_input: CognitiveCycleInput
    state_before: CognitiveStateSnapshot
    state_after: CognitiveStateSnapshot
    world_predictions: tuple[TransitionPrediction, ...]
    workspace_snapshot: WorkspaceSnapshot
    workspace_cycle: CognitiveCycleState
    plan: HierarchicalPlan
    information_plan: InformationAcquisitionPlan
    simulated_outcomes: tuple[ObservedActionEffect, ...]
    consolidation_outcome: ConsolidationOutcome
    learning_candidates: tuple[LearningCandidate, ...]
    learning_evaluations: tuple[LearningEvaluation, ...]
    promotion_requests: tuple[PromotionRequest, ...]
    rollback_plans: tuple[LearningRollbackPlan, ...]
    evidence: CognitiveRuntimeEvidence
    diagnostics: CognitiveRuntimeDiagnostics
    incidents: tuple[CognitiveRuntimeIncident, ...] = Field(default_factory=tuple)
    status: RuntimeStatus = "operator_review_required"
    action_execution_performed: bool = False
    external_effect_performed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def output_must_remain_review_only(self) -> Self:
        if self.status != "operator_review_required":
            raise ValueError("completed runtime output must require operator review")
        if self.action_execution_performed:
            raise ValueError("runtime output must not execute actions")
        if self.external_effect_performed:
            raise ValueError("runtime output must not perform external effects")
        if self.evidence.session_id != self.session_state.session_id:
            raise ValueError("evidence must match session")
        if self.evidence.cycle_id != self.cycle_input.cycle_id:
            raise ValueError("evidence must match cycle input")
        if self.state_after.content_hash != self.session_state.state_snapshot_hash:
            raise ValueError("session state must point at the persisted after snapshot")
        if self.diagnostics.status != "operator_review_required":
            raise ValueError("completed diagnostics must require operator review")
        return self


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "CANDIDATE_ID",
    "IMPLEMENTATION_TASK",
    "REQUIRED_CYCLE_STEPS",
    "SCHEMA_VERSION",
    "SCOPE",
    "ApprovedCognitiveObservation",
    "CognitiveCycleInput",
    "CognitiveCycleOutput",
    "CognitiveRuntimeBudget",
    "CognitiveRuntimeDiagnostics",
    "CognitiveRuntimeEvidence",
    "CognitiveRuntimeIncident",
    "CognitiveRuntimeModel",
    "CognitiveSessionManifest",
    "CognitiveSessionState",
]
