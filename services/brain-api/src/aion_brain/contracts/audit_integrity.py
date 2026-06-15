"""Tamper-evident audit integrity contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from pathlib import PurePath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AuditOutcome = Literal[
    "allowed",
    "denied",
    "blocked",
    "waiting_for_approval",
    "completed",
    "failed",
    "skipped",
    "dry_run",
    "redacted",
    "corrected",
]
AuditCheckpointStatus = Literal["created", "verified", "failed"]
AuditVerificationStatus = Literal["passed", "warning", "failed"]
AuditExportType = Literal["json", "jsonl", "manifest_only"]
AuditRedactionMode = Literal["metadata_only", "redact_sensitive", "exclude_sensitive"]
AuditExportStatus = Literal[
    "dry_run",
    "completed",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
]
ProvenanceResourceType = Literal[
    "event",
    "command",
    "memory",
    "graph_node",
    "graph_edge",
    "evidence",
    "evidence_chunk",
    "trace",
    "reasoning",
    "model_call",
    "plan",
    "execution",
    "workflow",
    "task",
    "goal",
    "approval",
    "policy",
    "risk",
    "autonomy",
    "capability",
    "module",
    "mcp",
    "sandbox",
    "backup",
    "release_package",
    "scenario",
    "audit_entry",
]
ProvenanceRelationType = Literal[
    "caused",
    "produced",
    "read",
    "wrote",
    "referenced",
    "grounded_by",
    "approved_by",
    "denied_by",
    "authorized_by",
    "blocked_by",
    "evaluated_by",
    "derived_from",
    "superseded_by",
    "corrected_by",
    "exported_by",
]

_SENSITIVE_KEY_PARTS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
    "authorization",
    "bearer",
    "raw_prompt",
}
_CHAIN_OF_THOUGHT_KEYS = {"chain_of_thought", "hidden_reasoning"}


class AuditEntry(BaseModel):
    """Append-only hash-chain audit entry."""

    model_config = ConfigDict(extra="forbid")

    audit_entry_id: str = Field(min_length=1)
    sequence_number: int = Field(ge=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    event_type: str = Field(min_length=1)
    outcome: AuditOutcome
    risk_level: str | None = None
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    command_id: str | None = None
    source_component: str = Field(min_length=1)
    payload_hash: str = Field(min_length=1)
    previous_hash: str | None = None
    entry_hash: str = Field(min_length=1)
    hash_algorithm: str
    canonical_payload: dict[str, Any]
    redaction_metadata: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime | None = None

    @field_validator("hash_algorithm")
    @classmethod
    def hash_algorithm_must_be_sha256(cls, value: str) -> str:
        if value != "sha256":
            raise ValueError("hash_algorithm must be sha256")
        return value

    @field_validator("canonical_payload", "redaction_metadata", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value, allow_redacted=True)
        return value


class AuditRecordRequest(BaseModel):
    """Request to append one audit entry."""

    model_config = ConfigDict(extra="forbid")

    audit_entry_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    event_type: str = Field(min_length=1)
    outcome: AuditOutcome
    risk_level: str | None = None
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    command_id: str | None = None
    source_component: str = Field(min_length=1)
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def strip_hidden_reasoning(self) -> AuditRecordRequest:
        self.payload = _strip_chain_of_thought(self.payload)
        self.metadata = _strip_chain_of_thought(self.metadata)
        _reject_unsafe_payload(self.payload, allow_redacted=True)
        _reject_unsafe_payload(self.metadata, allow_redacted=True)
        return self


class AuditIntegrityCheckpoint(BaseModel):
    """Hash checkpoint over a contiguous audit entry range."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(min_length=1)
    from_sequence: int = Field(ge=1)
    to_sequence: int = Field(ge=1)
    entry_count: int = Field(ge=0)
    root_hash: str = Field(min_length=1)
    previous_checkpoint_hash: str | None = None
    checkpoint_hash: str = Field(min_length=1)
    hash_algorithm: str
    status: AuditCheckpointStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("hash_algorithm")
    @classmethod
    def hash_algorithm_must_be_sha256(cls, value: str) -> str:
        if value != "sha256":
            raise ValueError("hash_algorithm must be sha256")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value, allow_redacted=True)
        return value

    @model_validator(mode="after")
    def sequence_range_must_be_coherent(self) -> AuditIntegrityCheckpoint:
        if self.to_sequence < self.from_sequence:
            raise ValueError("to_sequence must be greater than or equal to from_sequence")
        return self


class ProvenanceLink(BaseModel):
    """Generic provenance edge between two AION records."""

    model_config = ConfigDict(extra="forbid")

    provenance_link_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_type: ProvenanceResourceType
    source_id: str = Field(min_length=1)
    target_type: ProvenanceResourceType
    target_id: str = Field(min_length=1)
    relation_type: ProvenanceRelationType
    confidence: float = Field(ge=0, le=1)
    audit_entry_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value, allow_redacted=True)
        return value


class AuditVerificationRequest(BaseModel):
    """Request to verify audit hash-chain integrity."""

    model_config = ConfigDict(extra="forbid")

    audit_verification_id: str | None = None
    trace_id: str | None = None
    from_sequence: int | None = Field(default=None, ge=1)
    to_sequence: int | None = Field(default=None, ge=1)
    verify_checkpoints: bool = True
    verify_hash_chain: bool = True
    verify_payload_hashes: bool = True
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value, allow_redacted=True)
        return value

    @model_validator(mode="after")
    def sequence_range_must_be_coherent(self) -> AuditVerificationRequest:
        if (
            self.from_sequence is not None
            and self.to_sequence is not None
            and self.to_sequence < self.from_sequence
        ):
            raise ValueError("to_sequence must be greater than or equal to from_sequence")
        return self


class AuditVerificationRun(BaseModel):
    """Persisted audit verification report."""

    model_config = ConfigDict(extra="forbid")

    audit_verification_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: AuditVerificationStatus
    from_sequence: int | None = None
    to_sequence: int | None = None
    checked_count: int = Field(ge=0)
    valid_count: int = Field(ge=0)
    invalid_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    violations: list[dict[str, Any]]
    report: dict[str, Any]
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("violations")
    @classmethod
    def violations_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for violation in value:
            _reject_unsafe_payload(violation, allow_redacted=True)
        return value

    @field_validator("report")
    @classmethod
    def report_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value, allow_redacted=True)
        return value


class AuditExportRequest(BaseModel):
    """Request to export audit entries locally."""

    model_config = ConfigDict(extra="forbid")

    audit_export_id: str | None = None
    trace_id: str | None = None
    export_type: AuditExportType = "jsonl"
    owner_scope: list[str] = Field(min_length=1)
    from_sequence: int | None = Field(default=None, ge=1)
    to_sequence: int | None = Field(default=None, ge=1)
    filters: dict[str, Any] = Field(default_factory=dict)
    redaction_mode: AuditRedactionMode = "redact_sensitive"
    output_dir: str = "artifacts/audit"
    dry_run: bool = True
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("filters", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value, allow_redacted=True)
        return value

    @field_validator("output_dir")
    @classmethod
    def output_dir_must_be_safe(cls, value: str) -> str:
        path = PurePath(value)
        if ".." in path.parts:
            raise ValueError("output_dir must not contain path traversal")
        return value

    @model_validator(mode="after")
    def sequence_range_must_be_coherent(self) -> AuditExportRequest:
        if (
            self.from_sequence is not None
            and self.to_sequence is not None
            and self.to_sequence < self.from_sequence
        ):
            raise ValueError("to_sequence must be greater than or equal to from_sequence")
        return self


class AuditExportRecord(BaseModel):
    """Persisted local audit export record."""

    model_config = ConfigDict(extra="forbid")

    audit_export_id: str = Field(min_length=1)
    trace_id: str | None = None
    export_type: AuditExportType
    status: AuditExportStatus
    owner_scope: list[str] = Field(min_length=1)
    from_sequence: int | None = None
    to_sequence: int | None = None
    filters: dict[str, Any]
    redaction_mode: AuditRedactionMode
    output_ref: str | None = None
    file_count: int = Field(ge=0)
    entry_count: int = Field(ge=0)
    checksum: str | None = None
    result: dict[str, Any]
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("filters", "result")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value, allow_redacted=True)
        return value


class AuditIntegrityStatus(BaseModel):
    """Current local audit integrity state."""

    model_config = ConfigDict(extra="forbid")

    latest_sequence: int
    latest_entry_hash: str | None
    latest_checkpoint_id: str | None
    latest_checkpoint_hash: str | None
    verification_status: str
    open_violations: int
    generated_at: datetime


def _normalize_key(key: str) -> str:
    return key.lower().replace("-", "_")


def _contains_sensitive_key(key: str) -> bool:
    normalized = _normalize_key(key)
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _strip_chain_of_thought(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_chain_of_thought(item)
            for key, item in value.items()
            if _normalize_key(str(key)) not in _CHAIN_OF_THOUGHT_KEYS
        }
    if isinstance(value, list):
        return [_strip_chain_of_thought(item) for item in value]
    return value


def _reject_unsafe_payload(value: Any, *, allow_redacted: bool) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = _normalize_key(str(key))
            if normalized in _CHAIN_OF_THOUGHT_KEYS:
                raise ValueError("payload must not contain chain-of-thought")
            if _contains_sensitive_key(str(key)) and not (
                allow_redacted and item == "[REDACTED]"
            ):
                raise ValueError("payload must not contain raw secrets or prompts")
            _reject_unsafe_payload(item, allow_redacted=allow_redacted)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item, allow_redacted=allow_redacted)
