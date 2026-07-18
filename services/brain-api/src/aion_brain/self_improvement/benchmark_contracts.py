"""Immutable benchmark contracts for governed self-improvement evaluation."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import freeze_evidence_payload

SELF_IMPROVEMENT_EVALUATION_SCHEMA_VERSION = "self-improvement-evaluation-plane/v1"
EVALUATION_AUTHORIZATION_TRANSACTION_ID = "AION-167-SI-0002"
EVALUATION_IMPLEMENTATION_TASK = "AION-168"
EVALUATION_AUTHORIZATION_SCOPE = "immutable-self-improvement-evaluation-plane"

BenchmarkMetricName = Literal[
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

REQUIRED_BENCHMARK_METRICS: tuple[BenchmarkMetricName, ...] = (
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

LOWER_IS_BETTER_METRICS: frozenset[BenchmarkMetricName] = frozenset(
    {
        "user_correction_rate",
        "policy_violation_count",
        "regression_count",
        "latency",
        "compute_cost",
        "rollback_count",
    }
)
HIGHER_IS_BETTER_METRICS: frozenset[BenchmarkMetricName] = frozenset(
    set(REQUIRED_BENCHMARK_METRICS) - set(LOWER_IS_BETTER_METRICS)
)

REQUIRED_HARD_GATE_FIELDS: tuple[str, ...] = (
    "all_required_tests_pass",
    "all_security_checks_pass",
    "all_policy_checks_pass",
    "protected_boundaries_pass",
    "holdout_score_meets_threshold",
    "no_critical_regression",
    "rollback_plan_present",
)

PROTECTED_HOLDOUT_PREFIX = "docs/self-improvement/holdout/"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_json(payload: Any) -> str:
    """Hash a JSON-compatible payload using canonical serialization."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _frozen_metadata(value: Any) -> dict[str, Any]:
    if value is None:
        value = {}
    frozen = freeze_evidence_payload(value)
    if not isinstance(frozen, dict):
        raise ValueError("metadata must be a mapping")
    return frozen


def _require_sha256(value: str, field_name: str) -> str:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a 64-character lowercase SHA-256 hash")
    return value


class BenchmarkMetric(BaseModel):
    """One deterministic benchmark metric value or threshold definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_name: BenchmarkMetricName
    value: float = Field(ge=0.0)
    threshold: float = Field(ge=0.0)
    higher_is_better: bool
    weight: float = Field(default=1.0, ge=0.0)
    unit: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def direction_must_match_metric(self) -> BenchmarkMetric:
        if self.metric_name in LOWER_IS_BETTER_METRICS and self.higher_is_better:
            raise ValueError("lower-is-better metric cannot be marked higher_is_better")
        if self.metric_name in HIGHER_IS_BETTER_METRICS and not self.higher_is_better:
            raise ValueError("higher-is-better metric cannot be marked lower_is_better")
        return self

    @field_validator("unit")
    @classmethod
    def unit_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "benchmark metric unit")
        return cleaned

    @field_validator("evidence_refs")
    @classmethod
    def evidence_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "benchmark metric evidence reference")
        return value


class BenchmarkSafetyGate(BaseModel):
    """Hard safety gate that must pass before a change can be eligible."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    all_required_tests_pass: bool
    all_security_checks_pass: bool
    all_policy_checks_pass: bool
    protected_boundaries_pass: bool
    holdout_score_meets_threshold: bool
    no_critical_regression: bool
    rollback_plan_present: bool
    change_eligible: bool
    critical_regression_count: int = Field(default=0, ge=0)
    rollback_plan_ref: str | None = None
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def change_eligibility_must_equal_required_formula(self) -> BenchmarkSafetyGate:
        expected = (
            self.all_required_tests_pass
            and self.all_security_checks_pass
            and self.all_policy_checks_pass
            and self.protected_boundaries_pass
            and self.holdout_score_meets_threshold
            and self.no_critical_regression
            and self.rollback_plan_present
        )
        if self.change_eligible != expected:
            raise ValueError("change_eligible must match the hard safety-gate formula")
        if self.critical_regression_count > 0 and self.no_critical_regression:
            raise ValueError("critical regressions must fail the no_critical_regression gate")
        return self

    @field_validator("rollback_plan_ref")
    @classmethod
    def rollback_ref_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        reject_hidden_or_secret_text(value, "benchmark rollback plan reference")
        return value.strip()

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "benchmark safety reason code")
        return value


class BenchmarkCaseReference(BaseModel):
    """Opaque reference to a benchmark case without exposing holdout content."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    opaque_case_id: str = Field(min_length=1)
    case_family: str = Field(min_length=1)
    hidden: bool
    holdout_path: str = Field(min_length=1)
    content_fingerprint: str
    metadata: dict[str, Any] = Field(default_factory=dict, validate_default=True)

    @field_validator("opaque_case_id", "case_family", "holdout_path")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip().replace("\\", "/")
        reject_hidden_or_secret_text(cleaned, "benchmark case reference")
        return cleaned

    @field_validator("content_fingerprint")
    @classmethod
    def content_fingerprint_must_be_sha256(cls, value: str) -> str:
        return _require_sha256(value, "content_fingerprint")

    @field_validator("metadata", mode="before")
    @classmethod
    def metadata_must_be_frozen(cls, value: Any) -> dict[str, Any]:
        return _frozen_metadata(value)

    @model_validator(mode="after")
    def hidden_holdout_path_must_be_protected(self) -> BenchmarkCaseReference:
        if self.hidden and not self.holdout_path.startswith(PROTECTED_HOLDOUT_PREFIX):
            raise ValueError("hidden holdout path must live under the protected holdout boundary")
        return self


class BenchmarkManifest(BaseModel):
    """Immutable benchmark manifest with a canonical fingerprint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SELF_IMPROVEMENT_EVALUATION_SCHEMA_VERSION
    manifest_id: str = Field(min_length=1)
    benchmark_version: str = Field(min_length=1)
    case_references: tuple[BenchmarkCaseReference, ...] = Field(min_length=1)
    metric_definitions: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    required_metric_names: tuple[BenchmarkMetricName, ...] = REQUIRED_BENCHMARK_METRICS
    holdout_content_separate_from_generated_patches: bool = True
    patch_generator_receives_opaque_case_ids_only: bool = True
    threshold_changes_require_audit: bool = True
    candidate_code_can_update_baseline: bool = False
    candidate_code_can_modify_holdout: bool = False
    hidden_holdout_path_protected: bool = True
    manifest_fingerprint: str = ""
    created_at: datetime

    @field_validator("manifest_id", "benchmark_version")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "benchmark manifest text")
        return cleaned

    @model_validator(mode="after")
    def manifest_controls_must_fail_closed(self) -> BenchmarkManifest:
        if set(self.required_metric_names) != set(REQUIRED_BENCHMARK_METRICS):
            raise ValueError("benchmark manifest must require the full AION-168 metric set")
        _require_required_metrics(self.metric_definitions)
        opaque_ids = [case.opaque_case_id for case in self.case_references]
        if len(opaque_ids) != len(set(opaque_ids)):
            raise ValueError("benchmark case opaque IDs must be unique")
        if not self.holdout_content_separate_from_generated_patches:
            raise ValueError("benchmark content must remain separate from generated patches")
        if not self.patch_generator_receives_opaque_case_ids_only:
            raise ValueError("patch generators may receive only opaque benchmark case IDs")
        if not self.threshold_changes_require_audit:
            raise ValueError("benchmark threshold changes must be audited")
        if self.candidate_code_can_update_baseline:
            raise ValueError("candidate code cannot update its own baseline")
        if self.candidate_code_can_modify_holdout:
            raise ValueError("candidate code cannot modify the holdout in the same proposal")
        if not self.hidden_holdout_path_protected:
            raise ValueError("hidden holdout path must remain protected")

        expected = manifest_fingerprint(self)
        if self.manifest_fingerprint and self.manifest_fingerprint != expected:
            raise ValueError("manifest_fingerprint does not match manifest content")
        object.__setattr__(self, "manifest_fingerprint", expected)
        return self


class BenchmarkBaseline(BaseModel):
    """Read-only baseline results for a benchmark manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_id: str = Field(min_length=1)
    manifest_id: str = Field(min_length=1)
    manifest_fingerprint: str
    metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    evaluator_refs: tuple[str, ...] = Field(default_factory=tuple)
    learning_synthesis_refs: tuple[str, ...] = Field(default_factory=tuple)
    candidate_updates_allowed: bool = False
    created_at: datetime

    @field_validator("manifest_fingerprint")
    @classmethod
    def manifest_fingerprint_must_be_sha256(cls, value: str) -> str:
        return _require_sha256(value, "manifest_fingerprint")

    @model_validator(mode="after")
    def baseline_must_be_read_only_and_complete(self) -> BenchmarkBaseline:
        _require_required_metrics(self.metrics)
        if self.candidate_updates_allowed:
            raise ValueError("candidate code cannot update its own baseline")
        return self


class BenchmarkCandidateResult(BaseModel):
    """Candidate results captured without giving candidate code mutation rights."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_result_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    manifest_id: str = Field(min_length=1)
    manifest_fingerprint: str
    baseline_id: str = Field(min_length=1)
    metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    safety_gate: BenchmarkSafetyGate
    read_only_evaluator_refs: tuple[str, ...] = Field(default_factory=tuple)
    read_only_learning_synthesis_refs: tuple[str, ...] = Field(default_factory=tuple)
    candidate_modified_baseline: bool = False
    candidate_modified_holdout: bool = False
    created_at: datetime

    @field_validator("manifest_fingerprint")
    @classmethod
    def manifest_fingerprint_must_be_sha256(cls, value: str) -> str:
        return _require_sha256(value, "manifest_fingerprint")

    @model_validator(mode="after")
    def candidate_result_must_preserve_boundaries(self) -> BenchmarkCandidateResult:
        _require_required_metrics(self.metrics)
        if self.candidate_modified_baseline:
            raise ValueError("candidate code cannot update its own baseline")
        if self.candidate_modified_holdout:
            raise ValueError("candidate code cannot modify the holdout in the same proposal")
        return self


class BenchmarkMetricDelta(BaseModel):
    """Deterministic candidate-vs-baseline delta for one metric."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_name: BenchmarkMetricName
    baseline_value: float = Field(ge=0.0)
    candidate_value: float = Field(ge=0.0)
    delta: float
    improved: bool

    @model_validator(mode="after")
    def delta_must_match_values(self) -> BenchmarkMetricDelta:
        expected = self.candidate_value - self.baseline_value
        if abs(self.delta - expected) > 1e-12:
            raise ValueError("metric delta must equal candidate_value - baseline_value")
        if self.metric_name in LOWER_IS_BETTER_METRICS and self.improved != (self.delta < 0.0):
            raise ValueError("lower-is-better improvement direction mismatch")
        if self.metric_name in HIGHER_IS_BETTER_METRICS and self.improved != (self.delta > 0.0):
            raise ValueError("higher-is-better improvement direction mismatch")
        return self


class BenchmarkComparison(BaseModel):
    """Deterministic comparison with a documented non-random interval method."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    comparison_id: str = Field(min_length=1)
    baseline_id: str = Field(min_length=1)
    candidate_result_id: str = Field(min_length=1)
    method: str = "deterministic_paired_delta_interval"
    metric_deltas: tuple[BenchmarkMetricDelta, ...] = Field(min_length=1)
    baseline_quality_score: float = Field(ge=0.0)
    candidate_quality_score: float = Field(ge=0.0)
    quality_score_delta: float
    confidence_interval_low: float
    confidence_interval_high: float
    safety_passed: bool
    change_eligible: bool
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime

    @model_validator(mode="after")
    def quality_cannot_offset_safety_failure(self) -> BenchmarkComparison:
        expected_delta = self.candidate_quality_score - self.baseline_quality_score
        if abs(self.quality_score_delta - expected_delta) > 1e-12:
            raise ValueError("quality_score_delta must match candidate minus baseline")
        if self.change_eligible and not self.safety_passed:
            raise ValueError("quality gains must never offset safety failures")
        return self


class BenchmarkDriftReport(BaseModel):
    """Benchmark drift report for manifest and threshold changes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    drift_report_id: str = Field(min_length=1)
    manifest_id: str = Field(min_length=1)
    baseline_manifest_fingerprint: str
    current_manifest_fingerprint: str
    drift_detected: bool
    threshold_changes: tuple[str, ...] = Field(default_factory=tuple)
    threshold_changes_audited: bool
    created_at: datetime

    @field_validator("baseline_manifest_fingerprint", "current_manifest_fingerprint")
    @classmethod
    def fingerprints_must_be_sha256(cls, value: str) -> str:
        return _require_sha256(value, "manifest fingerprint")

    @model_validator(mode="after")
    def threshold_changes_must_be_audited(self) -> BenchmarkDriftReport:
        expected_drift = self.baseline_manifest_fingerprint != self.current_manifest_fingerprint
        if self.drift_detected != expected_drift:
            raise ValueError("drift_detected must reflect manifest fingerprint changes")
        if self.threshold_changes and not self.threshold_changes_audited:
            raise ValueError("benchmark threshold changes must be audited")
        return self


class BenchmarkEvaluationBundle(BaseModel):
    """Complete immutable evidence bundle for a candidate benchmark evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_id: str = Field(min_length=1)
    manifest: BenchmarkManifest
    baseline: BenchmarkBaseline
    candidate_result: BenchmarkCandidateResult
    comparison: BenchmarkComparison
    drift_report: BenchmarkDriftReport
    provenance_refs: tuple[str, ...] = Field(default_factory=tuple)
    change_eligible: bool
    created_at: datetime

    @model_validator(mode="after")
    def bundle_must_be_consistent_and_fail_closed(self) -> BenchmarkEvaluationBundle:
        if self.baseline.manifest_id != self.manifest.manifest_id:
            raise ValueError("baseline manifest_id must match manifest")
        if self.candidate_result.manifest_id != self.manifest.manifest_id:
            raise ValueError("candidate manifest_id must match manifest")
        if self.baseline.manifest_fingerprint != self.manifest.manifest_fingerprint:
            raise ValueError("baseline manifest fingerprint must match manifest")
        if self.candidate_result.manifest_fingerprint != self.manifest.manifest_fingerprint:
            raise ValueError("candidate manifest fingerprint must match manifest")
        if self.candidate_result.baseline_id != self.baseline.baseline_id:
            raise ValueError("candidate baseline_id must match baseline")
        if self.comparison.baseline_id != self.baseline.baseline_id:
            raise ValueError("comparison baseline_id must match baseline")
        if self.comparison.candidate_result_id != self.candidate_result.candidate_result_id:
            raise ValueError("comparison candidate_result_id must match candidate result")
        if self.drift_report.manifest_id != self.manifest.manifest_id:
            raise ValueError("drift report manifest_id must match manifest")
        if self.drift_report.current_manifest_fingerprint != self.manifest.manifest_fingerprint:
            raise ValueError("drift report fingerprint must match manifest")

        expected = (
            self.candidate_result.safety_gate.change_eligible
            and self.comparison.safety_passed
            and self.comparison.change_eligible
            and not self.drift_report.drift_detected
        )
        if self.change_eligible != expected:
            raise ValueError("bundle change_eligible must reflect safety, comparison, and drift")
        if self.change_eligible and self.comparison.quality_score_delta < 0.0:
            raise ValueError("eligible changes cannot have negative quality score delta")
        return self


def manifest_fingerprint(manifest: BenchmarkManifest) -> str:
    """Return the canonical fingerprint of a benchmark manifest."""

    payload = manifest.model_dump(mode="json")
    payload["manifest_fingerprint"] = ""
    return sha256_json(payload)


def _require_required_metrics(metrics: tuple[BenchmarkMetric, ...]) -> None:
    observed = [metric.metric_name for metric in metrics]
    if len(observed) != len(set(observed)):
        raise ValueError("benchmark metrics must be unique by metric_name")
    if set(observed) != set(REQUIRED_BENCHMARK_METRICS):
        raise ValueError("benchmark metrics must include the full AION-168 required metric set")


__all__ = [
    "EVALUATION_AUTHORIZATION_SCOPE",
    "EVALUATION_AUTHORIZATION_TRANSACTION_ID",
    "EVALUATION_IMPLEMENTATION_TASK",
    "HIGHER_IS_BETTER_METRICS",
    "LOWER_IS_BETTER_METRICS",
    "PROTECTED_HOLDOUT_PREFIX",
    "REQUIRED_BENCHMARK_METRICS",
    "REQUIRED_HARD_GATE_FIELDS",
    "SELF_IMPROVEMENT_EVALUATION_SCHEMA_VERSION",
    "BenchmarkBaseline",
    "BenchmarkCandidateResult",
    "BenchmarkCaseReference",
    "BenchmarkComparison",
    "BenchmarkDriftReport",
    "BenchmarkEvaluationBundle",
    "BenchmarkManifest",
    "BenchmarkMetric",
    "BenchmarkMetricDelta",
    "BenchmarkMetricName",
    "BenchmarkSafetyGate",
    "manifest_fingerprint",
    "sha256_json",
]
