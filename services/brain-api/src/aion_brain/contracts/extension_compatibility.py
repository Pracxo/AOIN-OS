"""Extension compatibility gate contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.extensions import ExtensionMode
from aion_brain.contracts.model_outputs import reject_secret_like_payload

ExtensionCompatibilityRunStatus = Literal["passed", "warning", "failed", "blocked"]


class ExtensionCompatibilityRequest(BaseModel):
    """Request to check one extension package against local AION contracts."""

    model_config = ConfigDict(extra="forbid")

    extension_compatibility_id: str | None = None
    trace_id: str | None = None
    extension_package_id: str = Field(min_length=1)
    mode: ExtensionMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    contract_snapshot_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ExtensionCompatibilityRun(BaseModel):
    """Result of deterministic extension compatibility checks."""

    model_config = ConfigDict(extra="forbid")

    extension_compatibility_id: str = Field(min_length=1)
    trace_id: str | None = None
    extension_package_id: str = Field(min_length=1)
    status: ExtensionCompatibilityRunStatus
    mode: ExtensionMode
    owner_scope: list[str] = Field(min_length=1)
    contract_snapshot_id: str | None = None
    compatibility_scan_id: str | None = None
    checks: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("checks", "findings", "blockers", "warnings")
    @classmethod
    def list_payloads_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_payload(item)
        return value

    @field_validator("result", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = ["ExtensionCompatibilityRequest", "ExtensionCompatibilityRun"]
