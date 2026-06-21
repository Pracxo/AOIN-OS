"""Preference ledger contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.concepts import reject_secret_like_keys, text_has_secret_markers

PreferenceType = Literal[
    "response_style",
    "formatting",
    "verbosity",
    "citation",
    "language",
    "workflow",
    "memory",
    "clarification",
    "operator",
    "style",
    "interaction",
    "format",
    "retrieval",
    "notification",
    "generic",
]
PreferenceStatus = Literal["candidate", "confirmed", "disabled", "rejected", "superseded"]
PreferenceLearningCandidateStatus = Literal[
    "proposed",
    "candidate",
    "confirmed",
    "rejected",
    "archived",
]
PreferenceSourceType = Literal[
    "user",
    "operator",
    "dialogue",
    "feedback",
    "learning",
    "memory",
    "system_config",
    "generic",
]

_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_FORBIDDEN_OVERRIDE_MARKERS = (
    "ignore policy",
    "override policy",
    "bypass policy",
    "bypass approval",
    "skip approval",
    "disable autonomy",
    "override autonomy",
    "override runtime config",
    "bypass sandbox",
    "show chain of thought",
    "reveal hidden reasoning",
    "expose secrets",
)


class PreferenceCreateRequest(BaseModel):
    """Request to create a preference ledger record."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preference_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    preference_key: str = Field(min_length=1)
    preference_type: PreferenceType = "generic"
    preference_value: dict[str, Any] = Field(default_factory=dict)
    status: PreferenceStatus = "candidate"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_type: PreferenceSourceType = "user"
    source_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("preference_key")
    @classmethod
    def preference_key_must_be_normalized(cls, value: str) -> str:
        normalized = normalize_preference_key(value)
        if not _KEY_RE.fullmatch(normalized):
            raise ValueError("preference_key must be lowercase dotted text")
        return normalized

    @field_validator("preference_value", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value

    def to_record(self, preference_id: str) -> PreferenceRecord:
        """Convert to the canonical stored preference record."""

        return PreferenceRecord(
            preference_id=preference_id,
            trace_id=self.trace_id,
            actor_id=self.actor_id,
            workspace_id=self.workspace_id,
            preference_key=self.preference_key,
            preference_type=self.preference_type,
            preference_value=self.preference_value,
            status=self.status,
            confidence=self.confidence,
            source_type=self.source_type,
            source_id=self.source_id,
            owner_scope=self.owner_scope,
            evidence_refs=self.evidence_refs,
            metadata=self.metadata,
            created_by=self.created_by,
        )


class PreferenceRecord(BaseModel):
    """One confirmed or candidate actor/workspace preference."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preference_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    preference_key: str = Field(min_length=1)
    preference_type: PreferenceType = "generic"
    preference_value: dict[str, Any] = Field(default_factory=dict)
    status: PreferenceStatus = "candidate"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_type: PreferenceSourceType = "generic"
    source_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    confirmed_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    confirmed_at: datetime | None = None
    rejected_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("preference_key")
    @classmethod
    def preference_key_must_be_normalized(cls, value: str) -> str:
        normalized = normalize_preference_key(value)
        if not _KEY_RE.fullmatch(normalized):
            raise ValueError("preference_key must be lowercase dotted text")
        return normalized

    @field_validator("preference_value", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value


class PreferenceLearningCandidate(BaseModel):
    """Reviewable candidate learned from explicit feedback or dialogue flags."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    candidate_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    preference_key: str = Field(min_length=1)
    preference_type: PreferenceType = "generic"
    proposed_value: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("proposed_value", "preference_value"),
    )
    status: PreferenceLearningCandidateStatus = "proposed"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str = Field(default="Explicit preference candidate.", min_length=1)
    source_type: PreferenceSourceType = "generic"
    source_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @property
    def preference_value(self) -> dict[str, Any]:
        """Backward-compatible access for service internals."""

        return self.proposed_value

    @field_validator("preference_key")
    @classmethod
    def preference_key_must_be_normalized(cls, value: str) -> str:
        normalized = normalize_preference_key(value)
        if not _KEY_RE.fullmatch(normalized):
            raise ValueError("preference_key must be lowercase dotted text")
        return normalized

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason cannot be empty")
        if text_has_secret_markers(value):
            raise ValueError("reason must not contain raw secrets")
        return value.strip()

    @field_validator("proposed_value", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value


def normalize_preference_key(value: str) -> str:
    """Normalize a preference key to deterministic lowercase dotted text."""

    return re.sub(r"[\s/]+", ".", value.strip().lower()).replace("..", ".")


def reject_forbidden_override_payload(value: Any) -> None:
    """Reject nested preference values that try to bypass hard AION boundaries."""

    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_forbidden_override(str(key)):
                raise ValueError("preference payload contains forbidden override key")
            reject_forbidden_override_payload(item)
    elif isinstance(value, list):
        for item in value:
            reject_forbidden_override_payload(item)
    elif isinstance(value, str) and _contains_forbidden_override(value):
        raise ValueError("preference payload contains forbidden override value")


def _contains_forbidden_override(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _FORBIDDEN_OVERRIDE_MARKERS)


__all__ = [
    "PreferenceCreateRequest",
    "PreferenceLearningCandidate",
    "PreferenceLearningCandidateStatus",
    "PreferenceRecord",
    "PreferenceSourceType",
    "PreferenceStatus",
    "PreferenceType",
    "normalize_preference_key",
    "reject_forbidden_override_payload",
]
