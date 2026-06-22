"""Trace narrative contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.concepts import reject_secret_like_keys, text_has_secret_markers

TraceNarrativeStatus = Literal["completed", "partial", "failed", "insufficient_records"]

_HIDDEN_REASONING_MARKERS = (
    "chain_of_thought",
    "chain-of-thought",
    "chain of thought",
    "hidden_reasoning",
    "hidden reasoning",
    "raw_prompt",
    "raw prompt",
)


class TraceNarrative(BaseModel):
    """Public narrative summary of observable records for one trace."""

    model_config = ConfigDict(extra="forbid")

    trace_narrative_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    status: TraceNarrativeStatus
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    key_decisions: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)
    outcomes: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    redaction_metadata: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_public_safe(cls, value: str) -> str:
        _reject_hidden_or_secret_text(value)
        return value

    @field_validator(
        "timeline",
        "key_decisions",
        "blockers",
        "approvals",
        "outcomes",
        "redaction_metadata",
        "metadata",
    )
    @classmethod
    def payload_must_be_public_safe(cls, value: Any) -> Any:
        reject_secret_like_keys(value)
        _reject_hidden_payload(value)
        return value


class TraceNarrativeRequest(BaseModel):
    """Request to build a public narrative for one trace."""

    model_config = ConfigDict(extra="forbid")

    trace_narrative_id: str | None = None
    trace_id: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    include_audit: bool = True
    include_provenance: bool = True
    include_events: bool = True
    include_decisions: bool = True
    include_outcomes: bool = True
    include_approvals: bool = True
    max_timeline_items: int = Field(default=100, ge=1, le=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_public_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        _reject_hidden_payload(value)
        return value


def trace_payload_has_hidden_reasoning(value: Any) -> bool:
    """Return true when nested trace narrative payload contains hidden markers."""

    try:
        _reject_hidden_payload(value)
    except ValueError:
        return True
    return False


def _reject_hidden_payload(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_hidden_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_hidden_payload(item)
    elif isinstance(value, str):
        _reject_hidden_or_secret_text(value)


def _reject_hidden_or_secret_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in _HIDDEN_REASONING_MARKERS):
        raise ValueError("trace narratives must not expose chain-of-thought or raw prompts")
    if text_has_secret_markers(value):
        raise ValueError("trace narratives must not expose raw secrets")


__all__ = [
    "TraceNarrative",
    "TraceNarrativeRequest",
    "TraceNarrativeStatus",
    "trace_payload_has_hidden_reasoning",
]
