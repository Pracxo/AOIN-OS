"""Governed self-improvement contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal, NoReturn

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

SELF_IMPROVEMENT_SCHEMA_VERSION = "self-improvement-governance-plane/v1"
AUTHORIZATION_TRANSACTION_ID = "AION-165-SI-0001"
IMPLEMENTATION_TASK = "AION-166"
AUTHORIZATION_SCOPE = "governed-self-improvement-control-plane"
PROGRAM_ID = "AION-SELF-IMPROVEMENT-001"

ImprovementLifecycleValue = Literal[
    "observed",
    "hypothesized",
    "test_created",
    "experiment_ready",
    "patch_created",
    "sandbox_running",
    "sandbox_passed",
    "sandbox_failed",
    "approval_pending",
    "approved",
    "rejected",
    "pr_created",
    "merged",
    "canary",
    "promoted",
    "rolled_back",
    "archived",
]
ImprovementRiskLevel = Literal["low", "medium", "high", "critical"]
ImprovementDecisionStatus = Literal["blocked", "approval_pending", "approved", "rejected"]
ImprovementApprovalStatus = Literal["pending", "approved", "rejected", "invalidated"]
ImprovementAuditEventType = Literal[
    "proposal_observed",
    "risk_assessed",
    "budget_evaluated",
    "approval_bound",
    "governance_decided",
    "evidence_recorded",
]

LIFECYCLE_STATES: tuple[ImprovementLifecycleValue, ...] = (
    "observed",
    "hypothesized",
    "test_created",
    "experiment_ready",
    "patch_created",
    "sandbox_running",
    "sandbox_passed",
    "sandbox_failed",
    "approval_pending",
    "approved",
    "rejected",
    "pr_created",
    "merged",
    "canary",
    "promoted",
    "rolled_back",
    "archived",
)
RISK_LEVELS: tuple[ImprovementRiskLevel, ...] = ("low", "medium", "high", "critical")

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class _FrozenDict(dict[str, Any]):
    """Immutable dict used for governance evidence payloads."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("self-improvement evidence is immutable")

    def __setitem__(self, key: str, value: Any) -> NoReturn:
        self._blocked(key, value)

    def __delitem__(self, key: str) -> NoReturn:
        self._blocked(key)

    def clear(self) -> NoReturn:
        self._blocked()

    def pop(self, key: str, default: Any = None) -> NoReturn:  # noqa: ARG002
        self._blocked(key, default)

    def popitem(self) -> NoReturn:
        self._blocked()

    def setdefault(self, key: str, default: Any = None) -> NoReturn:
        self._blocked(key, default)

    def update(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._blocked(*args, **kwargs)


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(UTC)


def freeze_evidence_payload(value: Any) -> Any:
    """Return an immutable, secret-free copy of a governance evidence payload."""

    reject_secret_like_payload(value)
    if isinstance(value, dict):
        return _FrozenDict(
            {str(key): freeze_evidence_payload(nested) for key, nested in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(freeze_evidence_payload(item) for item in value)
    return value


def _frozen_evidence_mapping(value: dict[str, Any]) -> dict[str, Any]:
    frozen = freeze_evidence_payload(value)
    if not isinstance(frozen, dict):
        raise ValueError("evidence must be a mapping")
    return frozen


class ImprovementProposalRef(BaseModel):
    """Reference to a proposed self-improvement change without patch material."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SELF_IMPROVEMENT_SCHEMA_VERSION
    proposal_id: str = Field(min_length=1)
    author_actor_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: tuple[str, ...] = Field(min_length=1)
    risk_level: ImprovementRiskLevel
    touches_protected_core: bool
    protected_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be empty")
        reject_hidden_or_secret_text(cleaned, "self-improvement proposal text")
        return cleaned

    @field_validator("owner_scope", "protected_paths", "evidence_refs")
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement proposal list")
        return cleaned

    @model_validator(mode="after")
    def protected_core_paths_must_match_flag(self) -> ImprovementProposalRef:
        if self.protected_paths and not self.touches_protected_core:
            raise ValueError("protected_paths require touches_protected_core=true")
        return self


class ImprovementLifecycleState(BaseModel):
    """Lifecycle state snapshot for a governed self-improvement proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lifecycle_state_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    state: ImprovementLifecycleValue
    previous_state: ImprovementLifecycleValue | None = None
    transition_reason: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime

    @field_validator("transition_reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "self-improvement lifecycle reason")
        return value.strip()


class ImprovementRiskAssessment(BaseModel):
    """Risk assessment for a proposed self-improvement change."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    risk_assessment_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    risk_level: ImprovementRiskLevel
    protected_core_impact: bool
    safety_passed: bool
    benchmark_passed: bool
    quality_score: float = Field(ge=0.0, le=1.0)
    approval_eligible: bool
    findings: tuple[str, ...] = Field(default_factory=tuple)
    evidence: dict[str, Any] = Field(default_factory=dict, validate_default=True)
    created_at: datetime

    @field_validator("findings")
    @classmethod
    def findings_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "self-improvement risk finding")
        return value

    @field_validator("evidence", mode="before")
    @classmethod
    def evidence_must_be_frozen(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return _FrozenDict()
        return _frozen_evidence_mapping(value)

    @model_validator(mode="after")
    def evidence_must_remain_frozen(self) -> ImprovementRiskAssessment:
        object.__setattr__(self, "evidence", _frozen_evidence_mapping(self.evidence))
        return self

    @model_validator(mode="after")
    def failed_safety_or_benchmarks_block_eligibility(self) -> ImprovementRiskAssessment:
        if self.approval_eligible and not self.safety_passed:
            raise ValueError("safety failure cannot be offset by quality score")
        if self.approval_eligible and not self.benchmark_passed:
            raise ValueError("benchmark failure blocks approval")
        return self


class ImprovementChangeBudget(BaseModel):
    """Bounded change budget for a self-improvement proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    change_budget_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    max_files: int = Field(ge=0)
    max_insertions: int = Field(ge=0)
    max_deletions: int = Field(ge=0)
    max_dependency_changes: int = Field(ge=0)
    max_protected_paths: int = Field(ge=0)
    observed_files: int = Field(ge=0)
    observed_insertions: int = Field(ge=0)
    observed_deletions: int = Field(ge=0)
    dependency_changes: int = Field(ge=0)
    protected_paths_touched: int = Field(ge=0)
    within_budget: bool
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime

    @model_validator(mode="after")
    def observed_change_must_fit_budget(self) -> ImprovementChangeBudget:
        within_limits = (
            self.observed_files <= self.max_files
            and self.observed_insertions <= self.max_insertions
            and self.observed_deletions <= self.max_deletions
            and self.dependency_changes <= self.max_dependency_changes
            and self.protected_paths_touched <= self.max_protected_paths
        )
        if self.within_budget != within_limits:
            raise ValueError("within_budget must reflect observed change budget")
        return self


class ImprovementApprovalBinding(BaseModel):
    """Human approval bound to exact commit and diff hashes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    approval_binding_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    approval_status: ImprovementApprovalStatus
    proposal_author_actor_id: str = Field(min_length=1)
    approver_actor_id: str = Field(min_length=1)
    approved_commit_sha: str | None = None
    approved_diff_hash: str | None = None
    current_commit_sha: str | None = None
    current_diff_hash: str | None = None
    protected_core_change: bool
    required_approver_count: int = Field(ge=1)
    observed_approver_count: int = Field(ge=0)
    approval_evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime

    @field_validator("approved_commit_sha", "current_commit_sha")
    @classmethod
    def commit_sha_must_be_exact(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("commit SHA must be exact 40-character lowercase hex")
        return value

    @field_validator("approved_diff_hash", "current_diff_hash")
    @classmethod
    def diff_hash_must_be_exact(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("diff hash must be exact 64-character lowercase hex")
        return value

    @model_validator(mode="after")
    def approval_must_be_exact_and_independent(self) -> ImprovementApprovalBinding:
        if self.approver_actor_id == self.proposal_author_actor_id:
            raise ValueError("proposal author cannot approve its own proposal")
        if self.protected_core_change and self.required_approver_count < 2:
            raise ValueError("protected-core proposal cannot use single approval")
        if self.approval_status == "approved":
            if (
                self.approved_commit_sha is None
                or self.approved_diff_hash is None
                or self.current_commit_sha is None
                or self.current_diff_hash is None
            ):
                raise ValueError("approved binding requires exact commit and diff hashes")
            if self.approved_commit_sha != self.current_commit_sha:
                raise ValueError("post-approval code change invalidates approval")
            if self.approved_diff_hash != self.current_diff_hash:
                raise ValueError("post-approval diff change invalidates approval")
            if self.observed_approver_count < self.required_approver_count:
                raise ValueError("observed approvals must satisfy required approvals")
        return self


class ImprovementProtectedPathDecision(BaseModel):
    """Protected-core classification for one path touched by a proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    protected: bool
    matched_pattern: str | None = None
    required_approver_count: int = Field(ge=1)
    reason: str = Field(min_length=1)

    @field_validator("path", "reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "self-improvement protected path text")
        return cleaned

    @model_validator(mode="after")
    def protected_path_requires_dual_approval(self) -> ImprovementProtectedPathDecision:
        if self.protected and self.required_approver_count < 2:
            raise ValueError("protected paths require at least two approvers")
        return self


class ImprovementRollbackPlan(BaseModel):
    """Required rollback plan for high-risk self-improvement work."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rollback_plan_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    required: bool
    steps: tuple[str, ...] = Field(min_length=1)
    verification_checks: tuple[str, ...] = Field(min_length=1)
    owner_actor_id: str = Field(min_length=1)
    estimated_minutes: int = Field(ge=1)
    created_at: datetime

    @field_validator("steps", "verification_checks")
    @classmethod
    def rollback_text_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "self-improvement rollback text")
        return value


class ImprovementGovernanceDecision(BaseModel):
    """Fail-closed governance decision for a self-improvement proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    governance_decision_id: str = Field(min_length=1)
    proposal: ImprovementProposalRef
    lifecycle_state: ImprovementLifecycleState
    risk_assessment: ImprovementRiskAssessment
    change_budget: ImprovementChangeBudget
    protected_path_decisions: tuple[ImprovementProtectedPathDecision, ...] = (
        Field(default_factory=tuple)
    )
    approval_binding: ImprovementApprovalBinding | None = None
    rollback_plan: ImprovementRollbackPlan | None = None
    status: ImprovementDecisionStatus
    reason_codes: tuple[str, ...] = Field(min_length=1)
    patch_creation_allowed: bool
    git_mutation_allowed: bool
    pr_creation_allowed: bool
    production_runtime_activation_allowed: bool
    created_at: datetime

    @model_validator(mode="after")
    def governance_must_fail_closed(self) -> ImprovementGovernanceDecision:
        if self.patch_creation_allowed:
            raise ValueError("patch creation is not authorized in AION-166")
        if self.git_mutation_allowed:
            raise ValueError("Git mutation is not authorized in AION-166")
        if self.pr_creation_allowed:
            raise ValueError("PR creation is not authorized in AION-166")
        if self.production_runtime_activation_allowed:
            raise ValueError("production runtime activation is not authorized in AION-166")
        if self.status == "approved":
            if not self.risk_assessment.safety_passed:
                raise ValueError("safety failure cannot be offset by quality score")
            if not self.risk_assessment.benchmark_passed:
                raise ValueError("benchmark failure blocks approval")
            if not self.risk_assessment.approval_eligible:
                raise ValueError("risk assessment is not approval eligible")
            if not self.change_budget.within_budget:
                raise ValueError("change budget failure blocks approval")
            if self.approval_binding is None or self.approval_binding.approval_status != "approved":
                raise ValueError("approved governance requires approved binding")
        if (
            self.risk_assessment.risk_level in {"high", "critical"}
            and self.rollback_plan is None
            and self.status != "blocked"
        ):
            raise ValueError("missing rollback plan blocks high-risk proposals")
        return self


class ImprovementAuditEvent(BaseModel):
    """Redacted audit event emitted by the self-improvement governance plane."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    audit_event_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    event_type: ImprovementAuditEventType
    actor_id: str = Field(min_length=1)
    redacted_summary: str = Field(min_length=1)
    evidence: dict[str, Any] = Field(default_factory=dict, validate_default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("redacted_summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "self-improvement audit summary")
        return value.strip()

    @field_validator("evidence", mode="before")
    @classmethod
    def evidence_must_be_frozen(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return _FrozenDict()
        return _frozen_evidence_mapping(value)

    @model_validator(mode="after")
    def evidence_must_remain_frozen(self) -> ImprovementAuditEvent:
        object.__setattr__(self, "evidence", _frozen_evidence_mapping(self.evidence))
        return self

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ImprovementProvenanceRecord(BaseModel):
    """Immutable provenance record for self-improvement evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provenance_record_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)
    redacted_summary: str = Field(min_length=1)
    input_evidence: dict[str, Any] = Field(default_factory=dict, validate_default=True)
    output_evidence: dict[str, Any] = Field(default_factory=dict, validate_default=True)
    created_at: datetime

    @field_validator("redacted_summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "self-improvement provenance summary")
        return value.strip()

    @field_validator("source_refs")
    @classmethod
    def source_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "self-improvement provenance source")
        return value

    @field_validator("input_evidence", "output_evidence", mode="before")
    @classmethod
    def provenance_evidence_must_be_frozen(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return _FrozenDict()
        return _frozen_evidence_mapping(value)

    @model_validator(mode="after")
    def provenance_evidence_must_remain_frozen(self) -> ImprovementProvenanceRecord:
        object.__setattr__(
            self,
            "input_evidence",
            _frozen_evidence_mapping(self.input_evidence),
        )
        object.__setattr__(
            self,
            "output_evidence",
            _frozen_evidence_mapping(self.output_evidence),
        )
        return self
