"""Counterfactual simulation contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.concepts import reject_secret_like_keys

CounterfactualMode = Literal["dry_run", "controlled"]
CounterfactualStatus = Literal[
    "completed",
    "dry_run",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
]


class CounterfactualRunRequest(BaseModel):
    """Request to project generic effects without mutating source records."""

    model_config = ConfigDict(extra="forbid")

    counterfactual_run_id: str | None = None
    decision_frame_id: str = Field(min_length=1)
    decision_option_id: str | None = None
    trace_id: str | None = None
    mode: CounterfactualMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    input_state: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    max_projected_changes: int = Field(default=25, ge=1, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("input_state", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class CounterfactualRun(BaseModel):
    """A deterministic projection of declared option effects."""

    model_config = ConfigDict(extra="forbid")

    counterfactual_run_id: str = Field(min_length=1)
    decision_frame_id: str = Field(min_length=1)
    decision_option_id: str | None = None
    trace_id: str | None = None
    status: CounterfactualStatus
    mode: CounterfactualMode
    owner_scope: list[str] = Field(min_length=1)
    input_state: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    projected_changes: list[dict[str, Any]] = Field(default_factory=list)
    projected_risks: list[dict[str, Any]] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("input_state", "result")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @field_validator("projected_changes", "projected_risks")
    @classmethod
    def lists_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_keys(value)
        return value


__all__ = [
    "CounterfactualMode",
    "CounterfactualRun",
    "CounterfactualRunRequest",
    "CounterfactualStatus",
]
