"""Release candidate gate contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.verification_matrix import VerificationCheck

ReleaseCandidateStatus = Literal[
    "proposed",
    "verifying",
    "passed",
    "failed",
    "blocked",
    "archived",
    "deleted",
]
RCGateMode = Literal["dry_run", "controlled"]
RCGateRunStatus = Literal["passed", "warning", "failed", "blocked", "dry_run"]
RCFindingType = Literal[
    "failed_required_check",
    "missing_required_check",
    "critical_warning",
    "docker_smoke_failed",
    "golden_path_failed",
    "freeze_gate_failed",
    "release_package_failed",
    "contract_drift",
    "registry_integrity",
    "lifecycle_risk",
    "external_feature_enabled",
    "activation_enabled",
    "policy_gap",
    "typecheck_failed",
    "test_failed",
    "generic",
]
RCFindingStatus = Literal["open", "resolved", "dismissed", "archived"]
RCSeverity = Literal["low", "medium", "high", "critical"]
RCEvidencePackStatus = Literal["created", "warning", "failed"]
RCEvidencePackType = Literal["rc", "freeze", "release", "audit", "local"]
RCReportStatus = Literal["passed", "warning", "failed", "blocked", "dry_run"]

_DOTTED_LOWERCASE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$")


class ReleaseCandidate(BaseModel):
    """One local release candidate record."""

    model_config = ConfigDict(extra="forbid")

    release_candidate_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    rc_key: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ReleaseCandidateStatus
    owner_scope: list[str] = Field(min_length=1)
    source_ref: str | None = None
    commit_ref: str | None = None
    tag_ref: str | None = None
    verification_matrix_id: str | None = None
    rc_run_id: str | None = None
    rc_report_id: str | None = None
    freeze_gate_id: str | None = None
    release_package_id: str | None = None
    readiness_score: float = Field(ge=0.0, le=1.0)
    release_ready: bool
    blocker_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    evidence_pack_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("rc_key")
    @classmethod
    def rc_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWERCASE.fullmatch(value):
            raise ValueError("rc_key must be dotted lowercase text")
        return value

    @field_validator("version")
    @classmethod
    def version_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("version cannot be empty")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def blockers_force_not_ready(self) -> ReleaseCandidate:
        if self.blocker_count > 0:
            self.release_ready = False
        return self


class ReleaseCandidateCreateRequest(BaseModel):
    """Request to create a release candidate shell."""

    model_config = ConfigDict(extra="forbid")

    release_candidate_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    rc_key: str
    version: str
    owner_scope: list[str] = Field(min_length=1)
    source_ref: str | None = None
    commit_ref: str | None = None
    tag_ref: str | None = None
    verification_matrix_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("rc_key")
    @classmethod
    def rc_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWERCASE.fullmatch(value):
            raise ValueError("rc_key must be dotted lowercase text")
        return value

    @field_validator("version")
    @classmethod
    def version_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("version cannot be empty")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RCGateRunRequest(BaseModel):
    """Request to run the local release candidate gate."""

    model_config = ConfigDict(extra="forbid")

    rc_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    release_candidate_id: str | None = None
    rc_key: str | None = None
    version: str | None = None
    verification_matrix_id: str | None = None
    mode: RCGateMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    check_results: list[VerificationCheck] = Field(default_factory=list)
    run_service_checks: bool = True
    include_docker_smoke: bool = False
    include_release_package: bool = True
    include_freeze_gate: bool = True
    include_golden_path: bool = True
    include_bootstrap: bool = True
    create_notifications: bool = False
    create_operator_items: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("rc_key")
    @classmethod
    def rc_key_must_be_dotted_lowercase(cls, value: str | None) -> str | None:
        if value is not None and not _DOTTED_LOWERCASE.fullmatch(value):
            raise ValueError("rc_key must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RCFinding(BaseModel):
    """One release candidate gate finding."""

    model_config = ConfigDict(extra="forbid")

    rc_finding_id: str = Field(min_length=1)
    trace_id: str | None = None
    rc_run_id: str | None = None
    release_candidate_id: str | None = None
    finding_type: RCFindingType
    severity: RCSeverity
    status: RCFindingStatus
    blocking: bool
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    check_key: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    recommended_action: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("title", "description", "recommended_action", "check_key")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return value
        reject_hidden_or_secret_text(value, "rc finding text")
        return value.strip()

    @field_validator("metadata", "evidence_refs")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value


class RCGateRun(BaseModel):
    """One deterministic RC gate run."""

    model_config = ConfigDict(extra="forbid")

    rc_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    release_candidate_id: str | None = None
    verification_matrix_id: str | None = None
    status: RCGateRunStatus
    mode: RCGateMode
    owner_scope: list[str] = Field(min_length=1)
    started_at: datetime
    completed_at: datetime | None = None
    checks_total: int = Field(ge=0)
    checks_passed: int = Field(ge=0)
    checks_failed: int = Field(ge=0)
    checks_warning: int = Field(ge=0)
    checks_skipped: int = Field(ge=0)
    blocker_count: int = Field(ge=0)
    readiness_score: float = Field(ge=0.0, le=1.0)
    release_ready: bool
    verification_checks: list[VerificationCheck] = Field(default_factory=list)
    findings: list[RCFinding] = Field(default_factory=list)
    evidence_pack_id: str | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("warnings", "failures")
    @classmethod
    def list_payload_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_payload(value)
        return value

    @field_validator("result", "metadata")
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def blockers_force_not_ready(self) -> RCGateRun:
        if self.blocker_count > 0:
            self.release_ready = False
        return self


class RCEvidencePack(BaseModel):
    """Redacted RC evidence pack for local operator review."""

    model_config = ConfigDict(extra="forbid")

    evidence_pack_id: str = Field(min_length=1)
    trace_id: str | None = None
    rc_run_id: str | None = None
    release_candidate_id: str | None = None
    status: RCEvidencePackStatus
    owner_scope: list[str] = Field(min_length=1)
    pack_type: RCEvidencePackType
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    check_summaries: list[dict[str, Any]] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    report_hash: str = Field(min_length=1)
    redacted_report: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("title", "summary", "report_hash")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "rc evidence pack text")
        return value.strip()

    @field_validator("evidence_refs", "check_summaries", "artifact_refs")
    @classmethod
    def list_payload_must_be_safe(cls, value: list[Any]) -> list[Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("redacted_report", "metadata")
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RCReport(BaseModel):
    """Persisted release candidate report."""

    model_config = ConfigDict(extra="forbid")

    rc_report_id: str = Field(min_length=1)
    trace_id: str | None = None
    release_candidate_id: str | None = None
    rc_run_id: str | None = None
    status: RCReportStatus
    owner_scope: list[str] = Field(min_length=1)
    version: str = Field(min_length=1)
    readiness_score: float = Field(ge=0.0, le=1.0)
    release_ready: bool
    blocker_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    passed_checks: list[str] = Field(default_factory=list)
    failed_checks: list[str] = Field(default_factory=list)
    warning_checks: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("findings", "recommendations")
    @classmethod
    def list_payload_must_be_safe(cls, value: list[Any]) -> list[Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("report", "metadata")
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def blockers_force_not_ready(self) -> RCReport:
        if self.blocker_count > 0:
            self.release_ready = False
        return self


class RCQuery(BaseModel):
    """Query RC-owned records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    status: str | None = None
    version: str | None = None
    release_ready: bool | None = None
    limit: int = Field(default=50, ge=1, le=500)


__all__ = [
    "RCEvidencePack",
    "RCEvidencePackStatus",
    "RCEvidencePackType",
    "RCFinding",
    "RCFindingStatus",
    "RCFindingType",
    "RCGateMode",
    "RCGateRun",
    "RCGateRunRequest",
    "RCGateRunStatus",
    "RCQuery",
    "RCReport",
    "RCReportStatus",
    "RCSeverity",
    "ReleaseCandidate",
    "ReleaseCandidateCreateRequest",
    "ReleaseCandidateStatus",
]
