"""Capability awareness contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.concepts import reject_secret_like_keys

CapabilityAwarenessType = Literal[
    "kernel",
    "memory",
    "evidence",
    "retrieval",
    "reasoning",
    "planning",
    "execution",
    "workflow",
    "module",
    "mcp",
    "sandbox",
    "policy",
    "autonomy",
    "risk",
    "approval",
    "dialogue",
    "response",
    "belief",
    "entity",
    "situation",
    "decision",
    "outcome",
    "learning",
    "operator",
    "audit",
    "visual",
    "backup",
    "release",
    "performance",
    "security",
    "resilience",
    "runtime_config",
    "sdk",
    "cli",
    "optional_adapter",
    "generic",
]
CapabilityAwarenessStatus = Literal[
    "active",
    "disabled",
    "unavailable",
    "degraded",
    "dry_run_only",
    "unknown",
]
CapabilityAvailability = Literal[
    "available",
    "unavailable",
    "optional_unavailable",
    "disabled_by_config",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "requires_setup",
    "unknown",
]
CapabilityAwarenessMode = Literal[
    "observe",
    "assist",
    "plan_only",
    "dry_run",
    "controlled",
    "metadata_only",
]
CapabilityRiskLevel = Literal["low", "medium", "high", "critical"]


class CapabilityAwarenessRecord(BaseModel):
    """Descriptive record of one capability and its current safe availability."""

    model_config = ConfigDict(extra="forbid")

    awareness_id: str = Field(min_length=1)
    capability_key: str = Field(min_length=1)
    capability_type: CapabilityAwarenessType
    status: CapabilityAwarenessStatus
    availability: CapabilityAvailability
    mode: CapabilityAwarenessMode
    risk_level: CapabilityRiskLevel
    requires_policy: bool
    requires_approval: bool
    requires_autonomy: bool
    dry_run_only: bool
    source_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


__all__ = [
    "CapabilityAvailability",
    "CapabilityAwarenessMode",
    "CapabilityAwarenessRecord",
    "CapabilityAwarenessStatus",
    "CapabilityAwarenessType",
    "CapabilityRiskLevel",
]
