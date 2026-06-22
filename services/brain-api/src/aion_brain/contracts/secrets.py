"""Secret reference contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SecretRefStatus = Literal["active", "disabled"]
SecretType = Literal[
    "api_key_ref",
    "oauth_ref",
    "database_credential_ref",
    "token_ref",
    "certificate_ref",
    "generic_ref",
]
SecretProvider = Literal["metadata_only", "environment", "external_vault_placeholder"]
SecretSensitivity = Literal["internal", "confidential", "restricted"]

SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}
RAW_SECRET_PREFIXES = ("sk-", "sk_", "xoxb-", "ghp_", "github_pat_", "AKIA")


class SecretRef(BaseModel):
    """Metadata-only reference to secret material stored outside AION Brain."""

    model_config = ConfigDict(extra="forbid")

    secret_ref_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: SecretRefStatus
    owner_scope: list[str] = Field(min_length=1)
    secret_type: SecretType
    provider: SecretProvider
    external_ref: str | None = None
    sensitivity: SecretSensitivity
    rotation_policy: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None
    last_rotated_at: datetime | None = None

    @field_validator("external_ref")
    @classmethod
    def external_ref_must_be_reference_only(cls, value: str | None) -> str | None:
        """Reject raw-looking secret material."""
        if value is not None and looks_like_raw_secret(value):
            raise ValueError("external_ref must be a reference, not raw secret material")
        return value

    @field_validator("rotation_policy", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys and values."""
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


class SecretRefCreateRequest(BaseModel):
    """Request to create a metadata-only secret reference."""

    model_config = ConfigDict(extra="forbid")

    secret_ref_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    secret_type: SecretType
    provider: SecretProvider = "metadata_only"
    external_ref: str | None = None
    sensitivity: SecretSensitivity = "confidential"
    rotation_policy: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("external_ref")
    @classmethod
    def external_ref_must_be_reference_only(cls, value: str | None) -> str | None:
        if value is not None and looks_like_raw_secret(value):
            raise ValueError("external_ref must be a reference, not raw secret material")
        return value

    @field_validator("rotation_policy", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


def reject_secret_like_keys(value: object) -> None:
    """Raise when nested dictionaries contain secret-like keys."""
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SECRET_KEY_PARTS):
                raise ValueError("payload must not contain secret-like keys")
            reject_secret_like_keys(nested)
    elif isinstance(value, list):
        for item in value:
            reject_secret_like_keys(item)


def reject_secret_like_values(value: object) -> None:
    """Raise when nested string values look like raw secret material."""
    if isinstance(value, dict):
        for nested in value.values():
            reject_secret_like_values(nested)
    elif isinstance(value, list):
        for item in value:
            reject_secret_like_values(item)
    elif isinstance(value, str) and looks_like_raw_secret(value):
        raise ValueError("payload must not contain raw secret-like values")


def looks_like_raw_secret(value: str) -> bool:
    """Return whether a string resembles raw credential material."""
    stripped = value.strip()
    lowered = stripped.lower()
    if not stripped:
        return False
    if any(stripped.startswith(prefix) for prefix in RAW_SECRET_PREFIXES):
        return True
    if any(marker in lowered for marker in ("password=", "secret=", "token=", "api_key=")):
        return True
    if lowered.startswith(("bearer ", "basic ")):
        return True
    if len(stripped) >= 40 and not any(sep in stripped for sep in (":", "/", ".")):
        return True
    return False


__all__ = [
    "SecretRef",
    "SecretRefCreateRequest",
    "looks_like_raw_secret",
    "reject_secret_like_keys",
    "reject_secret_like_values",
]
