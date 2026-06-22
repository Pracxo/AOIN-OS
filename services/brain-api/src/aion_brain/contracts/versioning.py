"""Version manifest and feature registry contracts."""

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ReleaseChannel = Literal["dev", "alpha", "beta", "rc", "stable"]
VersionManifestStatus = Literal["draft", "active", "frozen", "deprecated"]
FeatureStatus = Literal["active", "disabled", "deprecated"]
FeatureCategory = Literal[
    "kernel",
    "api",
    "memory",
    "graph",
    "evidence",
    "retrieval",
    "reasoning",
    "planning",
    "execution",
    "workflow",
    "autonomy",
    "policy",
    "risk",
    "approval",
    "module",
    "mcp",
    "sandbox",
    "visual",
    "sdk",
    "cli",
    "observability",
    "replay",
    "regression",
    "scenario",
    "release",
]

_FEATURE_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:[._][a-z][a-z0-9_]*)*$")
_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "payment",
    "procurement",
    "security",
}


class VersionManifest(BaseModel):
    """Versioned release manifest for AION Brain."""

    model_config = ConfigDict(extra="forbid")

    version_manifest_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    release_channel: ReleaseChannel
    status: VersionManifestStatus
    api_version: str = Field(min_length=1)
    sdk_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    contract_hash: str = Field(min_length=1)
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    adapter_matrix: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like manifest metadata."""
        reject_secret_like_keys(value)
        return value


class FeatureRegistryEntry(BaseModel):
    """A versioned feature in AION's generic feature registry."""

    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(min_length=1)
    feature_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: FeatureStatus
    category: FeatureCategory
    default_enabled: bool
    required: bool
    owner_scope: list[str] = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deprecated_at: datetime | None = None

    @field_validator("feature_key")
    @classmethod
    def feature_key_must_be_generic(cls, value: str) -> str:
        """Require lowercase generic feature keys."""
        if not _FEATURE_KEY_PATTERN.match(value):
            raise ValueError("feature_key must be lowercase dotted text")
        reject_domain_text(value)
        return value

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank feature text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("dependencies")
    @classmethod
    def dependencies_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject domain-specific feature dependencies."""
        for dependency in value:
            reject_domain_text(dependency)
        return value

    @field_validator("metadata")
    @classmethod
    def feature_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like feature metadata."""
        reject_secret_like_keys(value)
        return value


class DeprecationPolicy(BaseModel):
    """Versioned deprecation policy metadata."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    rules: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    @field_validator("rules")
    @classmethod
    def rules_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject secret-like rule metadata."""
        for rule in value:
            reject_secret_like_keys(rule)
        return value


def reject_secret_like_keys(value: dict[str, Any]) -> None:
    """Reject secret-like keys anywhere inside a dictionary."""
    for key, item in value.items():
        lowered = str(key).lower()
        if any(part in lowered for part in _SECRET_KEY_PARTS):
            raise ValueError("payload must not contain secret-like keys")
        if isinstance(item, dict):
            reject_secret_like_keys(item)
        elif isinstance(item, list):
            for element in item:
                if isinstance(element, dict):
                    reject_secret_like_keys(element)


def reject_domain_text(value: str) -> None:
    """Reject vertical/domain-specific terms in versioning metadata."""
    lowered = value.lower()
    if any(term in lowered for term in _BANNED_DOMAIN_TERMS):
        raise ValueError("versioning metadata must remain domain-neutral")
