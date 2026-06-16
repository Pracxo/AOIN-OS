"""Self-model and limitation contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.capability_awareness import CapabilityAwarenessRecord
from aion_brain.contracts.concepts import reject_secret_like_keys

SelfModelStatus = Literal["active", "archived"]
SelfDescriptionFormat = Literal["structured", "short_text", "markdown"]
LimitationCategory = Literal[
    "configuration",
    "optional_adapter",
    "autonomy",
    "policy",
    "approval",
    "grounding",
    "confidence",
    "data_availability",
    "execution",
    "external_integration",
    "security",
    "resilience",
    "performance",
    "release",
    "generic",
]
LimitationStatus = Literal["active", "resolved", "archived", "accepted"]
LimitationSeverity = Literal["low", "medium", "high", "critical"]

_AION_FULL_NAME = "Adaptive Intelligence Orchestration Nexus"
_UNSAFE_SELF_CLAIM_MARKERS = ("sentient", "conscious", "self-aware", "self aware", "personality")
_PRODUCTION_READY_MARKERS = (
    "production ready",
    "production-ready",
    "fully autonomous",
    "full autonomy",
)
_LIMITATION_KEY_PATTERN = re.compile(r"^[a-z0-9_.]+$")


class SelfModelProfile(BaseModel):
    """A factual, descriptive profile for AION itself."""

    model_config = ConfigDict(extra="forbid")

    self_model_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: SelfModelStatus
    description: str = Field(min_length=1)
    operating_principles: list[str] = Field(min_length=1)
    architecture_refs: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("full_name")
    @classmethod
    def full_name_must_use_official_meaning(cls, value: str) -> str:
        if _AION_FULL_NAME not in value:
            raise ValueError("full_name must include Adaptive Intelligence Orchestration Nexus")
        return value

    @field_validator("description", "name")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        lowered = value.lower()
        if any(marker in lowered for marker in _UNSAFE_SELF_CLAIM_MARKERS):
            raise ValueError("self model must not claim sentience or personality")
        if any(marker in lowered for marker in _PRODUCTION_READY_MARKERS):
            raise ValueError("self model must not claim production readiness or full autonomy")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class LimitationRecord(BaseModel):
    """A factual limitation AION should disclose when relevant."""

    model_config = ConfigDict(extra="forbid")

    limitation_id: str = Field(min_length=1)
    limitation_key: str = Field(min_length=1)
    category: LimitationCategory
    status: LimitationStatus
    severity: LimitationSeverity
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    affected_capabilities: list[str] = Field(default_factory=list)
    workaround: str | None = None
    disclosure_required: bool
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("limitation_key")
    @classmethod
    def limitation_key_must_be_lowercase(cls, value: str) -> str:
        if not _LIMITATION_KEY_PATTERN.fullmatch(value):
            raise ValueError(
                "limitation_key must contain lowercase letters, digits, dot or underscore"
            )
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class LimitationCreateRequest(BaseModel):
    """Request to create one limitation ledger record."""

    model_config = ConfigDict(extra="forbid")

    limitation_id: str | None = None
    limitation_key: str = Field(min_length=1)
    category: LimitationCategory
    severity: LimitationSeverity
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    affected_capabilities: list[str] = Field(default_factory=list)
    workaround: str | None = None
    disclosure_required: bool = True
    owner_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("limitation_key")
    @classmethod
    def limitation_key_must_be_lowercase(cls, value: str) -> str:
        if not _LIMITATION_KEY_PATTERN.fullmatch(value):
            raise ValueError(
                "limitation_key must contain lowercase letters, digits, dot or underscore"
            )
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SelfDescriptionRequest(BaseModel):
    """Request a factual self-description from awareness records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    include_capabilities: bool = True
    include_limitations: bool = True
    include_architecture: bool = True
    include_status: bool = True
    format: SelfDescriptionFormat = "structured"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SelfDescription(BaseModel):
    """Factual self-description for APIs, SDKs, CLI, and dialogue."""

    model_config = ConfigDict(extra="forbid")

    name: str
    full_name: str
    version: str
    summary: str
    architecture: list[str] = Field(default_factory=list)
    capabilities: list[CapabilityAwarenessRecord] = Field(default_factory=list)
    limitations: list[LimitationRecord] = Field(default_factory=list)
    status: dict[str, Any] = Field(default_factory=dict)
    disclosures: list[str] = Field(default_factory=list)
    generated_at: datetime

    @model_validator(mode="after")
    def summary_must_be_safe(self) -> SelfDescription:
        lowered = self.summary.lower()
        if any(marker in lowered for marker in _UNSAFE_SELF_CLAIM_MARKERS):
            raise ValueError("self description must not claim sentience")
        if any(marker in lowered for marker in _PRODUCTION_READY_MARKERS):
            raise ValueError("self description must not claim production readiness")
        return self


__all__ = [
    "LimitationCategory",
    "LimitationCreateRequest",
    "LimitationRecord",
    "LimitationSeverity",
    "LimitationStatus",
    "SelfDescription",
    "SelfDescriptionFormat",
    "SelfDescriptionRequest",
    "SelfModelProfile",
    "SelfModelStatus",
]
