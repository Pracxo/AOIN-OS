"""Release baseline contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.scenarios import reject_secret_like_keys

ReleaseBaselineStatus = Literal["passed", "failed", "warning"]


class ReleaseBaselineRequest(BaseModel):
    """Request to run the deterministic v0.1 release baseline."""

    model_config = ConfigDict(extra="forbid")

    release_baseline_id: str | None = None
    version: str = Field(min_length=1)
    owner_scope: list[str] = Field(default_factory=list)
    scenario_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=lambda: ["release_baseline"])
    include_quality_gates: bool = True
    include_kernel_self_test: bool = True
    include_policy_coverage: bool = True
    include_openapi_hygiene: bool = True
    include_boundary_check: bool = True
    include_contract_export: bool = True
    fail_fast: bool = False
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def version_cannot_be_blank(cls, value: str) -> str:
        """Reject blank release versions."""
        if not value.strip():
            raise ValueError("version cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        reject_secret_like_keys(value)
        return value


class ReleaseBaselineReport(BaseModel):
    """Persisted deterministic release baseline report."""

    model_config = ConfigDict(extra="forbid")

    release_baseline_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ReleaseBaselineStatus
    scenario_run_ids: list[str] = Field(default_factory=list)
    quality_gate_results: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
