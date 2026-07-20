"""Contracts for disabled controlled shadow activation evaluation."""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.self_improvement_shadow import (
    SHADOW_REFERENCE_KINDS,
    canonical_shadow_fingerprint,
    fingerprint_model,
    require_fingerprint,
    require_safe_identifier,
    require_utc_datetime,
    validate_shadow_text,
)

SHADOW_ACTIVATION_CONTRACT_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation/v1"
] = "self-improvement-shadow-activation/v1"
SHADOW_ACTIVATION_CANDIDATE_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-candidate/v1"
] = "self-improvement-shadow-activation-candidate/v1"
SHADOW_ACTIVATION_REQUEST_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-request/v1"
] = "self-improvement-shadow-activation-request/v1"
SHADOW_ACTIVATION_APPROVAL_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-approval/v1"
] = "self-improvement-shadow-activation-approval/v1"
SHADOW_ACTIVATION_STATE_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-state/v1"
] = "self-improvement-shadow-activation-state/v1"
SHADOW_ACTIVATION_BUDGET_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-budget/v1"
] = "self-improvement-shadow-activation-budget/v1"
SHADOW_ACTIVATION_MONITORING_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-monitoring/v1"
] = "self-improvement-shadow-activation-monitoring/v1"
SHADOW_ACTIVATION_DEACTIVATION_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-deactivation/v1"
] = "self-improvement-shadow-activation-deactivation/v1"
SHADOW_ACTIVATION_EVIDENCE_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-evidence/v1"
] = "self-improvement-shadow-activation-evidence/v1"
SHADOW_ACTIVATION_INCIDENT_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-incident/v1"
] = "self-improvement-shadow-activation-incident/v1"
SHADOW_ACTIVATION_SIMULATION_SCHEMA_VERSION: Literal[
    "self-improvement-shadow-activation-simulation/v1"
] = "self-improvement-shadow-activation-simulation/v1"
SHADOW_ACTIVATION_REASON_CODE_REGISTRY_VERSION = (
    "self-improvement-shadow-activation-reasons/v1"
)

PROGRAM_ID: Literal["AION-SELF-IMPROVEMENT-001"] = "AION-SELF-IMPROVEMENT-001"
ACTIVATION_PROGRAM_ID: Literal[
    "AION-SELF-IMPROVEMENT-CONTROLLED-SHADOW-ACTIVATION-001"
] = "AION-SELF-IMPROVEMENT-CONTROLLED-SHADOW-ACTIVATION-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-180-SI-0007"] = "AION-180-SI-0007"
APPROVAL_RECORD_ID: Literal["AION-180-SI-0007"] = "AION-180-SI-0007"
PARENT_EVALUATION_ID: Literal["AION-SOE-001"] = "AION-SOE-001"
PARENT_EVALUATION_DECISION: Literal[
    "SHADOW_MODE_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_ACTIVATION_AUTHORIZATION_REVIEW"
] = "SHADOW_MODE_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_ACTIVATION_AUTHORIZATION_REVIEW"
PARENT_CLOSEOUT_TASK: Literal["AION-179"] = "AION-179"
PARENT_MAIN_COMMIT: Literal["133040597ca8ed997bbc32b8bb8c980a123d2f9a"] = (
    "133040597ca8ed997bbc32b8bb8c980a123d2f9a"
)
PARENT_SHADOW_IMPLEMENTATION_COMMIT: Literal[
    "b05dd3cc49cff086997232bfc579a7ca891a184b"
] = "b05dd3cc49cff086997232bfc579a7ca891a184b"
PARENT_AUTHORIZATION_TRANSACTION_ID: Literal["AION-177-SI-0006"] = "AION-177-SI-0006"
CANDIDATE_ID: Literal["controlled-shadow-mode-activation-control-plane"] = (
    "controlled-shadow-mode-activation-control-plane"
)
WORKSTREAM: Literal["self-improvement-shadow-activation-governance"] = (
    "self-improvement-shadow-activation-governance"
)
IMPLEMENTATION_TASK: Literal["AION-181"] = "AION-181"
FORMAL_CLOSEOUT_TASK: Literal["AION-182"] = "AION-182"
AUTHORIZATION_SCOPE: Literal[
    "disabled-shadow-activation-request-approval-monitoring-deactivation-control-plane"
] = "disabled-shadow-activation-request-approval-monitoring-deactivation-control-plane"

MAXIMUM_ACTIVATION_WINDOW_SECONDS = 3600
MAXIMUM_RUNS_PER_ACTIVATION = 10
MAXIMUM_CONCURRENCY = 4
MAXIMUM_RETENTION_SECONDS = 604800
MAXIMUM_EVIDENCE_BUNDLE_BYTES = 10485760

STRICT_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

ShadowActivationState = Literal[
    "drafted",
    "evidence_ready",
    "approval_pending",
    "approved_disabled",
    "simulation_ready",
    "simulated",
    "review_pending",
    "rejected",
    "expired",
    "revoked",
    "archived",
]
ForbiddenShadowActivationState = Literal[
    "active",
    "running_in_production",
    "canary",
    "deployed",
    "promoted",
    "merged",
    "self_approved",
]
ShadowActivationDecisionOutcome = Literal[
    "candidate_valid",
    "candidate_invalid",
    "approval_required",
    "approval_invalid",
    "simulation_ready",
    "simulation_passed",
    "simulation_failed",
    "expired",
    "revoked",
    "archived",
    "runtime_disabled",
]
ShadowActivationEnvironment = Literal["local_offline_operator_evaluation"]
ShadowActivationDataClassification = Literal["synthetic", "redacted"]
ShadowActivationAdapterType = Literal[
    "in_memory_redacted_snapshot_adapter",
    "explicit_local_shadow_evidence_bundle_adapter",
]
ShadowActivationRiskLevel = Literal["high", "critical"]
ShadowActivationTransitionReason = Literal[
    "candidate_evidence_valid",
    "candidate_evidence_invalid",
    "approval_required",
    "approval_valid",
    "approval_invalid",
    "approval_expired",
    "approval_revoked",
    "simulation_ready",
    "simulation_passed",
    "simulation_failed",
    "operator_review_required",
    "archived",
    "runtime_disabled",
]
ShadowActivationMonitoringMetricName = Literal[
    "run_count",
    "reference_count",
    "evaluation_count",
    "pattern_count",
    "hypothesis_count",
    "regression_proposal_count",
    "shadow_proposal_count",
    "review_item_count",
    "budget_violation_count",
    "redaction_failure_count",
    "reference_failure_count",
    "fingerprint_mismatch_count",
    "output_boundary_failure_count",
    "wall_clock_seconds",
    "benchmark_cost_units",
    "output_bytes",
    "output_files",
    "network_call_count",
    "connector_call_count",
    "provider_call_count",
    "git_operation_count",
    "source_mutation_count",
    "real_pr_count",
    "approval_creation_count",
    "runtime_promotion_count",
    "runtime_influence_count",
]
ShadowActivationDeactivationTrigger = Literal[
    "network_call_detected",
    "connector_call_detected",
    "provider_call_detected",
    "git_operation_detected",
    "source_mutation_detected",
    "pull_request_creation_detected",
    "approval_creation_detected",
    "runtime_promotion_detected",
    "runtime_influence_detected",
    "output_boundary_escape_detected",
    "redaction_failure_detected",
    "holdout_disclosure_detected",
    "protected_material_exposure_detected",
    "fingerprint_mismatch_detected",
    "budget_violation_detected",
    "unknown_reference_type_detected",
    "stale_or_expired_approval_detected",
    "activation_window_expired",
    "run_count_exhausted",
    "operator_kill_switch_asserted",
]

SHADOW_ACTIVATION_STATES: tuple[ShadowActivationState, ...] = (
    "drafted",
    "evidence_ready",
    "approval_pending",
    "approved_disabled",
    "simulation_ready",
    "simulated",
    "review_pending",
    "rejected",
    "expired",
    "revoked",
    "archived",
)
FORBIDDEN_SHADOW_ACTIVATION_STATES: frozenset[str] = frozenset(
    {
        "active",
        "running_in_production",
        "canary",
        "deployed",
        "promoted",
        "merged",
        "self_approved",
    }
)
SHADOW_ACTIVATION_ALLOWED_TRANSITIONS: dict[ShadowActivationState, frozenset[str]] = {
    "drafted": frozenset({"evidence_ready", "rejected", "archived"}),
    "evidence_ready": frozenset({"approval_pending", "rejected", "archived"}),
    "approval_pending": frozenset({"approved_disabled", "rejected", "expired", "revoked"}),
    "approved_disabled": frozenset({"simulation_ready", "expired", "revoked", "archived"}),
    "simulation_ready": frozenset({"simulated", "rejected", "expired", "revoked"}),
    "simulated": frozenset({"review_pending", "rejected", "archived"}),
    "review_pending": frozenset({"archived", "revoked"}),
    "rejected": frozenset({"archived"}),
    "expired": frozenset({"archived"}),
    "revoked": frozenset({"archived"}),
    "archived": frozenset(),
}
SHADOW_ACTIVATION_DECISION_OUTCOMES: tuple[ShadowActivationDecisionOutcome, ...] = (
    "candidate_valid",
    "candidate_invalid",
    "approval_required",
    "approval_invalid",
    "simulation_ready",
    "simulation_passed",
    "simulation_failed",
    "expired",
    "revoked",
    "archived",
    "runtime_disabled",
)
DISALLOWED_SHADOW_ACTIVATION_ENVIRONMENTS = frozenset(
    {
        "production",
        "staging_connected",
        "network_connected",
        "provider_connected",
        "connector_connected",
        "user_traffic",
        "kernel_runtime",
    }
)
SHADOW_ACTIVATION_ADAPTER_TYPES: tuple[ShadowActivationAdapterType, ...] = (
    "in_memory_redacted_snapshot_adapter",
    "explicit_local_shadow_evidence_bundle_adapter",
)
SHADOW_ACTIVATION_MONITORING_METRICS: tuple[ShadowActivationMonitoringMetricName, ...] = (
    "run_count",
    "reference_count",
    "evaluation_count",
    "pattern_count",
    "hypothesis_count",
    "regression_proposal_count",
    "shadow_proposal_count",
    "review_item_count",
    "budget_violation_count",
    "redaction_failure_count",
    "reference_failure_count",
    "fingerprint_mismatch_count",
    "output_boundary_failure_count",
    "wall_clock_seconds",
    "benchmark_cost_units",
    "output_bytes",
    "output_files",
    "network_call_count",
    "connector_call_count",
    "provider_call_count",
    "git_operation_count",
    "source_mutation_count",
    "real_pr_count",
    "approval_creation_count",
    "runtime_promotion_count",
    "runtime_influence_count",
)
FORBIDDEN_COUNTER_METRICS: frozenset[ShadowActivationMonitoringMetricName] = frozenset(
    {
        "network_call_count",
        "connector_call_count",
        "provider_call_count",
        "git_operation_count",
        "source_mutation_count",
        "real_pr_count",
        "approval_creation_count",
        "runtime_promotion_count",
        "runtime_influence_count",
    }
)
SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS: tuple[ShadowActivationDeactivationTrigger, ...] = (
    "network_call_detected",
    "connector_call_detected",
    "provider_call_detected",
    "git_operation_detected",
    "source_mutation_detected",
    "pull_request_creation_detected",
    "approval_creation_detected",
    "runtime_promotion_detected",
    "runtime_influence_detected",
    "output_boundary_escape_detected",
    "redaction_failure_detected",
    "holdout_disclosure_detected",
    "protected_material_exposure_detected",
    "fingerprint_mismatch_detected",
    "budget_violation_detected",
    "unknown_reference_type_detected",
    "stale_or_expired_approval_detected",
    "activation_window_expired",
    "run_count_exhausted",
    "operator_kill_switch_asserted",
)
FORBIDDEN_COUNTER_TRIGGER_BY_METRIC: dict[str, ShadowActivationDeactivationTrigger] = {
    "network_call_count": "network_call_detected",
    "connector_call_count": "connector_call_detected",
    "provider_call_count": "provider_call_detected",
    "git_operation_count": "git_operation_detected",
    "source_mutation_count": "source_mutation_detected",
    "real_pr_count": "pull_request_creation_detected",
    "approval_creation_count": "approval_creation_detected",
    "runtime_promotion_count": "runtime_promotion_detected",
    "runtime_influence_count": "runtime_influence_detected",
}
FAILURE_TRIGGER_BY_METRIC: dict[str, ShadowActivationDeactivationTrigger] = {
    "budget_violation_count": "budget_violation_detected",
    "redaction_failure_count": "redaction_failure_detected",
    "fingerprint_mismatch_count": "fingerprint_mismatch_detected",
    "output_boundary_failure_count": "output_boundary_escape_detected",
}
SHADOW_ACTIVATION_REASON_CODES: tuple[str, ...] = (
    "activation_candidate_valid",
    "activation_candidate_invalid",
    "activation_candidate_expired",
    "activation_request_valid",
    "activation_request_invalid",
    "activation_environment_allowed",
    "activation_environment_blocked",
    "activation_data_classification_allowed",
    "activation_data_classification_blocked",
    "activation_adapter_allowed",
    "activation_adapter_blocked",
    "activation_reference_set_bound",
    "activation_reference_set_mismatch",
    "activation_output_boundary_valid",
    "activation_output_boundary_invalid",
    "activation_budget_satisfied",
    "activation_budget_exceeded",
    "activation_monitoring_plan_valid",
    "activation_monitoring_plan_invalid",
    "activation_deactivation_plan_valid",
    "activation_deactivation_plan_invalid",
    "activation_approval_required",
    "activation_approval_valid",
    "activation_approval_invalid",
    "activation_approval_expired",
    "activation_approval_consumed",
    "activation_approval_reuse_blocked",
    "activation_self_approval_blocked",
    "activation_separation_of_duties_satisfied",
    "activation_separation_of_duties_failed",
    "activation_security_review_satisfied",
    "activation_security_review_failed",
    "activation_binding_mismatch",
    "activation_transition_allowed",
    "activation_transition_blocked",
    "activation_forbidden_state_blocked",
    "activation_simulation_ready",
    "activation_simulation_passed",
    "activation_simulation_failed",
    "activation_monitoring_passed",
    "activation_monitoring_breached",
    "activation_deactivation_required",
    "activation_deactivation_not_required",
    "activation_kill_switch_asserted",
    "activation_window_expired",
    "activation_run_count_exhausted",
    "activation_network_access_blocked",
    "activation_connector_access_blocked",
    "activation_provider_access_blocked",
    "activation_source_mutation_blocked",
    "activation_git_mutation_blocked",
    "activation_pr_creation_blocked",
    "activation_approval_creation_blocked",
    "activation_merge_blocked",
    "activation_promotion_blocked",
    "activation_production_exposure_blocked",
    "activation_runtime_disabled",
    "activation_actual_activation_unauthorized",
    "activation_scope_control_plane_only",
)
SHADOW_ACTIVATION_REASON_CODE_SET = frozenset(SHADOW_ACTIVATION_REASON_CODES)
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_ALL_ZERO_SHA1 = "0" * 40


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(UTC)


def require_activation_identifier(value: str, field_name: str = "identifier") -> str:
    """Require a bounded identifier suitable for activation evidence."""

    return require_safe_identifier(value, field_name)


def require_sha1(value: str, field_name: str = "sha") -> str:
    """Require a lowercase Git SHA-1-sized digest."""

    if not _SHA1_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase 40-character SHA")
    return value


def require_activation_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    """Require stable activation reason codes."""

    if len(value) != len(set(value)):
        raise ValueError("activation reason codes must be unique")
    for code in value:
        if code not in SHADOW_ACTIVATION_REASON_CODE_SET:
            raise ValueError("unknown activation reason code")
    return value


def require_metric_names(
    value: tuple[ShadowActivationMonitoringMetricName, ...],
) -> tuple[ShadowActivationMonitoringMetricName, ...]:
    """Require exact monitoring coverage in registry order."""

    if tuple(value) != SHADOW_ACTIVATION_MONITORING_METRICS:
        raise ValueError("activation monitoring metrics must match the registry")
    return value


def fingerprint_activation_model(model: BaseModel) -> str:
    """Return a deterministic fingerprint for an activation model."""

    return fingerprint_model(model)


def _safe_text(value: str, field_name: str = "text", max_length: int = 512) -> str:
    return validate_shadow_text(value, field_name=field_name, max_length=max_length)


def _safe_identifier_tuple(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    cleaned = tuple(require_activation_identifier(item, field_name) for item in value)
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{field_name} must be unique")
    return cleaned


def _fingerprint_tuple(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    cleaned = tuple(require_fingerprint(item, field_name) for item in value)
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{field_name} must be unique")
    return cleaned


def _finite_non_negative(value: int | float, field_name: str) -> int | float:
    if not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be finite")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _field_fingerprint(value: str, info: Any) -> str:
    return require_fingerprint(value, getattr(info, "field_name", "fingerprint"))


def _created_before_expiry(
    created_at: datetime,
    expires_at: datetime,
    maximum_seconds: int,
) -> None:
    if expires_at <= created_at:
        raise ValueError("activation expiry must be later than creation")
    if (expires_at - created_at).total_seconds() > maximum_seconds:
        raise ValueError("activation lifetime exceeds the authorized maximum")


class ShadowActivationCandidate(BaseModel):
    """Immutable candidate facts bound to the AION-180 authorization."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-candidate/v1"] = (
        SHADOW_ACTIVATION_CANDIDATE_SCHEMA_VERSION
    )
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    program_id: Literal["AION-SELF-IMPROVEMENT-001"] = PROGRAM_ID
    activation_program_id: Literal[
        "AION-SELF-IMPROVEMENT-CONTROLLED-SHADOW-ACTIVATION-001"
    ] = ACTIVATION_PROGRAM_ID
    implementation_authorization_id: Literal["AION-180-SI-0007"] = (
        AUTHORIZATION_TRANSACTION_ID
    )
    parent_evaluation_id: Literal["AION-SOE-001"] = PARENT_EVALUATION_ID
    parent_evaluation_decision: Literal[
        "SHADOW_MODE_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_ACTIVATION_AUTHORIZATION_REVIEW"
    ] = PARENT_EVALUATION_DECISION
    base_commit_sha: str = Field(min_length=40, max_length=40)
    candidate_commit_sha: str = Field(min_length=40, max_length=40)
    candidate_tree_sha: str = Field(min_length=40, max_length=40)
    diff_sha256: str = Field(min_length=64, max_length=64)
    implementation_evidence_fingerprint: str = Field(min_length=64, max_length=64)
    evaluation_report_fingerprint: str = Field(min_length=64, max_length=64)
    benchmark_manifest_fingerprint: str = Field(min_length=64, max_length=64)
    benchmark_result_fingerprint: str = Field(min_length=64, max_length=64)
    reference_set_fingerprint: str = Field(min_length=64, max_length=64)
    operator_scope_fingerprint: str = Field(min_length=64, max_length=64)
    output_boundary_fingerprint: str = Field(min_length=64, max_length=64)
    run_budget_fingerprint: str = Field(min_length=64, max_length=64)
    monitoring_plan_fingerprint: str = Field(min_length=64, max_length=64)
    deactivation_plan_fingerprint: str = Field(min_length=64, max_length=64)
    rollback_commit_sha: str = Field(min_length=40, max_length=40)
    risk_level: ShadowActivationRiskLevel
    created_at: datetime
    expires_at: datetime
    read_only: bool = True
    redacted: bool = True
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("activation_candidate_id")
    @classmethod
    def candidate_id_is_safe(cls, value: str) -> str:
        return require_activation_identifier(value, "activation_candidate_id")

    @field_validator(
        "base_commit_sha",
        "candidate_commit_sha",
        "candidate_tree_sha",
        "rollback_commit_sha",
    )
    @classmethod
    def commit_shas_are_valid(cls, value: str, info: Any) -> str:
        return require_sha1(value, getattr(info, "field_name", "sha"))

    @field_validator(
        "diff_sha256",
        "implementation_evidence_fingerprint",
        "evaluation_report_fingerprint",
        "benchmark_manifest_fingerprint",
        "benchmark_result_fingerprint",
        "reference_set_fingerprint",
        "operator_scope_fingerprint",
        "output_boundary_fingerprint",
        "run_budget_fingerprint",
        "monitoring_plan_fingerprint",
        "deactivation_plan_fingerprint",
    )
    @classmethod
    def fingerprints_are_valid(cls, value: str, info: Any) -> str:
        return _field_fingerprint(value, info)

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def candidate_is_disabled_and_bounded(self) -> ShadowActivationCandidate:
        _created_before_expiry(self.created_at, self.expires_at, MAXIMUM_RETENTION_SECONDS)
        if self.candidate_commit_sha == _ALL_ZERO_SHA1:
            raise ValueError("candidate commit must be bound to an actual SHA")
        if self.candidate_tree_sha == _ALL_ZERO_SHA1:
            raise ValueError("candidate tree must be bound to an actual SHA")
        if not self.read_only or not self.redacted:
            raise ValueError("activation candidate must be read-only and redacted")
        if self.shadow_activation_enabled or self.runtime_effect:
            raise ValueError("activation candidate cannot enable activation or runtime effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationCandidateValidation(BaseModel):
    """Result of fail-closed candidate validation."""

    model_config = FROZEN_MODEL_CONFIG

    valid: bool
    expired: bool
    binding_mismatches: tuple[str, ...] = Field(default_factory=tuple)
    reason_codes: tuple[str, ...]
    fingerprint: str = ""

    @field_validator("binding_mismatches")
    @classmethod
    def binding_mismatches_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_identifier_tuple(value, "binding_mismatch")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @model_validator(mode="after")
    def validation_is_consistent(self) -> ShadowActivationCandidateValidation:
        if self.expired and "activation_candidate_expired" not in self.reason_codes:
            raise ValueError("expired candidates must include the expired reason")
        if not self.valid and not self.binding_mismatches and not self.expired:
            raise ValueError("invalid candidate validation must explain the mismatch")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationResourceBudget(BaseModel):
    """Exact maximum resource budget for disabled activation simulation."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-budget/v1"] = (
        SHADOW_ACTIVATION_BUDGET_SCHEMA_VERSION
    )
    maximum_activation_window_seconds: int = MAXIMUM_ACTIVATION_WINDOW_SECONDS
    maximum_runs_per_activation: int = MAXIMUM_RUNS_PER_ACTIVATION
    maximum_observation_references_per_run: int = 1000
    maximum_evaluation_records_per_run: int = 1000
    maximum_failure_patterns_per_run: int = 100
    maximum_hypotheses_per_run: int = 50
    maximum_regression_test_proposals_per_run: int = 25
    maximum_shadow_proposals_per_run: int = 10
    maximum_concurrency: int = MAXIMUM_CONCURRENCY
    maximum_wall_clock_seconds_per_run: int = 1800
    maximum_benchmark_cost_units_per_run: int = 50
    maximum_output_bytes_per_run: int = MAXIMUM_EVIDENCE_BUNDLE_BYTES
    maximum_total_output_bytes_per_activation: int = 52428800
    maximum_operator_output_files_per_run: int = 20
    maximum_retention_seconds: int = MAXIMUM_RETENTION_SECONDS
    production_exposure_basis_points: int = 0
    network_calls: int = 0
    connector_calls: int = 0
    provider_calls: int = 0
    git_operations: int = 0
    source_mutations: int = 0
    real_pull_requests: int = 0
    approvals_created: int = 0
    merges: int = 0
    runtime_promotions: int = 0
    production_canaries: int = 0
    deployments: int = 0
    model_training_runs: int = 0
    fingerprint: str = ""

    @field_validator("*")
    @classmethod
    def budget_values_are_non_negative(cls, value: Any) -> Any:
        if isinstance(value, int | float):
            return _finite_non_negative(value, "activation budget")
        return value

    @model_validator(mode="after")
    def budget_never_authorizes_side_effects(self) -> ShadowActivationResourceBudget:
        canonical = canonical_activation_resource_limits()
        for field_name, maximum in canonical.items():
            if getattr(self, field_name) > maximum:
                raise ValueError(f"{field_name} exceeds the authorized activation budget")
        for field_name in (
            "production_exposure_basis_points",
            "network_calls",
            "connector_calls",
            "provider_calls",
            "git_operations",
            "source_mutations",
            "real_pull_requests",
            "approvals_created",
            "merges",
            "runtime_promotions",
            "production_canaries",
            "deployments",
            "model_training_runs",
        ):
            if getattr(self, field_name) != 0:
                raise ValueError(f"{field_name} must be zero")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationResourceUsage(BaseModel):
    """Observed activation-control-plane resource usage."""

    model_config = FROZEN_MODEL_CONFIG

    activation_window_seconds: int = 0
    runs: int = 0
    observation_references: int = 0
    evaluation_records: int = 0
    failure_patterns: int = 0
    hypotheses: int = 0
    regression_test_proposals: int = 0
    shadow_proposals: int = 0
    concurrency: int = 0
    wall_clock_seconds: float = 0.0
    benchmark_cost_units: int = 0
    output_bytes: int = 0
    total_output_bytes: int = 0
    output_files: int = 0
    retention_seconds: int = 0
    production_exposure_basis_points: int = 0
    network_calls: int = 0
    connector_calls: int = 0
    provider_calls: int = 0
    git_operations: int = 0
    source_mutations: int = 0
    real_pull_requests: int = 0
    approvals_created: int = 0
    merges: int = 0
    runtime_promotions: int = 0
    production_canaries: int = 0
    deployments: int = 0
    model_training_runs: int = 0

    @field_validator("*")
    @classmethod
    def usage_values_are_non_negative(cls, value: int | float) -> int | float:
        return _finite_non_negative(value, "activation usage")


class ShadowActivationBudgetDecision(BaseModel):
    """Fail-closed resource-budget decision."""

    model_config = FROZEN_MODEL_CONFIG

    within_budget: bool
    violations: tuple[str, ...]
    usage: ShadowActivationResourceUsage
    budget: ShadowActivationResourceBudget
    fail_closed: bool
    candidate_invalidated: bool
    partial_activation_state_exposed: bool = False
    approval_created: bool = False
    implementation_authorization_created: bool = False
    runtime_effect: bool = False
    reason_codes: tuple[str, ...]
    fingerprint: str = ""

    @field_validator("violations")
    @classmethod
    def violations_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_identifier_tuple(value, "activation_budget_violation")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @model_validator(mode="after")
    def decision_is_consistent(self) -> ShadowActivationBudgetDecision:
        expected = bool(self.violations)
        if self.within_budget == expected:
            raise ValueError("activation budget decision is inconsistent")
        if self.fail_closed != expected or self.candidate_invalidated != expected:
            raise ValueError("activation budget violations must fail closed")
        if any(
            (
                self.partial_activation_state_exposed,
                self.approval_created,
                self.implementation_authorization_created,
                self.runtime_effect,
            )
        ):
            raise ValueError("activation budget decision cannot create side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationOutputBoundary(BaseModel):
    """Read-only output boundary validation contract."""

    model_config = FROZEN_MODEL_CONFIG

    output_directory: str = Field(min_length=1)
    maximum_output_bytes_per_run: int = MAXIMUM_EVIDENCE_BUNDLE_BYTES
    maximum_total_output_bytes: int = 52428800
    maximum_output_files_per_run: int = 20
    overwrite_allowed: bool = False
    hidden_output_allowed: bool = False
    automatic_directory_discovery: bool = False
    background_writer_enabled: bool = False
    repository_output_allowed: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @field_validator(
        "maximum_output_bytes_per_run",
        "maximum_total_output_bytes",
        "maximum_output_files_per_run",
    )
    @classmethod
    def limits_are_bounded(cls, value: int, info: Any) -> int:
        _finite_non_negative(value, getattr(info, "field_name", "limit"))
        return value

    @model_validator(mode="after")
    def boundary_is_read_only(self) -> ShadowActivationOutputBoundary:
        if self.maximum_output_bytes_per_run > MAXIMUM_EVIDENCE_BUNDLE_BYTES:
            raise ValueError("output bytes per run exceeds authorization")
        if self.maximum_total_output_bytes > 52428800:
            raise ValueError("total output bytes exceeds authorization")
        if self.maximum_output_files_per_run > 20:
            raise ValueError("output file count exceeds authorization")
        if any(
            (
                self.overwrite_allowed,
                self.hidden_output_allowed,
                self.automatic_directory_discovery,
                self.background_writer_enabled,
                self.repository_output_allowed,
            )
        ):
            raise ValueError("activation output boundary cannot permit writes or discovery")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationOutputBoundaryValidation(BaseModel):
    """Result of output-boundary validation."""

    model_config = FROZEN_MODEL_CONFIG

    valid: bool
    violations: tuple[str, ...] = Field(default_factory=tuple)
    canonical_output_directory: str | None = None
    reason_codes: tuple[str, ...]
    fingerprint: str = ""

    @field_validator("violations")
    @classmethod
    def violations_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_identifier_tuple(value, "output_boundary_violation")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @model_validator(mode="after")
    def validation_is_consistent(self) -> ShadowActivationOutputBoundaryValidation:
        if self.valid == bool(self.violations):
            raise ValueError("activation output-boundary validation is inconsistent")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationMonitoringThreshold(BaseModel):
    """One threshold for disabled activation monitoring."""

    model_config = FROZEN_MODEL_CONFIG

    metric_name: ShadowActivationMonitoringMetricName
    maximum_value: float = Field(ge=0.0)
    deactivate_on_breach: bool = True
    reason_code: str
    fingerprint: str = ""

    @field_validator("maximum_value")
    @classmethod
    def maximum_value_is_finite(cls, value: float) -> float:
        return float(_finite_non_negative(value, "monitoring maximum value"))

    @field_validator("reason_code")
    @classmethod
    def reason_code_is_registered(cls, value: str) -> str:
        if value not in SHADOW_ACTIVATION_REASON_CODE_SET and value not in (
            SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS
        ):
            raise ValueError("unknown activation monitoring reason code")
        return value

    @model_validator(mode="after")
    def threshold_is_fail_closed(self) -> ShadowActivationMonitoringThreshold:
        if not self.deactivate_on_breach:
            raise ValueError("activation monitoring thresholds must deactivate on breach")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationMonitoringPlan(BaseModel):
    """Monitoring plan bound to one activation candidate."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-monitoring/v1"] = (
        SHADOW_ACTIVATION_MONITORING_SCHEMA_VERSION
    )
    monitoring_plan_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    required_metric_names: tuple[ShadowActivationMonitoringMetricName, ...]
    thresholds: tuple[ShadowActivationMonitoringThreshold, ...]
    forbidden_counters_must_equal_zero: bool = True
    operator_kill_switch_required: bool = True
    evidence_preservation_required: bool = True
    incident_record_required: bool = True
    created_at: datetime
    fingerprint: str = ""

    @field_validator("monitoring_plan_id", "activation_candidate_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("required_metric_names")
    @classmethod
    def metrics_match_registry(
        cls, value: tuple[ShadowActivationMonitoringMetricName, ...]
    ) -> tuple[ShadowActivationMonitoringMetricName, ...]:
        return require_metric_names(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def monitoring_plan_is_complete(self) -> ShadowActivationMonitoringPlan:
        threshold_by_metric = {threshold.metric_name: threshold for threshold in self.thresholds}
        if tuple(threshold_by_metric) != SHADOW_ACTIVATION_MONITORING_METRICS:
            raise ValueError("activation monitoring thresholds must cover every metric")
        if len(threshold_by_metric) != len(self.thresholds):
            raise ValueError("activation monitoring thresholds must be unique")
        for metric_name in FORBIDDEN_COUNTER_METRICS:
            if threshold_by_metric[metric_name].maximum_value != 0:
                raise ValueError("activation forbidden counters must have zero thresholds")
        if not all(
            (
                self.forbidden_counters_must_equal_zero,
                self.operator_kill_switch_required,
                self.evidence_preservation_required,
                self.incident_record_required,
            )
        ):
            raise ValueError("activation monitoring plan must preserve fail-closed controls")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationHealthSnapshot(BaseModel):
    """Synthetic or redacted monitoring snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    activation_candidate_id: str = Field(min_length=1, max_length=128)
    run_count: int = 0
    reference_count: int = 0
    evaluation_count: int = 0
    pattern_count: int = 0
    hypothesis_count: int = 0
    regression_proposal_count: int = 0
    shadow_proposal_count: int = 0
    review_item_count: int = 0
    budget_violation_count: int = 0
    redaction_failure_count: int = 0
    reference_failure_count: int = 0
    fingerprint_mismatch_count: int = 0
    output_boundary_failure_count: int = 0
    wall_clock_seconds: float = 0.0
    benchmark_cost_units: int = 0
    output_bytes: int = 0
    output_files: int = 0
    network_call_count: int = 0
    connector_call_count: int = 0
    provider_call_count: int = 0
    git_operation_count: int = 0
    source_mutation_count: int = 0
    real_pr_count: int = 0
    approval_creation_count: int = 0
    runtime_promotion_count: int = 0
    runtime_influence_count: int = 0
    operator_kill_switch_asserted: bool = False
    observed_at: datetime
    fingerprint: str = ""

    @field_validator("activation_candidate_id")
    @classmethod
    def candidate_id_is_safe(cls, value: str) -> str:
        return require_activation_identifier(value, "activation_candidate_id")

    @field_validator(
        "run_count",
        "reference_count",
        "evaluation_count",
        "pattern_count",
        "hypothesis_count",
        "regression_proposal_count",
        "shadow_proposal_count",
        "review_item_count",
        "budget_violation_count",
        "redaction_failure_count",
        "reference_failure_count",
        "fingerprint_mismatch_count",
        "output_boundary_failure_count",
        "wall_clock_seconds",
        "benchmark_cost_units",
        "output_bytes",
        "output_files",
        "network_call_count",
        "connector_call_count",
        "provider_call_count",
        "git_operation_count",
        "source_mutation_count",
        "real_pr_count",
        "approval_creation_count",
        "runtime_promotion_count",
        "runtime_influence_count",
    )
    @classmethod
    def metric_values_are_non_negative(cls, value: int | float, info: Any) -> int | float:
        return _finite_non_negative(value, getattr(info, "field_name", "metric"))

    @field_validator("observed_at")
    @classmethod
    def observed_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def set_fingerprint(self) -> ShadowActivationHealthSnapshot:
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationMonitoringDecision(BaseModel):
    """Decision produced from one monitoring snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    monitoring_passed: bool
    deactivation_required: bool
    breached_metrics: tuple[str, ...] = Field(default_factory=tuple)
    trigger_codes: tuple[ShadowActivationDeactivationTrigger, ...] = Field(default_factory=tuple)
    forbidden_counter_violation: bool
    window_expired: bool
    run_count_exhausted: bool
    kill_switch_asserted: bool
    runtime_action_performed: bool = False
    runtime_effect: bool = False
    decided_at: datetime
    fingerprint: str = ""

    @field_validator("breached_metrics")
    @classmethod
    def breached_metrics_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_identifier_tuple(value, "breached_metric")

    @field_validator("decided_at")
    @classmethod
    def decided_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def monitoring_decision_is_inert(self) -> ShadowActivationMonitoringDecision:
        if self.monitoring_passed == self.deactivation_required:
            raise ValueError("activation monitoring decision is inconsistent")
        if self.deactivation_required != bool(self.trigger_codes):
            raise ValueError("activation monitoring triggers must require deactivation")
        if self.runtime_action_performed or self.runtime_effect:
            raise ValueError("activation monitoring decision cannot perform runtime actions")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationDeactivationPlan(BaseModel):
    """Immutable deactivation response plan for the disabled control plane."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-deactivation/v1"] = (
        SHADOW_ACTIVATION_DEACTIVATION_SCHEMA_VERSION
    )
    deactivation_plan_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    required_triggers: tuple[ShadowActivationDeactivationTrigger, ...]
    stop_future_runs: bool = True
    preserve_immutable_evidence: bool = True
    create_redacted_incident_record: bool = True
    source_rollback_allowed: bool = False
    runtime_rollback_allowed: bool = False
    automatic_reactivation_allowed: bool = False
    new_authorization_required: bool = True
    created_at: datetime
    fingerprint: str = ""

    @field_validator("deactivation_plan_id", "activation_candidate_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def plan_is_fail_closed(self) -> ShadowActivationDeactivationPlan:
        if tuple(self.required_triggers) != SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS:
            raise ValueError("activation deactivation triggers must match the registry")
        if not all(
            (
                self.stop_future_runs,
                self.preserve_immutable_evidence,
                self.create_redacted_incident_record,
                self.new_authorization_required,
            )
        ):
            raise ValueError(
                "activation deactivation plan must preserve evidence and require review"
            )
        if any(
            (
                self.source_rollback_allowed,
                self.runtime_rollback_allowed,
                self.automatic_reactivation_allowed,
            )
        ):
            raise ValueError("activation deactivation plan cannot authorize side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationDeactivationDecision(BaseModel):
    """Advisory deactivation decision evidence."""

    model_config = FROZEN_MODEL_CONFIG

    decision_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    triggered: bool
    triggers: tuple[ShadowActivationDeactivationTrigger, ...] = Field(default_factory=tuple)
    stop_future_runs: bool
    preserve_immutable_evidence: bool
    incident_record_required: bool
    runtime_action_performed: bool = False
    source_action_performed: bool = False
    reactivation_authorized: bool = False
    runtime_effect: bool = False
    decided_at: datetime
    fingerprint: str = ""

    @field_validator("decision_id", "activation_candidate_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("decided_at")
    @classmethod
    def decided_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def decision_is_advisory_only(self) -> ShadowActivationDeactivationDecision:
        if self.triggered != bool(self.triggers):
            raise ValueError("activation deactivation trigger state is inconsistent")
        if self.triggered and not all(
            (self.stop_future_runs, self.preserve_immutable_evidence, self.incident_record_required)
        ):
            raise ValueError("activation deactivation must preserve fail-closed evidence")
        if any(
            (
                self.runtime_action_performed,
                self.source_action_performed,
                self.reactivation_authorized,
                self.runtime_effect,
            )
        ):
            raise ValueError("activation deactivation decision cannot perform side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationRequest(BaseModel):
    """Disabled activation request bound to exact candidate facts."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-request/v1"] = (
        SHADOW_ACTIVATION_REQUEST_SCHEMA_VERSION
    )
    activation_request_id: str = Field(min_length=1, max_length=128)
    activation_candidate: ShadowActivationCandidate
    requesting_operator_principal_id: str = Field(min_length=1, max_length=128)
    requested_environment: ShadowActivationEnvironment = "local_offline_operator_evaluation"
    data_classification: ShadowActivationDataClassification
    allowed_reference_kinds: tuple[str, ...]
    approved_reference_fingerprints: tuple[str, ...]
    approved_adapter_types: tuple[ShadowActivationAdapterType, ...]
    maximum_runs: int = Field(ge=1, le=MAXIMUM_RUNS_PER_ACTIVATION)
    activation_window_start: datetime
    activation_window_end: datetime
    resource_budget: ShadowActivationResourceBudget
    monitoring_plan: ShadowActivationMonitoringPlan
    deactivation_plan: ShadowActivationDeactivationPlan
    output_boundary: ShadowActivationOutputBoundary
    retention_seconds: int = Field(ge=0, le=MAXIMUM_RETENTION_SECONDS)
    operator_review_required: bool = True
    runtime_activation_requested: bool = False
    created_at: datetime
    read_only: bool = True
    redacted: bool = True
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("activation_request_id", "requesting_operator_principal_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("allowed_reference_kinds")
    @classmethod
    def reference_kinds_are_authorized(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("activation request must bind at least one reference kind")
        if len(value) != len(set(value)):
            raise ValueError("activation reference kinds must be unique")
        for item in value:
            require_activation_identifier(item, "allowed_reference_kind")
            if item not in SHADOW_REFERENCE_KINDS:
                raise ValueError("unknown activation reference kind")
        return value

    @field_validator("approved_reference_fingerprints")
    @classmethod
    def reference_fingerprints_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _fingerprint_tuple(value, "approved_reference_fingerprint")

    @field_validator("approved_adapter_types")
    @classmethod
    def adapter_types_are_authorized(
        cls, value: tuple[ShadowActivationAdapterType, ...]
    ) -> tuple[ShadowActivationAdapterType, ...]:
        if not value:
            raise ValueError("activation request must name at least one adapter type")
        if len(value) != len(set(value)):
            raise ValueError("activation adapter types must be unique")
        for item in value:
            if item not in SHADOW_ACTIVATION_ADAPTER_TYPES:
                raise ValueError("unknown activation adapter type")
        return value

    @field_validator("activation_window_start", "activation_window_end", "created_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def request_is_disabled_and_bound(self) -> ShadowActivationRequest:
        if self.activation_window_end <= self.activation_window_start:
            raise ValueError("activation window must be positive")
        if (
            self.activation_window_end - self.activation_window_start
        ).total_seconds() > MAXIMUM_ACTIVATION_WINDOW_SECONDS:
            raise ValueError("activation window exceeds authorization")
        candidate = self.activation_candidate
        if candidate.reference_set_fingerprint not in self.approved_reference_fingerprints:
            raise ValueError("activation reference set is not bound")
        if self.output_boundary.fingerprint != candidate.output_boundary_fingerprint:
            raise ValueError("activation output boundary fingerprint mismatch")
        if self.resource_budget.fingerprint != candidate.run_budget_fingerprint:
            raise ValueError("activation resource budget fingerprint mismatch")
        if self.monitoring_plan.activation_candidate_id != candidate.activation_candidate_id:
            raise ValueError("activation monitoring candidate mismatch")
        if self.monitoring_plan.fingerprint != candidate.monitoring_plan_fingerprint:
            raise ValueError("activation monitoring plan fingerprint mismatch")
        if self.deactivation_plan.activation_candidate_id != candidate.activation_candidate_id:
            raise ValueError("activation deactivation candidate mismatch")
        if self.deactivation_plan.fingerprint != candidate.deactivation_plan_fingerprint:
            raise ValueError("activation deactivation plan fingerprint mismatch")
        if not self.operator_review_required:
            raise ValueError("activation request requires operator review")
        if any(
            (
                self.runtime_activation_requested,
                not self.read_only,
                not self.redacted,
                self.shadow_activation_enabled,
                self.runtime_effect,
            )
        ):
            raise ValueError("activation request cannot authorize runtime effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationApprovalBinding(BaseModel):
    """Externally supplied approval evidence bound to exact immutable facts."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-approval/v1"] = (
        SHADOW_ACTIVATION_APPROVAL_SCHEMA_VERSION
    )
    activation_request_id: str
    activation_candidate_id: str
    base_commit_sha: str
    candidate_commit_sha: str
    candidate_tree_sha: str
    diff_sha256: str
    implementation_evidence_fingerprint: str
    evaluation_report_fingerprint: str
    benchmark_manifest_fingerprint: str
    benchmark_result_fingerprint: str
    reference_set_fingerprint: str
    operator_scope_fingerprint: str
    output_boundary_fingerprint: str
    run_budget_fingerprint: str
    monitoring_plan_fingerprint: str
    deactivation_plan_fingerprint: str
    rollback_commit_sha: str
    requesting_operator_principal_id: str
    approver_principal_ids: tuple[str, ...]
    security_reviewer_principal_ids: tuple[str, ...]
    activation_window_start: datetime
    activation_window_end: datetime
    maximum_runs: int
    approved_adapter_types: tuple[ShadowActivationAdapterType, ...]
    approved_reference_fingerprints: tuple[str, ...]
    approved_environment: ShadowActivationEnvironment
    approved_at: datetime
    expires_at: datetime
    consumed: bool
    reusable: bool = False
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator(
        "activation_request_id",
        "activation_candidate_id",
        "requesting_operator_principal_id",
    )
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator(
        "base_commit_sha",
        "candidate_commit_sha",
        "candidate_tree_sha",
        "rollback_commit_sha",
    )
    @classmethod
    def shas_are_valid(cls, value: str, info: Any) -> str:
        return require_sha1(value, getattr(info, "field_name", "sha"))

    @field_validator(
        "diff_sha256",
        "implementation_evidence_fingerprint",
        "evaluation_report_fingerprint",
        "benchmark_manifest_fingerprint",
        "benchmark_result_fingerprint",
        "reference_set_fingerprint",
        "operator_scope_fingerprint",
        "output_boundary_fingerprint",
        "run_budget_fingerprint",
        "monitoring_plan_fingerprint",
        "deactivation_plan_fingerprint",
    )
    @classmethod
    def fingerprints_are_valid(cls, value: str, info: Any) -> str:
        return _field_fingerprint(value, info)

    @field_validator("approver_principal_ids", "security_reviewer_principal_ids")
    @classmethod
    def principal_tuples_are_safe(cls, value: tuple[str, ...], info: Any) -> tuple[str, ...]:
        return tuple(
            require_activation_identifier(item, getattr(info, "field_name", "principal"))
            for item in value
        )

    @field_validator("approved_reference_fingerprints")
    @classmethod
    def approved_refs_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _fingerprint_tuple(value, "approved_reference_fingerprint")

    @field_validator(
        "activation_window_start",
        "activation_window_end",
        "approved_at",
        "expires_at",
    )
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def binding_is_external_and_inert(self) -> ShadowActivationApprovalBinding:
        if (self.expires_at - self.approved_at).total_seconds() > MAXIMUM_RETENTION_SECONDS:
            raise ValueError("activation approval lifetime exceeds the authorized maximum")
        if self.activation_window_end <= self.activation_window_start:
            raise ValueError("activation approval window must be positive")
        if self.maximum_runs < 1 or self.maximum_runs > MAXIMUM_RUNS_PER_ACTIVATION:
            raise ValueError("activation approval maximum runs out of bounds")
        if not self.read_only or not self.redacted:
            raise ValueError("activation approval evidence must be redacted and read-only")
        if self.runtime_effect:
            raise ValueError("activation approval evidence cannot create runtime effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationCurrentFacts(BaseModel):
    """Current immutable facts used to revalidate approval binding."""

    model_config = FROZEN_MODEL_CONFIG

    activation_request_id: str
    activation_candidate_id: str
    base_commit_sha: str
    candidate_commit_sha: str
    candidate_tree_sha: str
    diff_sha256: str
    implementation_evidence_fingerprint: str
    evaluation_report_fingerprint: str
    benchmark_manifest_fingerprint: str
    benchmark_result_fingerprint: str
    reference_set_fingerprint: str
    operator_scope_fingerprint: str
    output_boundary_fingerprint: str
    run_budget_fingerprint: str
    monitoring_plan_fingerprint: str
    deactivation_plan_fingerprint: str
    rollback_commit_sha: str
    requesting_operator_principal_id: str
    activation_window_start: datetime
    activation_window_end: datetime
    maximum_runs: int
    approved_adapter_types: tuple[ShadowActivationAdapterType, ...]
    approved_reference_fingerprints: tuple[str, ...]
    approved_environment: ShadowActivationEnvironment
    fingerprint: str = ""

    @field_validator(
        "activation_request_id",
        "activation_candidate_id",
        "requesting_operator_principal_id",
    )
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator(
        "base_commit_sha",
        "candidate_commit_sha",
        "candidate_tree_sha",
        "rollback_commit_sha",
    )
    @classmethod
    def shas_are_valid(cls, value: str, info: Any) -> str:
        return require_sha1(value, getattr(info, "field_name", "sha"))

    @field_validator(
        "diff_sha256",
        "implementation_evidence_fingerprint",
        "evaluation_report_fingerprint",
        "benchmark_manifest_fingerprint",
        "benchmark_result_fingerprint",
        "reference_set_fingerprint",
        "operator_scope_fingerprint",
        "output_boundary_fingerprint",
        "run_budget_fingerprint",
        "monitoring_plan_fingerprint",
        "deactivation_plan_fingerprint",
    )
    @classmethod
    def fingerprints_are_valid(cls, value: str, info: Any) -> str:
        return _field_fingerprint(value, info)

    @field_validator("approved_reference_fingerprints")
    @classmethod
    def refs_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _fingerprint_tuple(value, "approved_reference_fingerprint")

    @field_validator("activation_window_start", "activation_window_end")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def facts_are_fingerprinted(self) -> ShadowActivationCurrentFacts:
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationApprovalValidation(BaseModel):
    """Approval-binding validation result."""

    model_config = FROZEN_MODEL_CONFIG

    valid: bool
    expired: bool
    consumed: bool
    reusable: bool
    self_approval_detected: bool
    separation_of_duties_satisfied: bool
    security_review_satisfied: bool
    binding_mismatches: tuple[str, ...] = Field(default_factory=tuple)
    reason_codes: tuple[str, ...]
    fingerprint: str = ""

    @field_validator("binding_mismatches")
    @classmethod
    def binding_mismatches_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_identifier_tuple(value, "approval_binding_mismatch")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @model_validator(mode="after")
    def validation_is_consistent(self) -> ShadowActivationApprovalValidation:
        if self.valid and (
            self.expired
            or self.consumed
            or self.reusable
            or self.self_approval_detected
            or self.binding_mismatches
            or not self.separation_of_duties_satisfied
            or not self.security_review_satisfied
        ):
            raise ValueError("valid activation approval cannot carry failing evidence")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationTransitionDecision(BaseModel):
    """Pure state-machine transition decision."""

    model_config = FROZEN_MODEL_CONFIG

    current_state: str
    next_state: str
    allowed: bool
    reason_codes: tuple[str, ...]
    fingerprint: str = ""

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @model_validator(mode="after")
    def set_fingerprint(self) -> ShadowActivationTransitionDecision:
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationStateRecord(BaseModel):
    """Immutable activation-control-plane state evidence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-state/v1"] = (
        SHADOW_ACTIVATION_STATE_SCHEMA_VERSION
    )
    state_record_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    previous_state: str | None = None
    current_state: ShadowActivationState
    sequence_number: int = Field(ge=0)
    reason_code: ShadowActivationTransitionReason
    actor_principal_id: str = Field(min_length=1, max_length=128)
    transitioned_at: datetime
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("state_record_id", "activation_candidate_id", "actor_principal_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("transitioned_at")
    @classmethod
    def transitioned_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def state_record_is_disabled(self) -> ShadowActivationStateRecord:
        if self.previous_state in FORBIDDEN_SHADOW_ACTIVATION_STATES:
            raise ValueError("activation state record cannot reference a forbidden state")
        if self.current_state in FORBIDDEN_SHADOW_ACTIVATION_STATES:
            raise ValueError("activation state record cannot enter a forbidden state")
        if self.shadow_activation_enabled or self.runtime_effect:
            raise ValueError("activation state record cannot enable runtime effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationIncidentRecord(BaseModel):
    """Redacted incident evidence for deactivation decisions."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-incident/v1"] = (
        SHADOW_ACTIVATION_INCIDENT_SCHEMA_VERSION
    )
    incident_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    activation_request_id: str = Field(min_length=1, max_length=128)
    incident_type: str = Field(min_length=1, max_length=128)
    trigger_codes: tuple[ShadowActivationDeactivationTrigger, ...]
    monitoring_snapshot_fingerprint: str = Field(min_length=64, max_length=64)
    deactivation_plan_fingerprint: str = Field(min_length=64, max_length=64)
    redacted: bool = True
    read_only: bool = True
    source_action_performed: bool = False
    runtime_action_performed: bool = False
    reactivation_authorized: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator(
        "incident_id",
        "activation_candidate_id",
        "activation_request_id",
        "incident_type",
    )
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("monitoring_snapshot_fingerprint", "deactivation_plan_fingerprint")
    @classmethod
    def fingerprints_are_valid(cls, value: str, info: Any) -> str:
        return _field_fingerprint(value, info)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def incident_is_redacted_and_inert(self) -> ShadowActivationIncidentRecord:
        if not self.redacted or not self.read_only:
            raise ValueError("activation incident must be redacted and read-only")
        if any(
            (
                self.source_action_performed,
                self.runtime_action_performed,
                self.reactivation_authorized,
            )
        ):
            raise ValueError("activation incident cannot perform side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationAuditEvent(BaseModel):
    """Redacted audit event for disabled control-plane decisions."""

    model_config = FROZEN_MODEL_CONFIG

    audit_event_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    activation_request_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=128)
    decision_outcome: ShadowActivationDecisionOutcome
    reason_codes: tuple[str, ...]
    created_at: datetime
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator(
        "audit_event_id",
        "activation_candidate_id",
        "activation_request_id",
        "event_type",
    )
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def event_is_inert(self) -> ShadowActivationAuditEvent:
        if not self.read_only or not self.redacted or self.runtime_effect:
            raise ValueError("activation audit event must be redacted and inert")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationProvenanceRecord(BaseModel):
    """Redacted provenance for activation-control-plane decisions."""

    model_config = FROZEN_MODEL_CONFIG

    provenance_record_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    activation_request_id: str = Field(min_length=1, max_length=128)
    authorization_transaction_id: Literal["AION-180-SI-0007"] = AUTHORIZATION_TRANSACTION_ID
    evidence_fingerprints: dict[str, str]
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator("provenance_record_id", "activation_candidate_id", "activation_request_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def provenance_is_safe(self) -> ShadowActivationProvenanceRecord:
        for key, value in self.evidence_fingerprints.items():
            require_activation_identifier(key, "evidence_fingerprint_key")
            require_fingerprint(value, "evidence_fingerprint")
        if not self.read_only or not self.redacted or self.runtime_effect:
            raise ValueError("activation provenance must be redacted and inert")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationDiagnostics(BaseModel):
    """Diagnostics proving the disabled control plane has no side effects."""

    model_config = FROZEN_MODEL_CONFIG

    diagnostics_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    activation_request_id: str = Field(min_length=1, max_length=128)
    candidate_valid: bool
    request_valid: bool
    approval_valid: bool
    budget_within_limits: bool
    monitoring_passed: bool
    deactivation_required: bool
    shadow_activation_enabled: bool = False
    actual_activation_authorized: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    approval_created: bool = False
    merged: bool = False
    active_learning_promoted: bool = False
    production_exposure: bool = False
    runtime_effect: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator("diagnostics_id", "activation_candidate_id", "activation_request_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def diagnostics_are_disabled(self) -> ShadowActivationDiagnostics:
        if any(
            (
                self.shadow_activation_enabled,
                self.actual_activation_authorized,
                self.source_modified,
                self.git_mutated,
                self.pull_request_created,
                self.approval_created,
                self.merged,
                self.active_learning_promoted,
                self.production_exposure,
                self.runtime_effect,
            )
        ):
            raise ValueError("activation diagnostics cannot record enabled runtime effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationOperatorReviewItem(BaseModel):
    """Operator review evidence; not an approval or authorization."""

    model_config = FROZEN_MODEL_CONFIG

    review_item_id: str = Field(min_length=1, max_length=128)
    activation_candidate_id: str = Field(min_length=1, max_length=128)
    activation_request_id: str = Field(min_length=1, max_length=128)
    current_state: ShadowActivationState
    decision_outcome: ShadowActivationDecisionOutcome
    candidate_validation_summary: str
    approval_validation_summary: str
    budget_summary: str
    monitoring_summary: str
    deactivation_summary: str
    evidence_fingerprints: dict[str, str]
    reason_codes: tuple[str, ...]
    operator_review_required: bool = True
    actual_activation_authorized: bool = False
    implementation_authorization_created: bool = False
    activation_approval_created: bool = False
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    created_at: datetime
    expires_at: datetime
    fingerprint: str = ""

    @field_validator("review_item_id", "activation_candidate_id", "activation_request_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator(
        "candidate_validation_summary",
        "approval_validation_summary",
        "budget_summary",
        "monitoring_summary",
        "deactivation_summary",
    )
    @classmethod
    def summaries_are_safe(cls, value: str, info: Any) -> str:
        return _safe_text(value, getattr(info, "field_name", "summary"), 512)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def review_item_is_evidence_only(self) -> ShadowActivationOperatorReviewItem:
        _created_before_expiry(self.created_at, self.expires_at, MAXIMUM_RETENTION_SECONDS)
        for key, value in self.evidence_fingerprints.items():
            require_activation_identifier(key, "review_evidence_key")
            require_fingerprint(value, "review_evidence_fingerprint")
        if any(
            (
                not self.operator_review_required,
                self.actual_activation_authorized,
                self.implementation_authorization_created,
                self.activation_approval_created,
                self.shadow_activation_enabled,
                self.runtime_effect,
            )
        ):
            raise ValueError("activation review item cannot approve or activate")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationEvidenceBundle(BaseModel):
    """Immutable evaluation evidence bundle for one control-plane decision."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-activation-evidence/v1"] = (
        SHADOW_ACTIVATION_EVIDENCE_SCHEMA_VERSION
    )
    activation_candidate_id: str
    activation_request_id: str
    decision_outcome: ShadowActivationDecisionOutcome
    audit_events: tuple[ShadowActivationAuditEvent, ...]
    provenance: ShadowActivationProvenanceRecord
    diagnostics: ShadowActivationDiagnostics
    incidents: tuple[ShadowActivationIncidentRecord, ...] = Field(default_factory=tuple)
    operator_review_item: ShadowActivationOperatorReviewItem
    read_only: bool = True
    redacted: bool = True
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator("activation_candidate_id", "activation_request_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: Any) -> str:
        return require_activation_identifier(value, getattr(info, "field_name", "identifier"))

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def evidence_is_inert(self) -> ShadowActivationEvidenceBundle:
        if not self.read_only or not self.redacted:
            raise ValueError("activation evidence bundle must be redacted and read-only")
        if self.shadow_activation_enabled or self.runtime_effect:
            raise ValueError("activation evidence bundle cannot activate runtime")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationEvaluationBundle(BaseModel):
    """Full disabled control-plane evaluation result."""

    model_config = FROZEN_MODEL_CONFIG

    decision_outcome: ShadowActivationDecisionOutcome
    candidate_validation: ShadowActivationCandidateValidation
    approval_validation: ShadowActivationApprovalValidation | None = None
    budget_decision: ShadowActivationBudgetDecision
    monitoring_decision: ShadowActivationMonitoringDecision
    deactivation_decision: ShadowActivationDeactivationDecision
    evidence_bundle: ShadowActivationEvidenceBundle
    reason_codes: tuple[str, ...]
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_activation_reason_codes(value)

    @model_validator(mode="after")
    def evaluation_is_disabled(self) -> ShadowActivationEvaluationBundle:
        if str(self.decision_outcome) == "active":
            raise ValueError("activation control plane cannot return active")
        if self.shadow_activation_enabled or self.runtime_effect:
            raise ValueError("activation control plane cannot create runtime effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


def canonical_activation_resource_limits() -> dict[str, int]:
    """Return the exact immutable activation resource limits."""

    return {
        "maximum_activation_window_seconds": MAXIMUM_ACTIVATION_WINDOW_SECONDS,
        "maximum_runs_per_activation": MAXIMUM_RUNS_PER_ACTIVATION,
        "maximum_observation_references_per_run": 1000,
        "maximum_evaluation_records_per_run": 1000,
        "maximum_failure_patterns_per_run": 100,
        "maximum_hypotheses_per_run": 50,
        "maximum_regression_test_proposals_per_run": 25,
        "maximum_shadow_proposals_per_run": 10,
        "maximum_concurrency": MAXIMUM_CONCURRENCY,
        "maximum_wall_clock_seconds_per_run": 1800,
        "maximum_benchmark_cost_units_per_run": 50,
        "maximum_output_bytes_per_run": MAXIMUM_EVIDENCE_BUNDLE_BYTES,
        "maximum_total_output_bytes_per_activation": 52428800,
        "maximum_operator_output_files_per_run": 20,
        "maximum_retention_seconds": MAXIMUM_RETENTION_SECONDS,
        "production_exposure_basis_points": 0,
        "network_calls": 0,
        "connector_calls": 0,
        "provider_calls": 0,
        "git_operations": 0,
        "source_mutations": 0,
        "real_pull_requests": 0,
        "approvals_created": 0,
        "merges": 0,
        "runtime_promotions": 0,
        "production_canaries": 0,
        "deployments": 0,
        "model_training_runs": 0,
    }


def validate_activation_candidate(
    candidate: ShadowActivationCandidate,
    *,
    expected_base_commit_sha: str | None = None,
    now: datetime | None = None,
) -> ShadowActivationCandidateValidation:
    """Validate immutable candidate facts without side effects."""

    checked_at = require_utc_datetime(now or utc_now())
    mismatches: list[str] = []
    if expected_base_commit_sha is not None:
        expected_base = require_sha1(
            expected_base_commit_sha,
            "expected_base_commit_sha",
        )
        if expected_base != candidate.base_commit_sha:
            mismatches.append("base_commit_sha")
    if candidate.implementation_authorization_id != AUTHORIZATION_TRANSACTION_ID:
        mismatches.append("implementation_authorization_id")
    if candidate.parent_evaluation_id != PARENT_EVALUATION_ID:
        mismatches.append("parent_evaluation_id")
    if candidate.parent_evaluation_decision != PARENT_EVALUATION_DECISION:
        mismatches.append("parent_evaluation_decision")
    if candidate.shadow_activation_enabled or candidate.runtime_effect:
        mismatches.append("runtime_disabled_flags")
    expired = candidate.expires_at <= checked_at
    reason_codes: list[str] = []
    if expired:
        reason_codes.append("activation_candidate_expired")
    if mismatches:
        reason_codes.append("activation_candidate_invalid")
    if not expired and not mismatches:
        reason_codes.append("activation_candidate_valid")
        reason_codes.append("activation_scope_control_plane_only")
        reason_codes.append("activation_runtime_disabled")
    return ShadowActivationCandidateValidation(
        valid=not expired and not mismatches,
        expired=expired,
        binding_mismatches=tuple(mismatches),
        reason_codes=tuple(reason_codes),
    )


def evaluate_shadow_activation_budget(
    usage: ShadowActivationResourceUsage,
    budget: ShadowActivationResourceBudget,
) -> ShadowActivationBudgetDecision:
    """Evaluate every activation budget dimension in deterministic order."""

    checks = (
        ("maximum_activation_window_seconds", usage.activation_window_seconds),
        ("maximum_runs_per_activation", usage.runs),
        ("maximum_observation_references_per_run", usage.observation_references),
        ("maximum_evaluation_records_per_run", usage.evaluation_records),
        ("maximum_failure_patterns_per_run", usage.failure_patterns),
        ("maximum_hypotheses_per_run", usage.hypotheses),
        ("maximum_regression_test_proposals_per_run", usage.regression_test_proposals),
        ("maximum_shadow_proposals_per_run", usage.shadow_proposals),
        ("maximum_concurrency", usage.concurrency),
        ("maximum_wall_clock_seconds_per_run", usage.wall_clock_seconds),
        ("maximum_benchmark_cost_units_per_run", usage.benchmark_cost_units),
        ("maximum_output_bytes_per_run", usage.output_bytes),
        ("maximum_total_output_bytes_per_activation", usage.total_output_bytes),
        ("maximum_operator_output_files_per_run", usage.output_files),
        ("maximum_retention_seconds", usage.retention_seconds),
        ("production_exposure_basis_points", usage.production_exposure_basis_points),
        ("network_calls", usage.network_calls),
        ("connector_calls", usage.connector_calls),
        ("provider_calls", usage.provider_calls),
        ("git_operations", usage.git_operations),
        ("source_mutations", usage.source_mutations),
        ("real_pull_requests", usage.real_pull_requests),
        ("approvals_created", usage.approvals_created),
        ("merges", usage.merges),
        ("runtime_promotions", usage.runtime_promotions),
        ("production_canaries", usage.production_canaries),
        ("deployments", usage.deployments),
        ("model_training_runs", usage.model_training_runs),
    )
    violations = tuple(
        field_name
        for field_name, observed in checks
        if observed > getattr(budget, field_name)
    )
    reason_codes = (
        ("activation_budget_satisfied",)
        if not violations
        else (
            "activation_budget_exceeded",
            "activation_runtime_disabled",
            "activation_actual_activation_unauthorized",
        )
    )
    return ShadowActivationBudgetDecision(
        within_budget=not violations,
        violations=violations,
        usage=usage,
        budget=budget,
        fail_closed=bool(violations),
        candidate_invalidated=bool(violations),
        reason_codes=reason_codes,
    )


def validate_shadow_activation_output_boundary(
    boundary: ShadowActivationOutputBoundary,
    *,
    repository_root: Path,
) -> ShadowActivationOutputBoundaryValidation:
    """Validate an explicit output directory without creating or writing files."""

    violations: list[str] = []
    text = boundary.output_directory
    if "://" in text or text.startswith("//"):
        violations.append("network_path")
    if "$" in text or text.startswith("~"):
        violations.append("expanded_path_syntax")
    path = Path(text)
    if not path.is_absolute():
        violations.append("relative_path")
    if ".." in path.parts:
        violations.append("path_traversal")
    if any(part.startswith(".") for part in path.parts if part not in {"/"}):
        violations.append("hidden_path_component")
    resolved_root = repository_root.resolve(strict=True)
    resolved_path: Path | None = None
    try:
        for candidate in (path, *path.parents):
            if candidate.exists() and candidate.is_symlink():
                violations.append("symlink_path")
                break
        resolved_path = path.resolve(strict=True)
    except OSError:
        violations.append("path_unavailable")
    if resolved_path is not None:
        if not resolved_path.is_dir():
            violations.append("not_directory")
        if resolved_path == resolved_root or resolved_root in resolved_path.parents:
            violations.append("repository_path")
    valid = not violations
    return ShadowActivationOutputBoundaryValidation(
        valid=valid,
        violations=tuple(violations),
        canonical_output_directory=(
            str(resolved_path) if valid and resolved_path is not None else None
        ),
        reason_codes=(
            ("activation_output_boundary_valid",)
            if valid
            else ("activation_output_boundary_invalid", "activation_runtime_disabled")
        ),
    )


def evaluate_shadow_activation_health(
    snapshot: ShadowActivationHealthSnapshot,
    plan: ShadowActivationMonitoringPlan,
    *,
    activation_window_end: datetime,
    maximum_runs: int,
    now: datetime | None = None,
) -> ShadowActivationMonitoringDecision:
    """Evaluate one health snapshot and return advisory deactivation triggers."""

    checked_at = require_utc_datetime(now or utc_now())
    window_end = require_utc_datetime(activation_window_end)
    if snapshot.activation_candidate_id != plan.activation_candidate_id:
        raise ValueError("activation monitoring candidate mismatch")
    threshold_by_metric = {threshold.metric_name: threshold for threshold in plan.thresholds}
    breached_metrics: list[str] = []
    triggers: list[ShadowActivationDeactivationTrigger] = []
    forbidden_violation = False
    for metric_name in SHADOW_ACTIVATION_MONITORING_METRICS:
        observed = getattr(snapshot, metric_name)
        threshold = threshold_by_metric[metric_name]
        if metric_name in FAILURE_TRIGGER_BY_METRIC and observed > 0:
            breached_metrics.append(metric_name)
            triggers.append(FAILURE_TRIGGER_BY_METRIC[metric_name])
            continue
        if observed > threshold.maximum_value:
            breached_metrics.append(metric_name)
            if metric_name in FORBIDDEN_COUNTER_TRIGGER_BY_METRIC:
                forbidden_violation = True
                triggers.append(FORBIDDEN_COUNTER_TRIGGER_BY_METRIC[metric_name])
    if snapshot.operator_kill_switch_asserted:
        triggers.append("operator_kill_switch_asserted")
    window_expired = checked_at >= window_end
    if window_expired:
        triggers.append("activation_window_expired")
    run_count_exhausted = snapshot.run_count >= maximum_runs
    if run_count_exhausted:
        triggers.append("run_count_exhausted")
    unique_triggers = tuple(dict.fromkeys(triggers))
    return ShadowActivationMonitoringDecision(
        monitoring_passed=not unique_triggers,
        deactivation_required=bool(unique_triggers),
        breached_metrics=tuple(dict.fromkeys(breached_metrics)),
        trigger_codes=unique_triggers,
        forbidden_counter_violation=forbidden_violation,
        window_expired=window_expired,
        run_count_exhausted=run_count_exhausted,
        kill_switch_asserted=snapshot.operator_kill_switch_asserted,
        decided_at=checked_at,
    )


def evaluate_shadow_activation_deactivation(
    *,
    health_decision: ShadowActivationMonitoringDecision,
    deactivation_plan: ShadowActivationDeactivationPlan,
    now: datetime | None = None,
    decision_id: str = "shadow-activation-deactivation-decision",
) -> ShadowActivationDeactivationDecision:
    """Create advisory deactivation evidence without touching runtime state."""

    checked_at = require_utc_datetime(now or utc_now())
    return ShadowActivationDeactivationDecision(
        decision_id=decision_id,
        activation_candidate_id=deactivation_plan.activation_candidate_id,
        triggered=health_decision.deactivation_required,
        triggers=health_decision.trigger_codes,
        stop_future_runs=health_decision.deactivation_required,
        preserve_immutable_evidence=True,
        incident_record_required=health_decision.deactivation_required,
        decided_at=checked_at,
    )


def build_current_facts_from_request(
    request: ShadowActivationRequest,
) -> ShadowActivationCurrentFacts:
    """Build the immutable facts that an external approval must match."""

    candidate = request.activation_candidate
    return ShadowActivationCurrentFacts(
        activation_request_id=request.activation_request_id,
        activation_candidate_id=candidate.activation_candidate_id,
        base_commit_sha=candidate.base_commit_sha,
        candidate_commit_sha=candidate.candidate_commit_sha,
        candidate_tree_sha=candidate.candidate_tree_sha,
        diff_sha256=candidate.diff_sha256,
        implementation_evidence_fingerprint=candidate.implementation_evidence_fingerprint,
        evaluation_report_fingerprint=candidate.evaluation_report_fingerprint,
        benchmark_manifest_fingerprint=candidate.benchmark_manifest_fingerprint,
        benchmark_result_fingerprint=candidate.benchmark_result_fingerprint,
        reference_set_fingerprint=candidate.reference_set_fingerprint,
        operator_scope_fingerprint=candidate.operator_scope_fingerprint,
        output_boundary_fingerprint=candidate.output_boundary_fingerprint,
        run_budget_fingerprint=candidate.run_budget_fingerprint,
        monitoring_plan_fingerprint=candidate.monitoring_plan_fingerprint,
        deactivation_plan_fingerprint=candidate.deactivation_plan_fingerprint,
        rollback_commit_sha=candidate.rollback_commit_sha,
        requesting_operator_principal_id=request.requesting_operator_principal_id,
        activation_window_start=request.activation_window_start,
        activation_window_end=request.activation_window_end,
        maximum_runs=request.maximum_runs,
        approved_adapter_types=request.approved_adapter_types,
        approved_reference_fingerprints=request.approved_reference_fingerprints,
        approved_environment=request.requested_environment,
    )


def validate_shadow_activation_approval(
    *,
    approval: ShadowActivationApprovalBinding,
    candidate: ShadowActivationCandidate,
    request: ShadowActivationRequest,
    current_facts: ShadowActivationCurrentFacts,
    now: datetime | None = None,
) -> ShadowActivationApprovalValidation:
    """Validate externally supplied approval evidence against current facts."""

    checked_at = require_utc_datetime(now or utc_now())
    expected = build_current_facts_from_request(request)
    mismatches: list[str] = []
    for field_name in type(expected).model_fields:
        if field_name == "fingerprint":
            continue
        if getattr(current_facts, field_name) != getattr(expected, field_name):
            mismatches.append(f"current_{field_name}")
        if hasattr(approval, field_name) and getattr(approval, field_name) != getattr(
            expected,
            field_name,
        ):
            mismatches.append(field_name)
    if approval.activation_candidate_id != candidate.activation_candidate_id:
        mismatches.append("candidate_identity")
    expired = approval.expires_at <= checked_at
    consumed = approval.consumed
    reusable = approval.reusable
    requester = approval.requesting_operator_principal_id
    approvers = approval.approver_principal_ids
    reviewers = approval.security_reviewer_principal_ids
    machine_or_invalid = {
        principal
        for principal in (*approvers, *reviewers)
        if _principal_is_machine_or_forbidden(principal)
    }
    self_approval = requester in approvers or requester in reviewers
    approver_unique = len(approvers) == len(set(approvers))
    reviewer_unique = len(reviewers) == len(set(reviewers))
    approver_count_ok = len(set(approvers)) >= 2
    independent_security = bool(set(reviewers)) and not (set(approvers) & set(reviewers))
    separation = (
        approver_unique
        and reviewer_unique
        and approver_count_ok
        and not self_approval
        and not machine_or_invalid
    )
    security = independent_security and requester not in reviewers and not machine_or_invalid
    reason_codes: list[str] = []
    if expired:
        reason_codes.append("activation_approval_expired")
    if consumed:
        reason_codes.append("activation_approval_consumed")
    if reusable:
        reason_codes.append("activation_approval_reuse_blocked")
    if self_approval:
        reason_codes.append("activation_self_approval_blocked")
    if separation:
        reason_codes.append("activation_separation_of_duties_satisfied")
    else:
        reason_codes.append("activation_separation_of_duties_failed")
    if security:
        reason_codes.append("activation_security_review_satisfied")
    else:
        reason_codes.append("activation_security_review_failed")
    if mismatches:
        reason_codes.append("activation_binding_mismatch")
    valid = (
        not (expired or consumed or reusable or self_approval or mismatches)
        and separation
        and security
    )
    reason_codes.append("activation_approval_valid" if valid else "activation_approval_invalid")
    reason_codes.append("activation_runtime_disabled")
    return ShadowActivationApprovalValidation(
        valid=valid,
        expired=expired,
        consumed=consumed,
        reusable=reusable,
        self_approval_detected=self_approval,
        separation_of_duties_satisfied=separation,
        security_review_satisfied=security,
        binding_mismatches=tuple(dict.fromkeys(mismatches)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def _principal_is_machine_or_forbidden(principal_id: str) -> bool:
    normalized = principal_id.casefold()
    return (
        principal_id in {PARENT_EVALUATION_ID, AUTHORIZATION_TRANSACTION_ID}
        or normalized.startswith("machine")
        or normalized.startswith("service")
        or normalized.startswith("automation")
        or ":machine" in normalized
    )


def shadow_activation_fingerprint(value: Any) -> str:
    """Fingerprint activation evidence through the shared canonical helper."""

    return canonical_shadow_fingerprint(value)


__all__ = [
    "ACTIVATION_PROGRAM_ID",
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CANDIDATE_ID",
    "DISALLOWED_SHADOW_ACTIVATION_ENVIRONMENTS",
    "FORMAL_CLOSEOUT_TASK",
    "FORBIDDEN_COUNTER_METRICS",
    "FORBIDDEN_COUNTER_TRIGGER_BY_METRIC",
    "FORBIDDEN_SHADOW_ACTIVATION_STATES",
    "FROZEN_MODEL_CONFIG",
    "IMPLEMENTATION_TASK",
    "MAXIMUM_ACTIVATION_WINDOW_SECONDS",
    "MAXIMUM_CONCURRENCY",
    "MAXIMUM_EVIDENCE_BUNDLE_BYTES",
    "MAXIMUM_RETENTION_SECONDS",
    "MAXIMUM_RUNS_PER_ACTIVATION",
    "PARENT_AUTHORIZATION_TRANSACTION_ID",
    "PARENT_CLOSEOUT_TASK",
    "PARENT_EVALUATION_DECISION",
    "PARENT_EVALUATION_ID",
    "PARENT_MAIN_COMMIT",
    "PARENT_SHADOW_IMPLEMENTATION_COMMIT",
    "PROGRAM_ID",
    "SHADOW_ACTIVATION_ADAPTER_TYPES",
    "SHADOW_ACTIVATION_ALLOWED_TRANSITIONS",
    "SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS",
    "SHADOW_ACTIVATION_DECISION_OUTCOMES",
    "SHADOW_ACTIVATION_MONITORING_METRICS",
    "SHADOW_ACTIVATION_REASON_CODES",
    "SHADOW_ACTIVATION_REASON_CODE_REGISTRY_VERSION",
    "SHADOW_ACTIVATION_REASON_CODE_SET",
    "SHADOW_ACTIVATION_STATES",
    "STRICT_MODEL_CONFIG",
    "ShadowActivationAdapterType",
    "ShadowActivationApprovalBinding",
    "ShadowActivationApprovalValidation",
    "ShadowActivationAuditEvent",
    "ShadowActivationBudgetDecision",
    "ShadowActivationCandidate",
    "ShadowActivationCandidateValidation",
    "ShadowActivationCurrentFacts",
    "ShadowActivationDataClassification",
    "ShadowActivationDeactivationDecision",
    "ShadowActivationDeactivationPlan",
    "ShadowActivationDeactivationTrigger",
    "ShadowActivationDecisionOutcome",
    "ShadowActivationDiagnostics",
    "ShadowActivationEnvironment",
    "ShadowActivationEvaluationBundle",
    "ShadowActivationEvidenceBundle",
    "ShadowActivationHealthSnapshot",
    "ShadowActivationIncidentRecord",
    "ShadowActivationMonitoringDecision",
    "ShadowActivationMonitoringMetricName",
    "ShadowActivationMonitoringPlan",
    "ShadowActivationMonitoringThreshold",
    "ShadowActivationOperatorReviewItem",
    "ShadowActivationOutputBoundary",
    "ShadowActivationOutputBoundaryValidation",
    "ShadowActivationProvenanceRecord",
    "ShadowActivationRequest",
    "ShadowActivationResourceBudget",
    "ShadowActivationResourceUsage",
    "ShadowActivationRiskLevel",
    "ShadowActivationState",
    "ShadowActivationStateRecord",
    "ShadowActivationTransitionDecision",
    "ShadowActivationTransitionReason",
    "WORKSTREAM",
    "build_current_facts_from_request",
    "canonical_activation_resource_limits",
    "evaluate_shadow_activation_budget",
    "evaluate_shadow_activation_deactivation",
    "evaluate_shadow_activation_health",
    "fingerprint_activation_model",
    "require_activation_identifier",
    "require_activation_reason_codes",
    "require_fingerprint",
    "require_metric_names",
    "require_sha1",
    "require_utc_datetime",
    "shadow_activation_fingerprint",
    "utc_now",
    "validate_activation_candidate",
    "validate_shadow_activation_approval",
    "validate_shadow_activation_output_boundary",
]
