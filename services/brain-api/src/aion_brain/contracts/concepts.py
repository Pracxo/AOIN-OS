"""Concept registry contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ConceptType = Literal[
    "generic",
    "process",
    "capability",
    "constraint",
    "policy",
    "goal",
    "task",
    "memory_type",
    "evidence_type",
    "system_component",
    "abstract",
]
ConceptStatus = Literal["active", "archived"]

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
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")


class ConceptRecord(BaseModel):
    """One abstract, domain-neutral concept known to AION Brain."""

    model_config = ConfigDict(extra="forbid")

    concept_id: str = Field(min_length=1)
    trace_id: str | None = None
    name: str = Field(min_length=1)
    normalized_name: str = Field(min_length=1)
    concept_type: ConceptType
    status: ConceptStatus
    description: str
    owner_scope: list[str] = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("name", "normalized_name")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ConceptCreateRequest(BaseModel):
    """Request to create one concept."""

    model_config = ConfigDict(extra="forbid")

    concept_id: str | None = None
    trace_id: str | None = None
    name: str = Field(min_length=1)
    concept_type: ConceptType = "generic"
    description: str
    owner_scope: list[str] = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_be_safe(cls, value: str) -> str:
        _reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ConceptArchiveRequest(BaseModel):
    """Request to archive one concept."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


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


def text_has_secret_markers(value: str) -> bool:
    """Return true when text contains obvious raw secret values."""
    lowered = value.lower()
    return any(marker in lowered for marker in _SECRET_VALUE_MARKERS)


def _reject_secret_text(value: str) -> None:
    if not value.strip():
        raise ValueError("value cannot be empty")
    if text_has_secret_markers(value):
        raise ValueError("value must not contain raw secrets")


__all__ = [
    "ConceptArchiveRequest",
    "ConceptCreateRequest",
    "ConceptRecord",
    "ConceptStatus",
    "ConceptType",
    "reject_secret_like_keys",
    "text_has_secret_markers",
]
