"""Prompt packet and model input governance contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PromptSectionType = Literal[
    "system_boundary",
    "self_model",
    "policy_constraints",
    "autonomy_constraints",
    "risk_constraints",
    "approval_constraints",
    "instruction_resolution",
    "user_message",
    "dialogue_history",
    "retrieved_context",
    "evidence",
    "memory",
    "belief",
    "entity",
    "situation",
    "decision",
    "outcome",
    "grounding",
    "citation",
    "tool_manifest",
    "response_format",
    "developer_note",
    "generic",
]
PromptTrustLevel = Literal[
    "system",
    "policy",
    "operator",
    "user",
    "evidence",
    "belief_supported",
    "memory_recall",
    "retrieved_context",
    "untrusted_context",
    "generated",
    "unknown",
]
PromptTemplateStatus = Literal["active", "disabled"]
PromptTemplateType = Literal[
    "reasoning",
    "planning",
    "response",
    "explanation",
    "summarization",
    "verification",
    "model_gateway",
    "generic",
]
PromptFragmentType = Literal[
    "system_boundary",
    "response_format",
    "grounding_instruction",
    "self_description",
    "limitation_disclosure",
    "style_instruction",
    "citation_instruction",
    "verification_instruction",
    "generic",
]
PromptPacketType = Literal[
    "reasoning",
    "planning",
    "response",
    "explanation",
    "verification",
    "model_gateway",
    "dry_run",
    "generic",
]
PromptPacketStatus = Literal["compiled", "blocked", "warning", "failed", "archived"]
PromptBoundaryStatus = Literal["passed", "warning", "failed", "blocked"]
PromptInjectionFindingType = Literal[
    "instruction_override_attempt",
    "policy_override_attempt",
    "autonomy_override_attempt",
    "approval_bypass_attempt",
    "tool_injection_attempt",
    "data_exfiltration_attempt",
    "hidden_prompt_request",
    "chain_of_thought_request",
    "secret_request",
    "source_confusion",
    "untrusted_context_instruction",
    "generic",
]
PromptInjectionSeverity = Literal["low", "medium", "high", "critical"]
PromptInjectionStatus = Literal["open", "resolved", "dismissed"]
PromptPreviewRedactionLevel = Literal["safe", "metadata_only", "hashes_only"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
_HIDDEN_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
    "raw prompt",
    "system prompt:",
    "developer prompt:",
)
_PROVIDER_MARKERS = (
    "<|system|>",
    "<|assistant|>",
    "<|developer|>",
    "[system]",
    "[developer]",
)


def reject_secret_like_payload(value: object) -> None:
    """Reject direct secret-like keys or values in public prompt contracts."""

    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError("payload must not contain secret-like keys")
            reject_secret_like_payload(nested)
    elif isinstance(value, list):
        for item in value:
            reject_secret_like_payload(item)
    elif isinstance(value, str):
        reject_hidden_or_secret_text(value, "payload")


def reject_hidden_or_secret_text(value: str, field_name: str) -> None:
    """Reject hidden reasoning, raw prompts, and obvious secret values."""

    lowered = value.lower()
    if any(marker in lowered for marker in _HIDDEN_MARKERS):
        raise ValueError(f"{field_name} must not contain hidden reasoning or raw prompt markers")
    if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
        raise ValueError(f"{field_name} must not contain secret-like values")


class PromptSection(BaseModel):
    """One ordered section in a provider-neutral prompt packet."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    section_type: PromptSectionType
    title: str = Field(min_length=1)
    content: str
    priority: int = Field(ge=0, le=1000)
    source_type: str | None = None
    source_id: str | None = None
    trust_level: PromptTrustLevel
    required: bool
    redacted: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "content")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def untrusted_context_cannot_be_boundary(self) -> PromptSection:
        if self.trust_level == "untrusted_context" and self.section_type == "system_boundary":
            raise ValueError("untrusted_context cannot override system_boundary")
        return self


class PromptTemplate(BaseModel):
    """Reusable provider-neutral prompt template."""

    model_config = ConfigDict(extra="forbid")

    prompt_template_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: PromptTemplateStatus
    template_type: PromptTemplateType
    version: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    sections: list[PromptSection] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PromptTemplateCreateRequest(BaseModel):
    """Request to create a prompt template."""

    model_config = ConfigDict(extra="forbid")

    prompt_template_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    template_type: PromptTemplateType = "generic"
    version: str = Field(default="0.1.0", min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    sections: list[PromptSection] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PromptFragment(BaseModel):
    """Reusable provider-neutral prompt fragment."""

    model_config = ConfigDict(extra="forbid")

    prompt_fragment_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: PromptTemplateStatus
    fragment_type: PromptFragmentType
    content: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "content")
        lowered = value.lower()
        if any(marker in lowered for marker in _PROVIDER_MARKERS):
            raise ValueError("content must not include provider-specific hidden prompt syntax")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PromptFragmentCreateRequest(BaseModel):
    """Request to create a prompt fragment."""

    model_config = ConfigDict(extra="forbid")

    prompt_fragment_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    fragment_type: PromptFragmentType = "generic"
    content: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("content")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        PromptFragment(
            prompt_fragment_id="validation",
            name="validation",
            description="validation",
            status="active",
            fragment_type="generic",
            content=value,
            content_hash="validation",
            owner_scope=["validation"],
        )
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PromptInjectionFinding(BaseModel):
    """Deterministic prompt injection detection result."""

    model_config = ConfigDict(extra="forbid")

    injection_finding_id: str = Field(min_length=1)
    trace_id: str | None = None
    prompt_packet_id: str | None = None
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    finding_type: PromptInjectionFindingType
    severity: PromptInjectionSeverity
    status: PromptInjectionStatus
    matched_text_redacted: str
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("matched_text_redacted")
    @classmethod
    def matched_text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "matched_text_redacted")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PromptBoundaryCheck(BaseModel):
    """Boundary safety check for prompt sections or packets."""

    model_config = ConfigDict(extra="forbid")

    boundary_check_id: str = Field(min_length=1)
    trace_id: str | None = None
    prompt_packet_id: str | None = None
    status: PromptBoundaryStatus
    safe: bool
    injection_findings: list[PromptInjectionFinding] = Field(default_factory=list)
    blocked_sections: list[str] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PromptPacket(BaseModel):
    """Compiled provider-neutral model input packet."""

    model_config = ConfigDict(extra="forbid")

    prompt_packet_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: PromptPacketStatus
    packet_type: PromptPacketType
    prompt_template_id: str | None = None
    target_model_route: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    input_refs: list[str] = Field(default_factory=list)
    sections: list[PromptSection] = Field(default_factory=list)
    section_manifests: list[dict[str, Any]] = Field(default_factory=list)
    rendered_hash: str = Field(min_length=1)
    redacted_preview: str | None = None
    token_estimate: int = Field(ge=0)
    char_count: int = Field(ge=0)
    boundary_check_id: str | None = None
    grounding_verification_id: str | None = None
    instruction_resolution_id: str | None = None
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("redacted_preview")
    @classmethod
    def preview_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "redacted_preview")
        return value

    @field_validator("metadata", "section_manifests")
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value


class PromptCompileRequest(BaseModel):
    """Request to compile a governed prompt packet."""

    model_config = ConfigDict(extra="forbid")

    prompt_packet_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    packet_type: PromptPacketType = "generic"
    prompt_template_id: str | None = None
    target_model_route: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    user_message: str | None = None
    context_packet_id: str | None = None
    dialogue_session_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    instruction_resolution_id: str | None = None
    grounding_verification_id: str | None = None
    sections: list[PromptSection] = Field(default_factory=list)
    max_chars: int = Field(default=12000, ge=1000, le=200000)
    include_redacted_preview: bool = True
    store_packet: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("user_message")
    @classmethod
    def user_message_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "user_message")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PromptPreviewRequest(BaseModel):
    """Request a safe prompt preview."""

    model_config = ConfigDict(extra="forbid")

    prompt_packet_id: str | None = None
    compile_request: PromptCompileRequest | None = None
    owner_scope: list[str] = Field(min_length=1)
    redaction_level: PromptPreviewRedactionLevel = "safe"

    @model_validator(mode="after")
    def packet_or_compile_request_required(self) -> PromptPreviewRequest:
        if not (self.prompt_packet_id or self.compile_request):
            raise ValueError("prompt_packet_id or compile_request is required")
        return self


class PromptPreview(BaseModel):
    """Safe redacted prompt preview."""

    model_config = ConfigDict(extra="forbid")

    preview_id: str = Field(min_length=1)
    prompt_packet_id: str | None = None
    redaction_level: PromptPreviewRedactionLevel
    preview: str
    section_count: int = Field(ge=0)
    token_estimate: int = Field(ge=0)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    @field_validator("preview")
    @classmethod
    def preview_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "preview")
        return value


class PromptCompileResult(BaseModel):
    """Result of prompt packet compilation."""

    model_config = ConfigDict(extra="forbid")

    prompt_packet: PromptPacket
    boundary_check: PromptBoundaryCheck | None = None
    model_input_manifest: Any | None = None
    blocked: bool
    constraints: list[str]
    warnings: list[dict[str, Any]]
    created_at: datetime


__all__ = [
    "PromptBoundaryCheck",
    "PromptCompileRequest",
    "PromptCompileResult",
    "PromptFragment",
    "PromptFragmentCreateRequest",
    "PromptInjectionFinding",
    "PromptPacket",
    "PromptPreview",
    "PromptPreviewRequest",
    "PromptSection",
    "PromptTemplate",
    "PromptTemplateCreateRequest",
    "reject_hidden_or_secret_text",
    "reject_secret_like_payload",
]
