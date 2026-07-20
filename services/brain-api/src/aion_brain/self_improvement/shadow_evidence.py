"""Immutable evidence bundles for controlled shadow-mode runs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.self_improvement_shadow import (
    ACTIVATION_PHASE_ID,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FROZEN_MODEL_CONFIG,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    SHADOW_EVIDENCE_SCHEMA_VERSION,
    ShadowRunOutcome,
    fingerprint_model,
    require_fingerprint,
    require_reason_codes,
    require_safe_identifier,
    require_utc_datetime,
    validate_shadow_text,
)
from aion_brain.self_improvement.shadow_budget import (
    ShadowBudgetDecision,
    ShadowResourceBudget,
    ShadowResourceUsage,
)


class ShadowAuditEvent(BaseModel):
    """Redacted audit event for an operator-invoked shadow run."""

    model_config = FROZEN_MODEL_CONFIG

    audit_event_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=128)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    reference_count: int = Field(ge=0)
    created_at: datetime
    redacted: bool = True
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("audit_event_id", "run_id", "event_type")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def event_is_redacted_and_inert(self) -> ShadowAuditEvent:
        if not self.redacted or self.runtime_effect:
            raise ValueError("shadow audit events must be redacted and inert")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowProvenanceRecord(BaseModel):
    """Redacted provenance for source references and generated shadow records."""

    model_config = FROZEN_MODEL_CONFIG

    provenance_record_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    manifest_fingerprint: str = Field(min_length=64, max_length=64)
    reference_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    observation_ids: tuple[str, ...] = Field(default_factory=tuple)
    pattern_ids: tuple[str, ...] = Field(default_factory=tuple)
    hypothesis_ids: tuple[str, ...] = Field(default_factory=tuple)
    proposal_ids: tuple[str, ...] = Field(default_factory=tuple)
    review_item_ids: tuple[str, ...] = Field(default_factory=tuple)
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    redacted: bool = True
    runtime_effect: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator("provenance_record_id", "run_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator(
        "observation_ids",
        "pattern_ids",
        "hypothesis_ids",
        "proposal_ids",
        "review_item_ids",
    )
    @classmethod
    def tuple_identifiers_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_safe_identifier(item) for item in value)

    @field_validator("manifest_fingerprint")
    @classmethod
    def manifest_fingerprint_is_sha256(cls, value: str) -> str:
        return require_fingerprint(value, "manifest_fingerprint")

    @field_validator("reference_fingerprints")
    @classmethod
    def reference_fingerprints_are_sha256(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_fingerprint(item) for item in value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def provenance_is_redacted_and_inert(self) -> ShadowProvenanceRecord:
        if self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("shadow provenance authorization mismatch")
        if not self.redacted or self.runtime_effect:
            raise ValueError("shadow provenance must be redacted and inert")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowRunDiagnostics(BaseModel):
    """Run diagnostics proving the shadow plane remains disabled at runtime."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = "self-improvement-shadow-diagnostics/v1"
    run_id: str = Field(min_length=1, max_length=128)
    shadow_mode_implemented: bool = True
    shadow_mode_implementation_state: str = "implemented_operator_invoked_disabled"
    shadow_mode_runtime_enabled: bool = False
    operator_invoked: bool = True
    background_loop: bool = False
    production_event_subscription: bool = False
    network_calls: int = 0
    git_operations: int = 0
    source_mutations: int = 0
    real_pull_requests: int = 0
    runtime_promotions: int = 0
    reference_count: int = Field(ge=0)
    observation_count: int = Field(ge=0)
    evaluation_count: int = Field(ge=0)
    pattern_count: int = Field(ge=0)
    hypothesis_count: int = Field(ge=0)
    regression_proposal_count: int = Field(ge=0)
    shadow_proposal_count: int = Field(ge=0)
    operator_review_item_count: int = Field(ge=0)
    wall_clock_seconds: float = Field(ge=0.0)
    benchmark_cost_units: int = Field(ge=0, le=50)
    output_bytes: int = Field(ge=0)
    output_files: int = Field(ge=0)
    implementation_authorization_created: bool = False
    approval_created: bool = False
    runtime_effect: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator("run_id")
    @classmethod
    def run_id_is_safe(cls, value: str) -> str:
        return require_safe_identifier(value, "run_id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def diagnostics_are_disabled(self) -> ShadowRunDiagnostics:
        if not self.shadow_mode_implemented:
            raise ValueError("shadow implementation evidence must be true")
        if self.shadow_mode_implementation_state != "implemented_operator_invoked_disabled":
            raise ValueError("shadow implementation state mismatch")
        if not self.operator_invoked:
            raise ValueError("shadow run must be operator-invoked")
        if any(
            (
                self.shadow_mode_runtime_enabled,
                self.background_loop,
                self.production_event_subscription,
                self.network_calls,
                self.git_operations,
                self.source_mutations,
                self.real_pull_requests,
                self.runtime_promotions,
                self.implementation_authorization_created,
                self.approval_created,
                self.runtime_effect,
            )
        ):
            raise ValueError("shadow diagnostics must remain runtime-disabled")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowBudgetFailureRecord(BaseModel):
    """Redacted record emitted when a run is stopped by budget enforcement."""

    model_config = FROZEN_MODEL_CONFIG

    budget_failure_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    violations: tuple[str, ...]
    reason_codes: tuple[str, ...]
    created_at: datetime
    redacted: bool = True
    implementation_authorization_created: bool = False
    approval_created: bool = False
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("budget_failure_id", "run_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("violations")
    @classmethod
    def violations_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_safe_identifier(item) for item in value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def failure_record_is_inert(self) -> ShadowBudgetFailureRecord:
        if not self.redacted or self.implementation_authorization_created or self.approval_created:
            raise ValueError("shadow budget failure must be redacted and inert")
        if self.runtime_effect:
            raise ValueError("shadow budget failure cannot create runtime effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowEvidenceBundle(BaseModel):
    """Immutable evidence bundle returned by one explicit shadow run."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_EVIDENCE_SCHEMA_VERSION
    run_id: str = Field(min_length=1, max_length=128)
    program_id: str = PROGRAM_ID
    activation_phase_id: str = ACTIVATION_PHASE_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    manifest_id: str = Field(min_length=1, max_length=128)
    manifest_fingerprint: str = Field(min_length=64, max_length=64)
    outcome: ShadowRunOutcome
    observations: tuple[Any, ...] = Field(default_factory=tuple)
    evaluation_summary: Any | None = None
    failure_patterns: tuple[Any, ...] = Field(default_factory=tuple)
    hypotheses: tuple[Any, ...] = Field(default_factory=tuple)
    regression_test_proposals: tuple[Any, ...] = Field(default_factory=tuple)
    shadow_proposals: tuple[Any, ...] = Field(default_factory=tuple)
    operator_review_items: tuple[Any, ...] = Field(default_factory=tuple)
    audit_events: tuple[ShadowAuditEvent, ...] = Field(default_factory=tuple)
    provenance: ShadowProvenanceRecord | None = None
    diagnostics: ShadowRunDiagnostics
    resource_budget: ShadowResourceBudget
    resource_usage: ShadowResourceUsage
    budget_decision: ShadowBudgetDecision
    budget_failure: ShadowBudgetFailureRecord | None = None
    reason_codes: tuple[str, ...]
    shadow_mode: bool = True
    shadow_only: bool = True
    operator_review_required: bool = True
    shadow_mode_implemented: bool = True
    shadow_mode_runtime_enabled: bool = False
    implementation_authorization_created: bool = False
    approval_created: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    merged: bool = False
    runtime_effect: bool = False
    active_learning_promoted: bool = False
    redacted: bool = True
    read_only: bool = True
    created_at: datetime
    expires_at: datetime
    fingerprint: str = ""

    @field_validator("run_id", "manifest_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("manifest_fingerprint")
    @classmethod
    def manifest_fingerprint_is_sha256(cls, value: str) -> str:
        return require_fingerprint(value, "manifest_fingerprint")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_reason_codes(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def bundle_is_shadow_only_and_inert(self) -> ShadowEvidenceBundle:
        if self.program_id != PROGRAM_ID or self.activation_phase_id != ACTIVATION_PHASE_ID:
            raise ValueError("shadow bundle lineage mismatch")
        if self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("shadow bundle authorization mismatch")
        if self.implementation_task != IMPLEMENTATION_TASK:
            raise ValueError("shadow bundle implementation task mismatch")
        if self.authorization_scope != AUTHORIZATION_SCOPE:
            raise ValueError("shadow bundle scope mismatch")
        if not all(
            (
                self.shadow_mode,
                self.shadow_only,
                self.operator_review_required,
                self.shadow_mode_implemented,
                self.redacted,
                self.read_only,
            )
        ):
            raise ValueError("shadow bundle must be redacted, read-only, and review-bound")
        if any(
            (
                self.shadow_mode_runtime_enabled,
                self.implementation_authorization_created,
                self.approval_created,
                self.source_modified,
                self.git_mutated,
                self.pull_request_created,
                self.merged,
                self.runtime_effect,
                self.active_learning_promoted,
            )
        ):
            raise ValueError("shadow bundle cannot create side effects")
        if self.expires_at < self.created_at:
            raise ValueError("shadow bundle expiry must not precede creation")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowRunResult(BaseModel):
    """Result returned by the explicit operator runner."""

    model_config = FROZEN_MODEL_CONFIG

    bundle: ShadowEvidenceBundle
    output_files: tuple[str, ...] = Field(default_factory=tuple)
    output_bytes: int = Field(ge=0)
    written: bool = False
    reason_codes: tuple[str, ...]
    fingerprint: str = ""

    @field_validator("output_files")
    @classmethod
    def output_files_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_shadow_text(item, max_length=128) for item in value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_reason_codes(value)

    @model_validator(mode="after")
    def set_fingerprint(self) -> ShadowRunResult:
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


__all__ = [
    "ShadowAuditEvent",
    "ShadowBudgetFailureRecord",
    "ShadowEvidenceBundle",
    "ShadowProvenanceRecord",
    "ShadowRunDiagnostics",
    "ShadowRunResult",
]
