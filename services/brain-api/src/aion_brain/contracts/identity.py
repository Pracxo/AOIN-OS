"""Identity contracts owned by AION Brain."""

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ActorType = Literal["user", "system", "module", "service"]
ActorStatus = Literal["active", "disabled"]
WorkspaceStatus = Literal["active", "archived", "disabled"]
WorkspaceRole = Literal["owner", "admin", "operator", "viewer", "module"]
MembershipStatus = Literal["active", "revoked"]
PermissionEffect = Literal["allow", "deny"]
PermissionGrantStatus = Literal["active", "revoked"]
ResourceType = Literal[
    "brain",
    "event",
    "memory",
    "graph",
    "capability",
    "module",
    "runtime",
    "plan",
    "execution",
    "goal",
    "task",
    "schedule",
    "reflection",
    "skill",
    "trace",
    "policy",
    "evaluation",
    "learning",
    "telemetry",
    "workspace",
]

SECRET_METADATA_KEYS = {"password", "secret", "token", "api_key", "private_key"}
PERMISSION_PATTERN = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$")


class ActorRecord(BaseModel):
    """Actor metadata controlled by AION Brain."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str = Field(min_length=1)
    actor_type: ActorType
    display_name: str = Field(min_length=1)
    status: ActorStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        _reject_secret_keys(value)
        return value


class WorkspaceRecord(BaseModel):
    """Workspace metadata controlled by AION Brain."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: WorkspaceStatus
    owner_actor_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        _reject_secret_keys(value)
        return value


class WorkspaceMembership(BaseModel):
    """Actor membership in a workspace."""

    model_config = ConfigDict(extra="forbid")

    membership_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    role: WorkspaceRole
    status: MembershipStatus
    granted_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    revoked_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        _reject_secret_keys(value)
        return value


class PermissionGrant(BaseModel):
    """Generic permission grant."""

    model_config = ConfigDict(extra="forbid")

    grant_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    role: WorkspaceRole | None = None
    permission: str = Field(min_length=1)
    resource_type: ResourceType
    resource_id: str | None = None
    effect: PermissionEffect
    status: PermissionGrantStatus
    granted_by: str | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    revoked_at: datetime | None = None

    @field_validator("permission")
    @classmethod
    def permission_must_be_dotted_generic(cls, value: str) -> str:
        """Require dotted generic permissions."""
        if not PERMISSION_PATTERN.fullmatch(value):
            raise ValueError("permission must be dotted generic permission text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        _reject_secret_keys(value)
        return value

    @model_validator(mode="after")
    def grant_must_have_target(self) -> "PermissionGrant":
        """Require at least one grant target."""
        if self.actor_id is None and self.workspace_id is None and self.role is None:
            raise ValueError("permission grant requires actor_id, workspace_id, or role")
        return self


def _reject_secret_keys(value: dict[str, Any]) -> None:
    for key, item in value.items():
        if key.lower() in SECRET_METADATA_KEYS:
            raise ValueError(f"metadata must not contain secret-like key: {key}")
        if isinstance(item, dict):
            _reject_secret_keys(item)
