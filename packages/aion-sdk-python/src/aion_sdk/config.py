"""Client configuration for public AION Brain APIs."""

from __future__ import annotations

import os
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class AIONClientConfig(BaseModel):
    """Configuration used by `AIONClient` and `aionctl`.

    The development identity fields map to AION Brain dev headers. This SDK does
    not carry bearer tokens or production authentication material.
    """

    model_config = ConfigDict(extra="forbid")

    base_url: str = "http://localhost:8080"
    timeout_seconds: float = Field(default=30.0, gt=0)
    actor_id: str | None = None
    workspace_id: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    security_scope: list[str] = Field(default_factory=list)
    trace_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    user_agent: str = "aion-sdk-python/0.1.0"

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        stripped = value.strip().rstrip("/")
        if not stripped:
            raise ValueError("base_url cannot be empty")
        if not stripped.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return stripped

    @field_validator("roles", "permissions", "security_scope")
    @classmethod
    def remove_empty_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @classmethod
    def from_env(cls) -> Self:
        """Build config from AION_* environment variables."""

        timeout = os.environ.get("AION_TIMEOUT_SECONDS")
        data: dict[str, Any] = {
            "base_url": os.environ.get("AION_BASE_URL", "http://localhost:8080"),
            "actor_id": os.environ.get("AION_ACTOR_ID"),
            "workspace_id": os.environ.get("AION_WORKSPACE_ID"),
            "roles": _csv(os.environ.get("AION_ROLES")),
            "permissions": _csv(os.environ.get("AION_PERMISSIONS")),
            "security_scope": _csv(os.environ.get("AION_SECURITY_SCOPE")),
            "trace_id": os.environ.get("AION_TRACE_ID"),
            "correlation_id": os.environ.get("AION_CORRELATION_ID"),
            "idempotency_key": os.environ.get("AION_IDEMPOTENCY_KEY"),
        }
        if timeout is not None and timeout.strip():
            data["timeout_seconds"] = float(timeout)
        return cls(**data)

    def with_overrides(
        self,
        *,
        base_url: str | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        security_scope: list[str] | None = None,
        trace_id: str | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> Self:
        """Return a copy with explicit CLI or caller overrides applied."""

        updates: dict[str, object] = {}
        for key, value in {
            "base_url": base_url,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
            "roles": roles,
            "permissions": permissions,
            "security_scope": security_scope,
            "trace_id": trace_id,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
        }.items():
            if value is not None:
                updates[key] = value
        return self.model_copy(update=updates)
