"""Provider-neutral model input manifest contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.prompts import reject_secret_like_payload

ModelInputManifestStatus = Literal["ready", "blocked", "warning", "failed"]


class ModelInputManifest(BaseModel):
    """Provider-neutral manifest for a governed model input packet."""

    model_config = ConfigDict(extra="forbid")

    model_input_manifest_id: str = Field(min_length=1)
    trace_id: str | None = None
    prompt_packet_id: str = Field(min_length=1)
    model_route: str | None = None
    provider_type: str | None = None
    status: ModelInputManifestStatus
    input_hash: str = Field(min_length=1)
    section_count: int = Field(ge=0)
    token_estimate: int = Field(ge=0)
    context_budget: dict[str, Any] = Field(default_factory=dict)
    grounding_refs: list[str] = Field(default_factory=list)
    instruction_refs: list[str] = Field(default_factory=list)
    safety_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("provider_type")
    @classmethod
    def provider_type_must_be_generic_or_configured(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value.startswith("provider:"):
            return value
        allowed = {"deterministic", "local", "configured", "generic"}
        if value not in allowed:
            raise ValueError("provider_type must be generic or configured")
        return value

    @field_validator("context_budget", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = ["ModelInputManifest"]
