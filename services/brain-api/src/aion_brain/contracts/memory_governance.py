"""Memory governance contracts owned by AION Brain."""

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.memory import MemoryRecord, MemoryType

GovernanceRuleStatus = Literal["active", "disabled"]
MemoryGovernanceRuleType = Literal[
    "retention",
    "decay",
    "write_gate",
    "retrieval_gate",
    "compaction",
    "forgetting",
    "conflict_detection",
]
MemoryGovernanceAction = Literal[
    "allow",
    "deny",
    "require_approval",
    "decay",
    "expire",
    "compact",
    "flag_conflict",
    "forget",
]
MemoryGovernanceActionType = Literal[
    "memory.write",
    "memory.retrieve",
    "memory.update",
    "memory.forget",
    "memory.compact",
    "memory.decay",
    "memory.conflict.scan",
]
MemorySensitivity = Literal["public", "internal", "confidential", "restricted"]
ForgetTargetType = Literal[
    "memory",
    "semantic_index",
    "graph_node",
    "graph_edge",
    "evidence_link",
    "skill_candidate",
    "skill",
    "trace_attachment",
]
ForgetStatus = Literal["pending_approval", "completed", "blocked_by_policy", "failed"]
MemoryConflictType = Literal[
    "duplicate",
    "metadata_fact_conflict",
    "evidence_contradiction",
    "stale_preference",
    "competing_procedure",
    "scope_conflict",
]
MemoryConflictSeverity = Literal["low", "medium", "high", "critical"]
MemoryConflictStatus = Literal["open", "resolved", "dismissed"]
MemoryConflictResolution = Literal[
    "keep_newest",
    "keep_highest_confidence",
    "keep_evidence_grounded",
    "dismiss",
    "manual_review",
]
MemoryCompactionStrategy = Literal[
    "deterministic_extract",
    "merge_duplicates",
    "summarize_by_metadata_key",
    "preference_rollup",
    "procedure_rollup",
]
MemoryCompactionStatus = Literal[
    "completed",
    "pending_approval",
    "blocked_by_policy",
    "failed",
]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
    "authorization",
}
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "hr",
    "procurement",
}


class MemoryGovernanceRule(BaseModel):
    """Generic memory lifecycle governance rule."""

    model_config = ConfigDict(extra="forbid")

    governance_rule_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: GovernanceRuleStatus
    rule_type: MemoryGovernanceRuleType
    memory_types: list[MemoryType] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    sensitivity_levels: list[MemorySensitivity] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    action: MemoryGovernanceAction
    priority: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms(value)
        return value

    @field_validator("conditions", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secrets and domain-specific keys or values."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class MemoryGovernanceDecision(BaseModel):
    """Persisted result of memory governance evaluation."""

    model_config = ConfigDict(extra="forbid")

    governance_decision_id: str = Field(min_length=1)
    trace_id: str | None = None
    memory_id: str | None = None
    rule_ids: list[str] = Field(default_factory=list)
    decision: MemoryGovernanceAction
    reason: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class MemoryDecayRecord(BaseModel):
    """Deterministic decay score record."""

    model_config = ConfigDict(extra="forbid")

    decay_id: str = Field(min_length=1)
    memory_id: str = Field(min_length=1)
    previous_score: float = Field(ge=0.0, le=1.0)
    new_score: float = Field(ge=0.0, le=1.0)
    decay_reason: str = Field(min_length=1)
    factors: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class MemoryGovernanceEvaluationRequest(BaseModel):
    """Request to evaluate memory governance rules."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    memory: MemoryRecord
    action_type: MemoryGovernanceActionType
    owner_scope: list[str] = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ForgetMemoryRequest(BaseModel):
    """Request to forget a memory-owned target through policy."""

    model_config = ConfigDict(extra="forbid")

    forget_request_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    target_type: ForgetTargetType
    target_id: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)
    requested_by: str | None = None
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Reject blank reasons."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class ForgetMemoryResult(BaseModel):
    """Result of a policy-gated forget request."""

    model_config = ConfigDict(extra="forbid")

    forget_request_id: str
    target_type: ForgetTargetType
    target_id: str
    status: ForgetStatus
    forgotten: bool
    approval_required: bool
    approval_request_id: str | None
    affected_refs: list[str] = Field(default_factory=list)
    preserved_refs: list[str] = Field(default_factory=list)
    reason: str
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class MemoryConflict(BaseModel):
    """Detected generic memory conflict."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str = Field(min_length=1)
    trace_id: str | None = None
    conflict_type: MemoryConflictType
    memory_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    severity: MemoryConflictSeverity
    status: MemoryConflictStatus
    description: str = Field(min_length=1)
    detected_by: str = Field(min_length=1)
    resolution: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class MemoryConflictScanRequest(BaseModel):
    """Request to scan for generic memory conflicts."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    memory_types: list[MemoryType] = Field(default_factory=list)
    conflict_types: list[MemoryConflictType] = Field(default_factory=list)
    limit: int = Field(default=500, ge=1, le=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryConflictResolutionRequest(BaseModel):
    """Request to resolve a generic memory conflict."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str = Field(min_length=1)
    resolution: MemoryConflictResolution
    actor_id: str | None = None
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Reject blank reasons."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value


class MemoryCompactionRequest(BaseModel):
    """Request deterministic memory compaction."""

    model_config = ConfigDict(extra="forbid")

    compaction_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    memory_types: list[MemoryType] = Field(default_factory=list)
    memory_ids: list[str] = Field(default_factory=list)
    strategy: MemoryCompactionStrategy = "deterministic_extract"
    max_input_records: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = True
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("strategy")
    @classmethod
    def strategy_must_be_domain_neutral(cls, value: str) -> str:
        """Reject domain-specific strategy names."""
        _reject_domain_terms(value)
        return value


class MemoryCompactionResult(BaseModel):
    """Result of deterministic memory compaction."""

    model_config = ConfigDict(extra="forbid")

    compaction_run_id: str
    status: MemoryCompactionStatus
    dry_run: bool
    strategy: MemoryCompactionStrategy
    input_memory_ids: list[str] = Field(default_factory=list)
    output_memory_ids: list[str] = Field(default_factory=list)
    compacted_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    approval_required: bool
    approval_request_id: str | None
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None


class MemoryRetentionSweepRequest(BaseModel):
    """Request to sweep memories for retention and decay."""

    model_config = ConfigDict(extra="forbid")

    owner_scope: list[str] = Field(min_length=1)
    memory_types: list[MemoryType] = Field(default_factory=list)
    dry_run: bool = True
    limit: int = Field(default=1000, ge=1, le=10000)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryRetentionSweepResult(BaseModel):
    """Result of a retention or decay sweep."""

    model_config = ConfigDict(extra="forbid")

    evaluated: int = Field(ge=0)
    expired: int = Field(ge=0)
    decayed: int = Field(ge=0)
    pending_approval: int = Field(ge=0)
    skipped: int = Field(ge=0)
    dry_run: bool
    decisions: list[MemoryGovernanceDecision] = Field(default_factory=list)


class MemoryForgettingRequestRecord(BaseModel):
    """Persistent forgetting request row."""

    model_config = ConfigDict(extra="forbid")

    forget_request_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    target_type: ForgetTargetType
    target_id: str
    owner_scope: list[str]
    reason: str
    status: ForgetStatus
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    requested_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class MemoryCompactionRunRecord(BaseModel):
    """Persistent compaction run row."""

    model_config = ConfigDict(extra="forbid")

    compaction_run_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str]
    memory_types: list[str]
    status: MemoryCompactionStatus
    input_memory_ids: list[str]
    output_memory_ids: list[str]
    strategy: MemoryCompactionStrategy
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class MemoryCompactedRecord(BaseModel):
    """Persistent relation from compacted output to inputs."""

    model_config = ConfigDict(extra="forbid")

    compacted_record_id: str
    compaction_run_id: str
    output_memory_id: str
    input_memory_ids: list[str]
    compaction_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


def _reject_secret_like_keys(value: object) -> None:
    if _has_secret_like_key(value):
        raise ValueError("metadata must not contain secret-like keys")


def _has_secret_like_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in _SECRET_KEY_PARTS):
                return True
            if _has_secret_like_key(nested):
                return True
    if isinstance(value, list):
        return any(_has_secret_like_key(item) for item in value)
    return False


def _reject_domain_terms(value: object) -> None:
    if isinstance(value, str):
        tokens = set(re.findall(r"[a-z0-9]+", value.lower()))
        if tokens.intersection(_BANNED_DOMAIN_TERMS):
            raise ValueError("memory governance rules must remain domain-neutral")
    elif isinstance(value, dict):
        for key, nested in value.items():
            _reject_domain_terms(str(key))
            _reject_domain_terms(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_domain_terms(item)
