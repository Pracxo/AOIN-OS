"""Contracts for the controlled self-improvement shadow plane."""

from __future__ import annotations

import math
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.production_auth.canonical import sha256_fingerprint

SHADOW_CONTRACT_SCHEMA_VERSION: Literal["self-improvement-shadow/v1"] = (
    "self-improvement-shadow/v1"
)
SHADOW_MANIFEST_SCHEMA_VERSION: Literal["self-improvement-shadow-manifest/v1"] = (
    "self-improvement-shadow-manifest/v1"
)
SHADOW_REFERENCE_SCHEMA_VERSION: Literal["self-improvement-shadow-reference/v1"] = (
    "self-improvement-shadow-reference/v1"
)
SHADOW_OBSERVATION_SCHEMA_VERSION = "self-improvement-shadow-observation/v1"
SHADOW_PATTERN_SCHEMA_VERSION = "self-improvement-shadow-pattern/v1"
SHADOW_HYPOTHESIS_SCHEMA_VERSION = "self-improvement-shadow-hypothesis/v1"
SHADOW_REGRESSION_PROPOSAL_SCHEMA_VERSION = (
    "self-improvement-shadow-regression-proposal/v1"
)
SHADOW_PROPOSAL_SCHEMA_VERSION = "self-improvement-shadow-proposal/v1"
SHADOW_REVIEW_ITEM_SCHEMA_VERSION = "self-improvement-shadow-review-item/v1"
SHADOW_EVIDENCE_SCHEMA_VERSION = "self-improvement-shadow-evidence/v1"
SHADOW_BUDGET_SCHEMA_VERSION = "self-improvement-shadow-budget/v1"
SHADOW_DIAGNOSTIC_SCHEMA_VERSION = "self-improvement-shadow-diagnostics/v1"
SHADOW_REASON_CODE_REGISTRY_VERSION = "self-improvement-shadow-reasons/v1"

PROGRAM_ID: Literal["AION-SELF-IMPROVEMENT-001"] = "AION-SELF-IMPROVEMENT-001"
ACTIVATION_PHASE_ID: Literal["AION-SELF-IMPROVEMENT-SHADOW-001"] = (
    "AION-SELF-IMPROVEMENT-SHADOW-001"
)
AUTHORIZATION_TRANSACTION_ID: Literal["AION-177-SI-0006"] = "AION-177-SI-0006"
APPROVAL_RECORD_ID = "AION-177-SI-0006"
IMPLEMENTATION_TASK = "AION-178"
AUTHORIZATION_SCOPE = (
    "read-only-shadow-observation-evaluation-pattern-mining-proposal-generation"
)
DEFAULT_RETENTION_SECONDS = 86400
MAXIMUM_RETENTION_SECONDS = 604800
DEFAULT_MAXIMUM_CONCURRENCY = 4

ShadowReferenceKind = Literal["trace", "evaluation", "outcome", "experience", "lesson", "pattern"]
ShadowMetricName = Literal[
    "task_success",
    "evidence_grounding",
    "user_correction_rate",
    "retrieval_precision",
    "plan_success",
    "policy_violation_count",
    "regression_count",
    "latency",
    "compute_cost",
    "rollback_count",
    "improvement_survival",
]
ShadowPatternType = Literal[
    "retrieval_failure",
    "planning_failure",
    "evidence_grounding_failure",
    "policy_block",
    "regression_drift",
    "replay_drift",
    "generic_failure",
]
ShadowChangeType = Literal[
    "retrieval_ranking_candidate",
    "planning_policy_candidate",
    "regression_test_candidate",
    "procedural_skill_candidate",
    "prompt_policy_review",
    "governance_review",
    "generic_review",
]
ShadowReviewState = Literal[
    "shadow_observed",
    "shadow_evaluated",
    "shadow_pattern_detected",
    "shadow_hypothesis_generated",
    "shadow_regression_proposed",
    "shadow_proposal_generated",
    "operator_review_pending",
    "discarded",
    "archived",
]
ShadowRunOutcome = Literal[
    "completed",
    "completed_without_pattern",
    "budget_blocked",
    "input_rejected",
    "reference_unavailable",
    "output_rejected",
    "runtime_disabled",
]
ShadowRiskLevel = Literal["low", "medium", "high", "critical"]
MetricDirection = Literal["increase", "decrease"]

SHADOW_METRIC_NAMES: tuple[ShadowMetricName, ...] = (
    "task_success",
    "evidence_grounding",
    "user_correction_rate",
    "retrieval_precision",
    "plan_success",
    "policy_violation_count",
    "regression_count",
    "latency",
    "compute_cost",
    "rollback_count",
    "improvement_survival",
)
LOWER_IS_BETTER_SHADOW_METRICS: frozenset[ShadowMetricName] = frozenset(
    {
        "user_correction_rate",
        "policy_violation_count",
        "regression_count",
        "latency",
        "compute_cost",
        "rollback_count",
    }
)
HIGHER_IS_BETTER_SHADOW_METRICS: frozenset[ShadowMetricName] = frozenset(
    set(SHADOW_METRIC_NAMES) - set(LOWER_IS_BETTER_SHADOW_METRICS)
)
SHADOW_REFERENCE_KINDS: tuple[ShadowReferenceKind, ...] = (
    "trace",
    "evaluation",
    "outcome",
    "experience",
    "lesson",
    "pattern",
)
SHADOW_PATTERN_TYPES: tuple[ShadowPatternType, ...] = (
    "retrieval_failure",
    "planning_failure",
    "evidence_grounding_failure",
    "policy_block",
    "regression_drift",
    "replay_drift",
    "generic_failure",
)
SHADOW_CHANGE_TYPES: tuple[ShadowChangeType, ...] = (
    "retrieval_ranking_candidate",
    "planning_policy_candidate",
    "regression_test_candidate",
    "procedural_skill_candidate",
    "prompt_policy_review",
    "governance_review",
    "generic_review",
)
ALLOWED_SHADOW_REVIEW_STATES: tuple[ShadowReviewState, ...] = (
    "shadow_observed",
    "shadow_evaluated",
    "shadow_pattern_detected",
    "shadow_hypothesis_generated",
    "shadow_regression_proposed",
    "shadow_proposal_generated",
    "operator_review_pending",
    "discarded",
    "archived",
)
FORBIDDEN_SHADOW_REVIEW_STATES = frozenset(
    {"approved", "pr_created", "merged", "canary", "promoted"}
)
SHADOW_REASON_CODES: tuple[str, ...] = (
    "shadow_run_completed",
    "shadow_run_completed_without_pattern",
    "shadow_manifest_valid",
    "shadow_manifest_rejected",
    "shadow_reference_resolved",
    "shadow_reference_unavailable",
    "shadow_reference_fingerprint_mismatch",
    "shadow_reference_stale",
    "shadow_input_redacted",
    "shadow_evaluation_completed",
    "shadow_pattern_detected",
    "shadow_no_repeated_pattern",
    "shadow_hypothesis_generated",
    "shadow_regression_proposed",
    "shadow_proposal_generated",
    "shadow_operator_review_required",
    "shadow_budget_satisfied",
    "shadow_budget_exceeded",
    "shadow_run_stopped_fail_closed",
    "shadow_output_boundary_satisfied",
    "shadow_output_boundary_rejected",
    "shadow_retention_applied",
    "shadow_deterministic_replay_verified",
    "shadow_runtime_influence_blocked",
    "shadow_active_promotion_blocked",
    "shadow_source_mutation_blocked",
    "shadow_git_mutation_blocked",
    "shadow_pr_creation_blocked",
    "shadow_approval_creation_blocked",
    "shadow_network_access_blocked",
    "shadow_background_execution_blocked",
    "shadow_authorization_scope_observation_only",
    "shadow_mode_runtime_disabled",
)
SHADOW_REASON_CODE_SET = frozenset(SHADOW_REASON_CODES)

STRICT_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EMAIL_RE = re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b")
_PHONE_RE = re.compile(r"(?:\+?\d[\d .()_-]{7,}\d)")
_NETWORK_RE = re.compile(r"(^|[\s])(?:[a-z][a-z0-9+.-]*://|www\.|[A-Za-z0-9-]+\.(?:com|net|org|io|dev)(?:/|\b))")
_COMMAND_RE = re.compile(r"(^|[\s])(?:\./|bash\s+|sh\s+|python\d?\s+|git\s+|curl\s+|rm\s+-)")
_FORBIDDEN_MARKERS = (
    "password",
    "credential",
    "authorization",
    "bearer",
    "access token",
    "refresh token",
    "session token",
    "cookie",
    "client secret",
    "private key",
    "signing key",
    "raw prompt",
    "hidden reasoning",
    "chain of thought",
    "raw user message",
    "provider payload",
    "source patch",
    "raw diff",
    "personal data",
    "email address",
    "phone number",
)


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(UTC)


def normalize_shadow_marker(value: str) -> str:
    """Return normalized text used only for safety marker matching."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.replace("-", " ").replace("_", " ")
    return " ".join(normalized.split())


def require_utc_datetime(value: datetime) -> datetime:
    """Require an aware UTC timestamp without accepting non-zero offsets."""

    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    offset = value.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("timestamp must be UTC")
    return value.astimezone(UTC)


def require_safe_identifier(value: str, field_name: str = "identifier") -> str:
    """Require a bounded ASCII identifier with no path separators."""

    cleaned = value.strip()
    if cleaned != value:
        raise ValueError(f"{field_name} has invalid boundary")
    if "/" in cleaned or "\\" in cleaned:
        raise ValueError(f"{field_name} has invalid boundary")
    if not _IDENTIFIER_RE.fullmatch(cleaned):
        raise ValueError(f"{field_name} has invalid boundary")
    validate_shadow_text(cleaned, field_name=field_name, max_length=128)
    return cleaned


def require_fingerprint(value: str, field_name: str = "fingerprint") -> str:
    """Require a lowercase SHA-256 fingerprint."""

    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 fingerprint")
    return value


def require_finite_number(value: float, field_name: str = "number") -> float:
    """Reject non-finite numeric values."""

    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    return value


def validate_shadow_text(value: str, *, field_name: str = "shadow text", max_length: int) -> str:
    """Validate redacted shadow text without echoing rejected material."""

    cleaned = unicodedata.normalize("NFKC", value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} is too long")
    if any(ord(char) < 32 for char in cleaned):
        raise ValueError(f"{field_name} has invalid control characters")
    reject_hidden_or_secret_text(cleaned, field_name)
    reject_secret_like_payload(cleaned)
    marker_text = normalize_shadow_marker(cleaned)
    if any(marker in marker_text for marker in _FORBIDDEN_MARKERS):
        raise ValueError(f"{field_name} contains prohibited material")
    if _EMAIL_RE.search(cleaned) or _PHONE_RE.search(cleaned):
        raise ValueError(f"{field_name} contains prohibited material")
    if _NETWORK_RE.search(cleaned):
        raise ValueError(f"{field_name} contains prohibited location material")
    if _COMMAND_RE.search(cleaned):
        raise ValueError(f"{field_name} contains prohibited command material")
    return cleaned


def canonical_shadow_fingerprint(value: Any) -> str:
    """Return the canonical SHA-256 fingerprint for shadow evidence."""

    return sha256_fingerprint(value)


def fingerprint_model(model: BaseModel, *, fingerprint_field: str = "fingerprint") -> str:
    """Fingerprint a model while excluding its own fingerprint field."""

    payload = model.model_dump(mode="python")
    payload.pop(fingerprint_field, None)
    return canonical_shadow_fingerprint(payload)


def require_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    """Validate immutable reason-code tuples."""

    if len(value) != len(set(value)):
        raise ValueError("reason codes must be unique")
    for code in value:
        if code not in SHADOW_REASON_CODE_SET:
            raise ValueError("unknown shadow reason code")
    return value


class ShadowReference(BaseModel):
    """Opaque read-only reference to an already-approved redacted source record."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-reference/v1"] = (
        SHADOW_REFERENCE_SCHEMA_VERSION
    )
    reference_kind: ShadowReferenceKind
    reference_id: str = Field(min_length=1, max_length=128)
    reference_fingerprint: str = Field(min_length=64, max_length=64)
    observed_at: datetime
    repeated_count: int = Field(ge=1, le=1000)
    source_version: str = Field(min_length=1, max_length=128)
    redacted: bool = True
    read_only: bool = True

    @field_validator("reference_id", "source_version")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("reference_fingerprint")
    @classmethod
    def reference_fingerprint_is_sha256(cls, value: str) -> str:
        return require_fingerprint(value, "reference_fingerprint")

    @field_validator("observed_at")
    @classmethod
    def observed_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def reference_is_redacted_and_read_only(self) -> ShadowReference:
        if not self.redacted or not self.read_only:
            raise ValueError("shadow references must be redacted and read-only")
        return self


class ShadowRedactedMetric(BaseModel):
    """Redacted numeric metric used for deterministic shadow evaluation."""

    model_config = FROZEN_MODEL_CONFIG

    metric_name: ShadowMetricName
    current_value: float = Field(ge=0.0, le=1_000_000_000.0)
    baseline_value: float = Field(ge=0.0, le=1_000_000_000.0)
    target_value: float = Field(ge=0.0, le=1_000_000_000.0)
    higher_is_better: bool
    weight: float = Field(ge=0.0, le=1.0)
    recorded_at: datetime
    reference_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("current_value", "baseline_value", "target_value", "weight")
    @classmethod
    def values_are_finite(cls, value: float) -> float:
        return require_finite_number(value)

    @field_validator("recorded_at")
    @classmethod
    def recorded_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @field_validator("reference_id")
    @classmethod
    def reference_id_is_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return require_safe_identifier(value, "reference_id")

    @model_validator(mode="after")
    def direction_matches_metric(self) -> ShadowRedactedMetric:
        if self.metric_name in LOWER_IS_BETTER_SHADOW_METRICS and self.higher_is_better:
            raise ValueError("metric direction mismatch")
        if self.metric_name in HIGHER_IS_BETTER_SHADOW_METRICS and not self.higher_is_better:
            raise ValueError("metric direction mismatch")
        return self


class ShadowObservationManifest(BaseModel):
    """Explicit operator-supplied manifest for one read-only shadow run."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["self-improvement-shadow-manifest/v1"] = (
        SHADOW_MANIFEST_SCHEMA_VERSION
    )
    manifest_id: str = Field(min_length=1, max_length=128)
    program_id: Literal["AION-SELF-IMPROVEMENT-001"] = PROGRAM_ID
    activation_phase_id: Literal["AION-SELF-IMPROVEMENT-SHADOW-001"] = ACTIVATION_PHASE_ID
    authorization_transaction_id: Literal["AION-177-SI-0006"] = AUTHORIZATION_TRANSACTION_ID
    references: tuple[ShadowReference, ...] = Field(min_length=1, max_length=1000)
    redacted_metrics: tuple[ShadowRedactedMetric, ...] = Field(min_length=1, max_length=1000)
    operator_scope_labels: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    requested_review_outputs: tuple[str, ...] = Field(default_factory=tuple, max_length=10)
    maximum_concurrency: int = Field(default=DEFAULT_MAXIMUM_CONCURRENCY, ge=1, le=4)
    retention_seconds: int = Field(
        default=DEFAULT_RETENTION_SECONDS,
        ge=0,
        le=MAXIMUM_RETENTION_SECONDS,
    )
    benchmark_cost_units: int = Field(default=0, ge=0, le=50)
    input_classification: Literal["synthetic", "redacted"]
    operator_invoked: bool = True
    shadow_only: bool = True
    read_only: bool = True
    redacted: bool = True
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    approval_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator("manifest_id")
    @classmethod
    def manifest_id_is_safe(cls, value: str) -> str:
        return require_safe_identifier(value, "manifest_id")

    @field_validator("operator_scope_labels", "requested_review_outputs")
    @classmethod
    def tuple_values_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(validate_shadow_text(item, max_length=128) for item in value)
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("shadow tuple values must be unique")
        if any(item in FORBIDDEN_SHADOW_REVIEW_STATES for item in cleaned):
            raise ValueError("forbidden shadow review output")
        return cleaned

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def manifest_flags_and_duplicates_are_valid(self) -> ShadowObservationManifest:
        if not all((self.operator_invoked, self.shadow_only, self.read_only, self.redacted)):
            raise ValueError("shadow manifest must be operator-invoked, redacted, and read-only")
        if any(
            (
                self.source_modified,
                self.git_mutated,
                self.pull_request_created,
                self.approval_created,
                self.runtime_effect,
            )
        ):
            raise ValueError("shadow manifest cannot carry side effects")
        reference_keys = {(item.reference_kind, item.reference_id) for item in self.references}
        if len(reference_keys) != len(self.references):
            raise ValueError("duplicate shadow reference")
        metric_keys = {
            (metric.reference_id or "*", metric.metric_name)
            for metric in self.redacted_metrics
        }
        if len(metric_keys) != len(self.redacted_metrics):
            raise ValueError("duplicate shadow metric")
        return self


__all__ = [
    "ACTIVATION_PHASE_ID",
    "ALLOWED_SHADOW_REVIEW_STATES",
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "DEFAULT_MAXIMUM_CONCURRENCY",
    "DEFAULT_RETENTION_SECONDS",
    "FORBIDDEN_SHADOW_REVIEW_STATES",
    "FROZEN_MODEL_CONFIG",
    "HIGHER_IS_BETTER_SHADOW_METRICS",
    "IMPLEMENTATION_TASK",
    "LOWER_IS_BETTER_SHADOW_METRICS",
    "MAXIMUM_RETENTION_SECONDS",
    "MetricDirection",
    "PROGRAM_ID",
    "SHADOW_BUDGET_SCHEMA_VERSION",
    "SHADOW_CHANGE_TYPES",
    "SHADOW_CONTRACT_SCHEMA_VERSION",
    "SHADOW_DIAGNOSTIC_SCHEMA_VERSION",
    "SHADOW_EVIDENCE_SCHEMA_VERSION",
    "SHADOW_HYPOTHESIS_SCHEMA_VERSION",
    "SHADOW_MANIFEST_SCHEMA_VERSION",
    "SHADOW_METRIC_NAMES",
    "SHADOW_OBSERVATION_SCHEMA_VERSION",
    "SHADOW_PATTERN_SCHEMA_VERSION",
    "SHADOW_PROPOSAL_SCHEMA_VERSION",
    "SHADOW_REASON_CODES",
    "SHADOW_REASON_CODE_REGISTRY_VERSION",
    "SHADOW_REFERENCE_KINDS",
    "SHADOW_REFERENCE_SCHEMA_VERSION",
    "SHADOW_REGRESSION_PROPOSAL_SCHEMA_VERSION",
    "SHADOW_REVIEW_ITEM_SCHEMA_VERSION",
    "STRICT_MODEL_CONFIG",
    "ShadowChangeType",
    "ShadowMetricName",
    "ShadowObservationManifest",
    "ShadowPatternType",
    "ShadowRedactedMetric",
    "ShadowReference",
    "ShadowReferenceKind",
    "ShadowReviewState",
    "ShadowRiskLevel",
    "ShadowRunOutcome",
    "canonical_shadow_fingerprint",
    "fingerprint_model",
    "normalize_shadow_marker",
    "require_finite_number",
    "require_fingerprint",
    "require_reason_codes",
    "require_safe_identifier",
    "require_utc_datetime",
    "utc_now",
    "validate_shadow_text",
]
