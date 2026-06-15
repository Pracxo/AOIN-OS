"""Connector metadata contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.secrets import (
    looks_like_raw_secret,
    reject_secret_like_keys,
    reject_secret_like_values,
)

ConnectorStatus = Literal["active", "disabled"]
ConnectorType = Literal[
    "http_placeholder",
    "database_placeholder",
    "filesystem_placeholder",
    "message_bus_placeholder",
    "generic_placeholder",
]
ConnectorRiskLevel = Literal["low", "medium", "high", "critical"]


class ConnectorDefinition(BaseModel):
    """Metadata-only connector definition for future sandboxed use."""

    model_config = ConfigDict(extra="forbid")

    connector_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ConnectorStatus
    connector_type: ConnectorType
    owner_scope: list[str] = Field(min_length=1)
    base_endpoint_ref: str | None = None
    auth_secret_ref_id: str | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    allowed_scopes: list[str] = Field(default_factory=list)
    risk_level: ConnectorRiskLevel
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("base_endpoint_ref")
    @classmethod
    def endpoint_ref_must_be_safe(cls, value: str | None) -> str | None:
        """Endpoint refs are references only; never raw credentials."""
        if value is not None and looks_like_raw_secret(value):
            raise ValueError("base_endpoint_ref must not contain raw secret material")
        return value

    @field_validator("allowed_actions")
    @classmethod
    def actions_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject vertical connector action names."""
        _reject_domain_terms(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


class ConnectorCreateRequest(BaseModel):
    """Request to create a metadata-only connector definition."""

    model_config = ConfigDict(extra="forbid")

    connector_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    connector_type: ConnectorType
    owner_scope: list[str] = Field(min_length=1)
    base_endpoint_ref: str | None = None
    auth_secret_ref_id: str | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    allowed_scopes: list[str] = Field(default_factory=list)
    risk_level: ConnectorRiskLevel = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("base_endpoint_ref")
    @classmethod
    def endpoint_ref_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None and looks_like_raw_secret(value):
            raise ValueError("base_endpoint_ref must not contain raw secret material")
        return value

    @field_validator("allowed_actions")
    @classmethod
    def actions_must_be_generic(cls, value: list[str]) -> list[str]:
        _reject_domain_terms(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "hr",
    "procurement",
    "payments",
}


def _reject_domain_terms(values: list[str]) -> None:
    for value in values:
        normalized = value.lower().replace("_", ".").replace("-", ".")
        if any(f".{term}." in f".{normalized}." for term in DOMAIN_TERMS):
            raise ValueError("connector actions must remain domain-neutral")


__all__ = ["ConnectorCreateRequest", "ConnectorDefinition"]
