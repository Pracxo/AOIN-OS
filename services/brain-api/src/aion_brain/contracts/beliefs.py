"""Belief state and truth maintenance contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BeliefClaimType = Literal[
    "observation",
    "user_statement",
    "system_statement",
    "inferred",
    "preference",
    "constraint",
    "status",
    "capability",
    "policy",
    "generic",
]
BeliefClaimStatus = Literal[
    "proposed",
    "supported",
    "uncertain",
    "contradicted",
    "stale",
    "rejected",
    "archived",
]
BeliefSensitivity = Literal["public", "internal", "confidential", "restricted"]
BeliefSourceType = Literal[
    "user_message",
    "dialogue_response",
    "evidence",
    "evidence_chunk",
    "memory",
    "graph",
    "reasoning",
    "plan",
    "execution",
    "workflow",
    "task",
    "policy",
    "risk",
    "approval",
    "audit",
    "system",
    "generic",
]
BeliefSupportType = Literal[
    "evidence",
    "memory",
    "graph",
    "reasoning",
    "user_statement",
    "system_state",
    "audit",
    "provenance",
]
BeliefRelationType = Literal[
    "supports",
    "weakly_supports",
    "contradicts",
    "derives_from",
    "references",
    "observed_in",
    "grounded_by",
]
BeliefContradictionType = Literal[
    "direct_claim_conflict",
    "evidence_contradiction",
    "temporal_conflict",
    "scope_conflict",
    "confidence_conflict",
    "generic",
]
BeliefSeverity = Literal["low", "medium", "high", "critical"]
BeliefContradictionStatus = Literal["open", "resolved", "dismissed"]
TruthMaintenanceStatus = Literal["completed", "dry_run", "failed", "blocked_by_policy"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
_HIDDEN_MARKERS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "hidden reasoning",
    "raw_prompt",
    "raw prompt",
}
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")


class BeliefClaim(BaseModel):
    """One explicit claim in AION's belief ledger."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    claim_text: str = Field(min_length=1)
    normalized_claim: str = Field(min_length=1)
    claim_hash: str = Field(min_length=1)
    claim_type: BeliefClaimType
    status: BeliefClaimStatus
    confidence: float = Field(ge=0.0, le=1.0)
    sensitivity: BeliefSensitivity
    owner_scope: list[str] = Field(min_length=1)
    source_type: BeliefSourceType
    source_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    response_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    observed_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("claim_text")
    @classmethod
    def claim_text_must_be_safe(cls, value: str) -> str:
        """Reject hidden reasoning and raw secret markers in claim text."""
        _reject_hidden_or_secret_text(value, "claim_text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_like_keys(value)
        return value


class BeliefClaimCreateRequest(BaseModel):
    """Request to create one explicit belief claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    claim_text: str = Field(min_length=1)
    claim_type: BeliefClaimType = "generic"
    source_type: BeliefSourceType
    source_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    response_refs: list[str] = Field(default_factory=list)
    sensitivity: BeliefSensitivity = "internal"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    observed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("claim_text")
    @classmethod
    def claim_text_must_be_safe(cls, value: str) -> str:
        _reject_hidden_or_secret_text(value, "claim_text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class BeliefSupport(BaseModel):
    """Evidence or provenance supporting or relating to a claim."""

    model_config = ConfigDict(extra="forbid")

    support_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    support_type: BeliefSupportType
    source_type: BeliefSourceType
    source_id: str = Field(min_length=1)
    relation_type: BeliefRelationType = "supports"
    strength: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class BeliefSupportCreateRequest(BaseModel):
    """Request to create one support relation."""

    model_config = ConfigDict(extra="forbid")

    support_id: str | None = None
    claim_id: str = Field(min_length=1)
    support_type: BeliefSupportType
    source_type: BeliefSourceType
    source_id: str = Field(min_length=1)
    relation_type: BeliefRelationType = "supports"
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class BeliefContradiction(BaseModel):
    """One explicit contradiction related to a claim."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(min_length=1)
    trace_id: str | None = None
    claim_id: str = Field(min_length=1)
    contradicting_claim_id: str | None = None
    source_type: BeliefSourceType
    source_id: str = Field(min_length=1)
    contradiction_type: BeliefContradictionType
    severity: BeliefSeverity
    status: BeliefContradictionStatus
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class BeliefRevision(BaseModel):
    """Revision history for one claim."""

    model_config = ConfigDict(extra="forbid")

    revision_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    trace_id: str | None = None
    from_status: BeliefClaimStatus | None = None
    to_status: BeliefClaimStatus
    previous_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    new_confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class BeliefQuery(BaseModel):
    """Query belief claims through the belief boundary."""

    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    scope: list[str] = Field(min_length=1)
    claim_types: list[BeliefClaimType] = Field(default_factory=list)
    statuses: list[BeliefClaimStatus] = Field(default_factory=list)
    source_types: list[BeliefSourceType] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    include_deleted: bool = False
    include_stale: bool = True
    limit: int = Field(default=50, ge=1, le=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class BeliefQueryResult(BaseModel):
    """Belief query result."""

    model_config = ConfigDict(extra="forbid")

    claims: list[BeliefClaim]
    supports: list[BeliefSupport]
    contradictions: list[BeliefContradiction]
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TruthMaintenanceRequest(BaseModel):
    """Request to run deterministic truth maintenance."""

    model_config = ConfigDict(extra="forbid")

    truth_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    claim_ids: list[str] = Field(default_factory=list)
    statuses: list[BeliefClaimStatus] = Field(default_factory=list)
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class TruthMaintenanceRun(BaseModel):
    """Persisted truth maintenance result."""

    model_config = ConfigDict(extra="forbid")

    truth_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: TruthMaintenanceStatus
    owner_scope: list[str] = Field(min_length=1)
    input_claim_ids: list[str]
    revised_claim_ids: list[str]
    contradiction_ids: list[str]
    stale_claim_ids: list[str]
    result: dict[str, Any]
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ClaimExtractionRequest(BaseModel):
    """Request for deterministic claim extraction."""

    model_config = ConfigDict(extra="forbid")

    source_type: BeliefSourceType
    source_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    max_claims: int = Field(default=10, ge=1, le=50)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text cannot be empty")
        if text_has_hidden_markers(value):
            raise ValueError("text must not contain chain-of-thought or hidden reasoning")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ClaimExtractionResult(BaseModel):
    """Deterministic claim extraction output."""

    model_config = ConfigDict(extra="forbid")

    extracted_claims: list[BeliefClaimCreateRequest]
    skipped_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BeliefReviseRequest(BaseModel):
    """API request to revise one belief claim."""

    model_config = ConfigDict(extra="forbid")

    to_status: BeliefClaimStatus
    new_confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    created_by: str | None = None


class BeliefDeleteRequest(BaseModel):
    """API request to soft-delete a claim."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class BeliefResolveRequest(BaseModel):
    """API request to resolve a contradiction."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


def text_has_hidden_markers(value: str) -> bool:
    """Return true when text contains hidden reasoning or raw prompt markers."""
    lowered = value.lower()
    return any(marker in lowered for marker in _HIDDEN_MARKERS)


def text_has_secret_markers(value: str) -> bool:
    """Return true when text contains obvious raw secret values."""
    lowered = value.lower()
    return any(marker in lowered for marker in _SECRET_VALUE_MARKERS)


def reject_secret_like_keys(value: Any, path: str = "") -> None:
    """Reject nested secret-like metadata keys."""
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError(f"metadata contains secret-like key: {path}{key}")
            reject_secret_like_keys(item, f"{path}{key}.")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_secret_like_keys(item, f"{path}{index}.")


def _reject_hidden_or_secret_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    if text_has_hidden_markers(value):
        raise ValueError(f"{field_name} must not contain chain-of-thought or hidden reasoning")
    if text_has_secret_markers(value):
        raise ValueError(f"{field_name} must not contain raw secrets")


def metadata_is_safe(value: dict[str, Any]) -> bool:
    """Return whether metadata passes secret-like validation."""
    try:
        reject_secret_like_keys(value)
    except ValueError:
        return False
    return True


__all__ = [
    "BeliefClaim",
    "BeliefClaimCreateRequest",
    "BeliefContradiction",
    "BeliefDeleteRequest",
    "BeliefQuery",
    "BeliefQueryResult",
    "BeliefResolveRequest",
    "BeliefReviseRequest",
    "BeliefRevision",
    "BeliefSupport",
    "BeliefSupportCreateRequest",
    "ClaimExtractionRequest",
    "ClaimExtractionResult",
    "TruthMaintenanceRequest",
    "TruthMaintenanceRun",
    "metadata_is_safe",
    "reject_secret_like_keys",
    "text_has_hidden_markers",
    "text_has_secret_markers",
]
