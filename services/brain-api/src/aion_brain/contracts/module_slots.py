"""Module slot contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

ModuleSlotStatus = Literal["proposed", "staged", "validated", "blocked", "archived", "deleted"]
ModuleSlotType = Literal[
    "module",
    "adapter",
    "connector",
    "capability_pack",
    "policy_pack",
    "visualization_pack",
    "generic",
]
ModuleSlotLifecycleState = Literal[
    "metadata_only",
    "intake",
    "reviewed",
    "mount_planned",
    "activation_blocked",
    "archived",
]
ModuleSlotCompatibilityStatus = Literal["unknown", "passed", "warning", "failed", "blocked"]

_DOTTED_LOWER_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "payment",
    "procurement",
    "human_resources",
}
_ACTIVATION_MARKERS = {
    "activate",
    "activation",
    "active_capability",
    "code_loading",
    "dynamic_route",
    "install",
    "load_code",
    "mount_execute",
    "register_route",
}


class ModuleSlot(BaseModel):
    """Inactive metadata slot for a future module."""

    model_config = ConfigDict(extra="forbid")

    module_slot_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    extension_package_id: str | None = None
    slot_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ModuleSlotStatus
    slot_type: ModuleSlotType
    lifecycle_state: ModuleSlotLifecycleState
    owner_scope: list[str] = Field(min_length=1)
    compatibility_status: ModuleSlotCompatibilityStatus
    allowed_modes: list[str] = Field(default_factory=list)
    declared_capability_refs: list[str] = Field(default_factory=list)
    capability_binding_refs: list[str] = Field(default_factory=list)
    contract_refs: list[str] = Field(default_factory=list)
    policy_action_refs: list[str] = Field(default_factory=list)
    setting_refs: list[str] = Field(default_factory=list)
    sandbox_profile_id: str | None = None
    mount_plan_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("slot_key")
    @classmethod
    def slot_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("slot_key must be dotted lowercase text")
        _reject_domain_text(value)
        return value

    @field_validator("name", "description", "version")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        reject_hidden_or_secret_text(cleaned, "module slot text")
        _reject_domain_text(cleaned)
        return cleaned

    @field_validator(
        "allowed_modes",
        "declared_capability_refs",
        "capability_binding_refs",
        "contract_refs",
        "policy_action_refs",
        "setting_refs",
    )
    @classmethod
    def string_lists_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "module slot list item")
            _reject_domain_text(item)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value

    @model_validator(mode="after")
    def slot_must_remain_metadata_only(self) -> ModuleSlot:
        if _contains_activation_marker(self.metadata):
            raise ValueError("module slot must not imply activation or code loading")
        return self


class ModuleSlotCreateRequest(BaseModel):
    """Request to create an inactive module slot."""

    model_config = ConfigDict(extra="forbid")

    module_slot_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    extension_package_id: str | None = None
    slot_key: str
    name: str
    description: str
    version: str = "0.1.0"
    slot_type: ModuleSlotType = "generic"
    owner_scope: list[str] = Field(min_length=1)
    allowed_modes: list[str] = Field(default_factory=lambda: ["dry_run"])
    declared_capability_refs: list[str] = Field(default_factory=list)
    contract_refs: list[str] = Field(default_factory=list)
    policy_action_refs: list[str] = Field(default_factory=list)
    setting_refs: list[str] = Field(default_factory=list)
    sandbox_profile_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("slot_key")
    @classmethod
    def slot_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("slot_key must be dotted lowercase text")
        _reject_domain_text(value)
        return value

    @field_validator("name", "description", "version")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        reject_hidden_or_secret_text(cleaned, "module slot text")
        _reject_domain_text(cleaned)
        return cleaned

    @field_validator(
        "allowed_modes",
        "declared_capability_refs",
        "contract_refs",
        "policy_action_refs",
        "setting_refs",
    )
    @classmethod
    def string_lists_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "module slot list item")
            _reject_domain_text(item)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        if _contains_activation_marker(value):
            raise ValueError("module slot must not imply activation or code loading")
        return value


class ModuleSlotArchiveRequest(BaseModel):
    """Request to archive or delete a module slot."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "reason")
        return value


def _reject_payload(value: object) -> None:
    reject_secret_like_payload(value)
    if _contains_domain_term(value):
        raise ValueError("module slot payload must not contain domain-specific logic")


def _reject_domain_text(value: str) -> None:
    lowered = value.lower().replace("-", "_")
    if any(term in lowered for term in _BANNED_DOMAIN_TERMS):
        raise ValueError("module slot must not contain domain-specific terms")


def _contains_domain_term(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_domain_term(key) or _contains_domain_term(item) for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_domain_term(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(term in lowered for term in _BANNED_DOMAIN_TERMS)
    return False


def _contains_activation_marker(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _ACTIVATION_MARKERS and nested not in (False, None, "", [], {}):
                return True
            if _contains_activation_marker(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_activation_marker(item) for item in value)
    elif isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(marker in lowered for marker in _ACTIVATION_MARKERS)
    return False


__all__ = [
    "ModuleSlot",
    "ModuleSlotArchiveRequest",
    "ModuleSlotCreateRequest",
]
