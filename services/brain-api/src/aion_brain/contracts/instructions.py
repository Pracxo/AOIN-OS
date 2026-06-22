"""Instruction hierarchy contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.concepts import reject_secret_like_keys, text_has_secret_markers

InstructionType = Literal[
    "response_style",
    "task_instruction",
    "session_instruction",
    "workspace_instruction",
    "operator_instruction",
    "clarification_instruction",
    "memory_instruction",
    "retrieval_instruction",
    "planning_instruction",
    "constraint",
    "system",
    "session",
    "task",
    "workflow",
    "workspace",
    "actor_preference",
    "learned_candidate",
    "runtime",
    "policy",
    "capability",
    "safety",
    "style",
    "grounding",
    "memory",
    "response",
    "generic",
]
InstructionSourceType = Literal[
    "user",
    "operator",
    "dialogue",
    "task",
    "workflow",
    "runtime_config",
    "policy",
    "self_model",
    "memory",
    "learning",
    "system_config",
    "current_session",
    "generic",
]
InstructionScopeType = Literal[
    "global",
    "workspace",
    "actor",
    "dialogue_session",
    "session",
    "task",
    "workflow",
    "trace",
    "request",
]
InstructionStatus = Literal["active", "disabled", "expired", "superseded", "rejected"]
ConstraintType = Literal[
    "policy",
    "autonomy",
    "risk",
    "approval",
    "runtime_config",
    "runtime",
    "capability",
    "sandbox",
    "response",
    "memory",
    "grounding",
    "instruction",
    "preference",
    "style",
    "generic",
]
ConstraintStatus = Literal["active", "disabled", "expired", "superseded"]
InstructionConflictType = Literal[
    "policy_override_attempt",
    "autonomy_override_attempt",
    "approval_bypass_attempt",
    "style_conflict",
    "memory_conflict",
    "grounding_conflict",
    "unsupported_instruction",
    "expired_instruction",
    "duplicate_instruction",
    "policy_override",
    "approval_bypass",
    "autonomy_override",
    "runtime_override",
    "capability_override",
    "sandbox_override",
    "grounding_conflict",
    "memory_conflict",
    "duplicate",
    "contradiction",
    "generic",
]
InstructionConflictStatus = Literal["open", "resolved", "dismissed"]
InstructionSeverity = Literal["low", "medium", "high", "critical"]
StyleProfileStatus = Literal["active", "disabled"]
InstructionResolutionStatus = Literal["completed", "warning", "blocked_by_policy", "failed"]

_HIDDEN_REASONING_MARKERS = (
    "chain_of_thought",
    "chain-of-thought",
    "chain of thought",
    "hidden_reasoning",
    "hidden reasoning",
    "private reasoning",
    "show your reasoning",
    "internal reasoning",
    "raw_prompt",
    "raw prompt",
)
_DOTTED_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_FORBIDDEN_OVERRIDE_MARKERS = (
    "ignore policy",
    "override policy",
    "bypass policy",
    "disable policy",
    "bypass approval",
    "skip approval",
    "ignore approval",
    "override approval",
    "disable autonomy",
    "override autonomy",
    "ignore autonomy",
    "ignore runtime config",
    "override runtime config",
    "ignore sandbox",
    "bypass sandbox",
    "ignore capability limits",
    "bypass capability",
    "show chain of thought",
    "reveal chain of thought",
    "show hidden reasoning",
    "reveal hidden reasoning",
    "expose secrets",
    "show secrets",
)


class InstructionCreateRequest(BaseModel):
    """Request to create one normalized instruction."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    instruction_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    instruction_text: str = Field(min_length=1)
    instruction_type: InstructionType = "generic"
    source_type: InstructionSourceType = "user"
    source_id: str | None = None
    scope_type: InstructionScopeType = "actor"
    owner_scope: list[str] = Field(min_length=1)
    priority: int = Field(default=500, ge=0, le=1000)
    expires_at: datetime | None = None
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("instruction_text")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_unsafe_instruction_text(value)
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value

    def to_record(self, instruction_id: str, normalized_instruction: str) -> InstructionRecord:
        """Convert to the canonical stored instruction record."""

        return InstructionRecord(
            instruction_id=instruction_id,
            trace_id=self.trace_id,
            actor_id=self.actor_id,
            workspace_id=self.workspace_id,
            instruction_text=self.instruction_text,
            normalized_instruction=normalized_instruction,
            instruction_type=self.instruction_type,
            source_type=self.source_type,
            source_id=self.source_id,
            scope_type=self.scope_type,
            owner_scope=self.owner_scope,
            priority=self.priority,
            status="active",
            expires_at=self.expires_at,
            constraints=self.constraints,
            metadata=self.metadata,
            created_by=self.created_by,
        )


class InstructionRecord(BaseModel):
    """One normalized instruction controlled by AION's hierarchy."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    instruction_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    instruction_text: str = Field(
        min_length=1,
        validation_alias=AliasChoices("instruction_text", "content"),
    )
    normalized_instruction: str | None = Field(
        default=None,
        validation_alias=AliasChoices("normalized_instruction", "normalized_content"),
    )
    instruction_type: InstructionType = "generic"
    source_type: InstructionSourceType = Field(
        default="generic",
        validation_alias=AliasChoices("source_type", "source"),
    )
    source_id: str | None = None
    scope_type: InstructionScopeType = "workspace"
    owner_scope: list[str] = Field(min_length=1)
    priority: int = Field(
        default=500,
        ge=0,
        le=1000,
        validation_alias=AliasChoices("priority", "priority_level"),
    )
    status: InstructionStatus = "active"
    expires_at: datetime | None = None
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None
    effective_from: datetime | None = Field(default=None, exclude=True)
    precedence_rank: int | None = Field(default=None, ge=1, le=10, exclude=True)

    @property
    def content(self) -> str:
        """Backward-compatible internal alias."""

        return self.instruction_text

    @property
    def normalized_content(self) -> str | None:
        """Backward-compatible internal alias."""

        return self.normalized_instruction

    @property
    def priority_level(self) -> int:
        """Backward-compatible internal alias."""

        return self.priority

    @property
    def source(self) -> str:
        """Backward-compatible internal alias."""

        return self.source_type

    @field_validator("instruction_text")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        reject_unsafe_instruction_text(value)
        return value.strip()

    @field_validator("normalized_instruction")
    @classmethod
    def normalized_instruction_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_unsafe_instruction_text(value)
            return value.strip()
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value

    @model_validator(mode="after")
    def validate_expiry_range(self) -> InstructionRecord:
        if self.effective_from and self.expires_at and self.effective_from >= self.expires_at:
            raise ValueError("effective_from must be before expires_at")
        return self


class ConstraintRecord(BaseModel):
    """A hard or soft constraint available to the instruction resolver."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    constraint_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    constraint_key: str = Field(min_length=1)
    constraint_type: ConstraintType = "generic"
    status: ConstraintStatus = "active"
    severity: InstructionSeverity = "medium"
    description: str = Field(default="Generic instruction constraint.", min_length=1)
    rule: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("rule", "constraint_value"),
    )
    source_type: InstructionSourceType = Field(
        default="generic",
        validation_alias=AliasChoices("source_type", "source"),
    )
    source_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None
    immutable: bool = Field(default=False, exclude=True)

    @property
    def constraint_value(self) -> dict[str, Any]:
        """Backward-compatible internal alias."""

        return self.rule

    @property
    def source(self) -> str:
        """Backward-compatible internal alias."""

        return self.source_type

    @field_validator("constraint_key")
    @classmethod
    def key_must_be_normalized(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _DOTTED_KEY_RE.fullmatch(normalized):
            raise ValueError("constraint_key must be lowercase dotted text")
        return normalized

    @field_validator("description")
    @classmethod
    def description_must_be_safe(cls, value: str) -> str:
        reject_unsafe_instruction_text(value, allow_override_markers=True)
        return value.strip()

    @field_validator("rule", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class StyleProfileCreateRequest(BaseModel):
    """Request to create a style profile."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    style_profile_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    style_rules: dict[str, Any] = Field(default_factory=dict)
    formatting_rules: dict[str, Any] = Field(default_factory=dict)
    tone_rules: dict[str, Any] = Field(default_factory=dict)
    prohibited_patterns: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_unsafe_instruction_text(value, allow_override_markers=True)
        return value.strip()

    @field_validator("style_rules", "formatting_rules", "tone_rules", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value

    @field_validator("prohibited_patterns")
    @classmethod
    def patterns_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_unsafe_instruction_text(item, allow_override_markers=True)
        return [item.strip() for item in value]

    def to_profile(self, style_profile_id: str) -> StyleProfile:
        """Convert to the canonical stored style profile."""

        return StyleProfile(
            style_profile_id=style_profile_id,
            name=self.name,
            description=self.description,
            actor_id=self.actor_id,
            workspace_id=self.workspace_id,
            owner_scope=self.owner_scope,
            style_rules=self.style_rules,
            formatting_rules=self.formatting_rules,
            tone_rules=self.tone_rules,
            prohibited_patterns=self.prohibited_patterns,
            metadata=self.metadata,
            created_by=self.created_by,
        )


class StyleProfile(BaseModel):
    """Actor or workspace response style profile below hard constraints."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    style_profile_id: str = Field(min_length=1)
    trace_id: str | None = None
    name: str = Field(min_length=1, validation_alias=AliasChoices("name", "profile_name"))
    description: str = "Generic response style profile."
    status: StyleProfileStatus = "active"
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    style_rules: dict[str, Any] = Field(default_factory=dict)
    formatting_rules: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("formatting_rules", "formatting"),
    )
    tone_rules: dict[str, Any] = Field(default_factory=dict)
    prohibited_patterns: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("prohibited_patterns", "response_rules"),
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None
    tone: str | None = Field(default=None, exclude=True)
    verbosity: str | None = Field(default=None, exclude=True)

    @property
    def profile_name(self) -> str:
        """Backward-compatible internal alias."""

        return self.name

    @property
    def formatting(self) -> dict[str, Any]:
        """Backward-compatible internal alias."""

        return self.formatting_rules

    @property
    def response_rules(self) -> list[str]:
        """Backward-compatible internal alias."""

        return self.prohibited_patterns

    @field_validator("name", "description", "tone", "verbosity")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_unsafe_instruction_text(value, allow_override_markers=True)
            return value.strip()
        return value

    @field_validator("prohibited_patterns")
    @classmethod
    def rules_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_unsafe_instruction_text(item, allow_override_markers=True)
        return [item.strip() for item in value]

    @field_validator("style_rules", "formatting_rules", "tone_rules", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value


class InstructionConflict(BaseModel):
    """A detected conflict between instruction, preference, and constraint records."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    conflict_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    conflict_type: InstructionConflictType
    severity: InstructionSeverity = "medium"
    status: InstructionConflictStatus = "open"
    instruction_ids: list[str] = Field(default_factory=list)
    preference_ids: list[str] = Field(default_factory=list)
    constraint_ids: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1, validation_alias=AliasChoices("reason", "description"))
    resolution: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @property
    def description(self) -> str:
        """Backward-compatible internal alias."""

        return self.reason

    @field_validator("reason", "resolution")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_unsafe_instruction_text(value, allow_override_markers=True)
            return value.strip()
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class InstructionResolutionRequest(BaseModel):
    """Request to resolve effective instructions under AION precedence."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    resolution_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    dialogue_session_id: str | None = None
    task_id: str | None = None
    workflow_run_id: str | None = None
    request_text: str | None = None
    include_preferences: bool = True
    include_style: bool = True
    include_constraints: bool = True
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata", "context"),
    )
    created_by: str | None = None
    current_session_instructions: list[str] = Field(default_factory=list, exclude=True)
    task_instructions: list[str] = Field(default_factory=list, exclude=True)
    workflow_instructions: list[str] = Field(default_factory=list, exclude=True)
    workspace_instructions: list[str] = Field(default_factory=list, exclude=True)
    instruction_ids: list[str] = Field(default_factory=list, exclude=True)
    preference_ids: list[str] = Field(default_factory=list, exclude=True)
    include_candidate_preferences: bool = Field(default=False, exclude=True)
    include_disabled: bool = Field(default=False, exclude=True)

    @field_validator(
        "current_session_instructions",
        "task_instructions",
        "workflow_instructions",
        "workspace_instructions",
    )
    @classmethod
    def instructions_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_unsafe_instruction_text(item)
        return [item.strip() for item in value]

    @field_validator("request_text")
    @classmethod
    def request_text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_unsafe_instruction_text(value, allow_override_markers=True)
            return value.strip()
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_forbidden_override_payload(value)
        return value


class InstructionResolutionResult(BaseModel):
    """Effective instruction packet after hierarchy and conflict resolution."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    resolution_run_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("resolution_run_id", "resolution_id"),
    )
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: InstructionResolutionStatus = "completed"
    owner_scope: list[str] = Field(min_length=1)
    applied_instruction_ids: list[str] = Field(default_factory=list)
    applied_preference_ids: list[str] = Field(default_factory=list)
    applied_constraint_ids: list[str] = Field(default_factory=list)
    suppressed_instruction_ids: list[str] = Field(default_factory=list)
    conflicts: list[InstructionConflict] = Field(default_factory=list)
    effective_instructions: list[str] = Field(default_factory=list)
    effective_style: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    suppressed: list[dict[str, Any]] = Field(default_factory=list, exclude=True)
    precedence_order: list[str] = Field(default_factory=list, exclude=True)

    @property
    def resolution_id(self) -> str:
        """Backward-compatible internal alias."""

        return self.resolution_run_id


def text_has_hidden_reasoning_markers(value: str) -> bool:
    """Return true when text asks for hidden reasoning or raw prompts."""

    lowered = value.lower()
    return any(marker in lowered for marker in _HIDDEN_REASONING_MARKERS)


def text_has_forbidden_override_markers(value: str) -> bool:
    """Return true when text tries to bypass AION hard boundaries."""

    lowered = value.lower()
    return any(marker in lowered for marker in _FORBIDDEN_OVERRIDE_MARKERS)


def reject_unsafe_instruction_text(
    value: str,
    *,
    allow_override_markers: bool = False,
) -> None:
    """Reject unsafe instruction text."""

    if not value.strip():
        raise ValueError("instruction text cannot be empty")
    if text_has_secret_markers(value):
        raise ValueError("instruction text must not contain raw secrets")
    if text_has_hidden_reasoning_markers(value):
        raise ValueError("instruction text must not request hidden reasoning")
    if not allow_override_markers and text_has_forbidden_override_markers(value):
        raise ValueError("instruction text must not override policy or safety boundaries")


def reject_forbidden_override_payload(value: Any) -> None:
    """Reject nested payload values that contain forbidden override attempts."""

    if isinstance(value, dict):
        for key, item in value.items():
            if text_has_forbidden_override_markers(str(key)):
                raise ValueError("payload contains forbidden override key")
            reject_forbidden_override_payload(item)
    elif isinstance(value, list):
        for item in value:
            reject_forbidden_override_payload(item)
    elif isinstance(value, str) and text_has_forbidden_override_markers(value):
        raise ValueError("payload contains forbidden override value")


__all__ = [
    "ConstraintRecord",
    "ConstraintStatus",
    "ConstraintType",
    "InstructionConflict",
    "InstructionConflictStatus",
    "InstructionConflictType",
    "InstructionCreateRequest",
    "InstructionRecord",
    "InstructionResolutionRequest",
    "InstructionResolutionResult",
    "InstructionResolutionStatus",
    "InstructionScopeType",
    "InstructionSeverity",
    "InstructionSourceType",
    "InstructionStatus",
    "InstructionType",
    "StyleProfile",
    "StyleProfileCreateRequest",
    "StyleProfileStatus",
    "reject_forbidden_override_payload",
    "reject_unsafe_instruction_text",
    "text_has_forbidden_override_markers",
    "text_has_hidden_reasoning_markers",
]
