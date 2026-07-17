"""Fail-closed actor-context resolution contracts."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal, NoReturn

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.scopes import ActorContext
from aion_brain.production_auth.canonical import sha256_fingerprint

SCHEMA_VERSION = "actor-context-resolution/v1"
CANONICALIZATION_VERSION = "production-auth-canonical-json/v1"
REASON_CODE_REGISTRY_VERSION = "actor-context-reason-codes/v1"

AUTHORIZATION_TRANSACTION_ID = "AION-159-PA-0005"
APPROVAL_RECORD_ID = "AION-159-PA-0005"
PARENT_AUTHORIZATION_TRANSACTION_ID = "AION-157-PA-0004"
AUTHORIZATION_SCOPE = "fail-closed-actor-context-resolution"
IMPLEMENTATION_TASK = "AION-160"
CANDIDATE_ID = "production-auth-actor-context-trust-boundary"
WORKSTREAM = "production-auth-route-context-hardening"

ACTOR_CONTEXT_RESOLUTION_STATE: Literal["implemented_fail_closed"] = (
    "implemented_fail_closed"
)

ActorContextResolutionSource = Literal[
    "anonymous_fail_closed",
    "request_identity_disabled",
    "development_simulation",
]
ActorContextResolutionReasonCode = Literal[
    "actor_context_anonymous_fail_closed",
    "non_development_identity_headers_ignored",
    "request_identity_context_disabled",
    "request_identity_context_invalid_fail_closed",
    "request_context_correlation_projected",
    "request_context_identity_metadata_ignored",
    "development_identity_simulation_enabled",
    "development_identity_headers_accepted",
    "runtime_authentication_disabled",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
]
ActorContextResolutionEventType = Literal[
    "actor_context_resolution_succeeded",
    "actor_context_resolution_failed_closed",
]

REQUIRED_REASON_CODES: tuple[ActorContextResolutionReasonCode, ...] = (
    "actor_context_anonymous_fail_closed",
    "non_development_identity_headers_ignored",
    "request_context_correlation_projected",
    "request_context_identity_metadata_ignored",
    "runtime_authentication_disabled",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
)
REQUEST_IDENTITY_REASON_CODES: tuple[ActorContextResolutionReasonCode, ...] = (
    "request_identity_context_disabled",
    "non_development_identity_headers_ignored",
    "request_context_correlation_projected",
    "request_context_identity_metadata_ignored",
    "runtime_authentication_disabled",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
)
INVALID_REQUEST_IDENTITY_REASON_CODES: tuple[ActorContextResolutionReasonCode, ...] = (
    "request_identity_context_invalid_fail_closed",
    "non_development_identity_headers_ignored",
    "request_context_correlation_projected",
    "request_context_identity_metadata_ignored",
    "runtime_authentication_disabled",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
)
DEVELOPMENT_REASON_CODES: tuple[ActorContextResolutionReasonCode, ...] = (
    "development_identity_simulation_enabled",
    "development_identity_headers_accepted",
    "request_context_correlation_projected",
    "runtime_authentication_disabled",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
)
ALLOWED_REASON_CODES: tuple[ActorContextResolutionReasonCode, ...] = (
    "actor_context_anonymous_fail_closed",
    "non_development_identity_headers_ignored",
    "request_identity_context_disabled",
    "request_identity_context_invalid_fail_closed",
    "request_context_correlation_projected",
    "request_context_identity_metadata_ignored",
    "development_identity_simulation_enabled",
    "development_identity_headers_accepted",
    "runtime_authentication_disabled",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
)

_PROTECTED_KEY_PARTS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "authorization_header",
    "bearer",
    "client_secret",
    "cookie",
    "credential",
    "hidden_reasoning",
    "id_token",
    "password",
    "private_key",
    "provider_payload",
    "raw_identity_claim",
    "raw_prompt",
    "refresh_token",
    "session",
    "session_token",
    "token",
}
_PROTECTED_VALUE_MARKERS = (
    "access token",
    "authorization header",
    "bearer ",
    "client secret",
    "cookie",
    "credential",
    "hidden reasoning",
    "id token",
    "password",
    "private key",
    "provider payload",
    "raw identity claim",
    "raw prompt",
    "refresh token",
    "session token",
)


class ActorContextResolutionVersionedModel(BaseModel):
    """Shared AION-160 version, authorization, and runtime guard fields."""

    schema_version: str = SCHEMA_VERSION
    canonicalization_version: str = CANONICALIZATION_VERSION
    reason_code_registry_version: str = REASON_CODE_REGISTRY_VERSION
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    candidate_id: str = CANDIDATE_ID
    workstream: str = WORKSTREAM
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_160_merge: bool = True
    actor_context_trust_boundary_remediated: bool = True
    actor_context_resolution_state: Literal["implemented_fail_closed"] = (
        ACTOR_CONTEXT_RESOLUTION_STATE
    )
    runtime_guard_hold_active: bool = True
    runtime_no_go_status: bool = True
    runtime_implementation_approved: bool = False
    production_auth_runtime_enabled: bool = False
    identity_verification_enabled: bool = False
    authenticated_requests_enabled: bool = False
    authenticated_actor_context_enabled: bool = False
    runtime_effect: bool = False
    redacted: bool = True

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value

    @field_validator("canonicalization_version")
    @classmethod
    def canonicalization_version_must_match(cls, value: str) -> str:
        if value != CANONICALIZATION_VERSION:
            raise ValueError(
                f"canonicalization_version must be {CANONICALIZATION_VERSION}"
            )
        return value

    @field_validator("reason_code_registry_version")
    @classmethod
    def reason_code_registry_version_must_match(cls, value: str) -> str:
        if value != REASON_CODE_REGISTRY_VERSION:
            raise ValueError(
                f"reason_code_registry_version must be {REASON_CODE_REGISTRY_VERSION}"
            )
        return value

    @model_validator(mode="after")
    def runtime_must_remain_disabled(self) -> ActorContextResolutionVersionedModel:
        _require_runtime_hold(self)
        return self


class ActorContextResolutionFingerprintedModel(ActorContextResolutionVersionedModel):
    """Versioned actor-context evidence with deterministic fingerprinting."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(
        self,
    ) -> ActorContextResolutionFingerprintedModel:
        expected = _fingerprint_for_model(self)
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical evidence payload")
        return self


class _FrozenDict(dict[str, Any]):
    """Small immutable dict for nested evidence metadata."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("actor context evidence metadata is immutable")

    def __setitem__(self, key: str, value: Any) -> NoReturn:
        self._blocked(key, value)

    def __delitem__(self, key: str) -> NoReturn:
        self._blocked(key)

    def clear(self) -> NoReturn:
        self._blocked()

    def pop(self, key: str, default: Any = None) -> NoReturn:  # noqa: ARG002
        self._blocked(key, default)

    def popitem(self) -> NoReturn:
        self._blocked()

    def setdefault(self, key: str, default: Any = None) -> NoReturn:
        self._blocked(key, default)

    def update(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._blocked(*args, **kwargs)


class ActorContextResolutionInput(ActorContextResolutionVersionedModel):
    """Immutable safe input for fail-closed actor-context resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    request_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    request_identity_context_present: bool = False
    request_identity_context_valid: bool = False
    development_simulation_enabled: bool = False
    development_actor_id: str | None = None
    development_workspace_id: str | None = None
    development_roles: tuple[str, ...] = Field(default_factory=tuple)
    development_permissions: tuple[str, ...] = Field(default_factory=tuple)
    development_security_scope: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class ActorContextResolutionStatus(ActorContextResolutionFingerprintedModel):
    """Public-safe status of one actor-context resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    status_id: str = Field(min_length=1)
    source: ActorContextResolutionSource
    reason_codes: tuple[ActorContextResolutionReasonCode, ...]
    request_id_present: bool = False
    trace_id_present: bool = False
    correlation_id_present: bool = False
    request_identity_context_present: bool = False
    request_identity_context_valid: bool = False
    development_identity_simulation_available: bool = True
    development_identity_simulation_active: bool = False
    non_development_identity_headers_ignored: bool = True
    request_identity_context_precedence: bool = True
    request_context_correlation_projection: bool = True
    request_context_identity_metadata_ignored: bool = True
    anonymous_zero_permission_fallback: bool = True
    actor_id_present: bool = False
    workspace_id_present: bool = False
    role_count: int = 0
    permission_count: int = 0
    security_scope_count: int = 0
    dev_mode: bool = False
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(
        cls,
        value: tuple[ActorContextResolutionReasonCode, ...],
    ) -> tuple[ActorContextResolutionReasonCode, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class ActorContextResolutionAuditEvent(ActorContextResolutionFingerprintedModel):
    """Redacted request-scoped actor-context resolution audit event."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    event_id: str = Field(min_length=1)
    event_type: ActorContextResolutionEventType
    request_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    source: ActorContextResolutionSource
    reason_codes: tuple[ActorContextResolutionReasonCode, ...]
    development_header_value_count: int = 0
    production_identity_header_values_stored: bool = False
    actor_context_failed_closed: bool = False
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(
        cls,
        value: tuple[ActorContextResolutionReasonCode, ...],
    ) -> tuple[ActorContextResolutionReasonCode, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class ActorContextResolutionProvenanceRecord(ActorContextResolutionFingerprintedModel):
    """Redacted provenance record for actor-context resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    provenance_id: str = Field(min_length=1)
    request_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    source: ActorContextResolutionSource
    resolver_name: str = "ProductionAuthActorContextResolver"
    resolver_version: str = SCHEMA_VERSION
    resolver_input_contains_raw_request: bool = False
    resolver_input_contains_headers: bool = False
    resolver_input_contains_cookies: bool = False
    request_context_actor_metadata_ignored: bool = True
    request_context_workspace_metadata_ignored: bool = True
    request_identity_context_precedence: bool = True
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class ActorContextResolutionDiagnosticSnapshot(ActorContextResolutionFingerprintedModel):
    """Safe process-level actor-context remediation diagnostics."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    diagnostic_id: str = Field(min_length=1)
    development_identity_simulation_available: bool = True
    development_identity_simulation_active: bool = False
    non_development_identity_headers_ignored: bool = True
    request_identity_context_precedence: bool = True
    request_context_correlation_projection: bool = True
    request_context_identity_metadata_ignored: bool = True
    anonymous_zero_permission_fallback: bool = True
    production_actor_header_trust_enabled: bool = False
    production_workspace_header_trust_enabled: bool = False
    production_role_header_trust_enabled: bool = False
    production_permission_header_trust_enabled: bool = False
    production_security_scope_header_trust_enabled: bool = False
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class ActorContextResolutionBundle(ActorContextResolutionFingerprintedModel):
    """Complete actor-context resolution result returned to request dependencies."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    bundle_id: str = Field(min_length=1)
    request_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    source: ActorContextResolutionSource
    actor_context: ActorContext
    status: ActorContextResolutionStatus
    audit_event: ActorContextResolutionAuditEvent
    provenance: ActorContextResolutionProvenanceRecord
    diagnostic_snapshot: ActorContextResolutionDiagnosticSnapshot
    reason_codes: tuple[ActorContextResolutionReasonCode, ...]
    resolution_failed: bool = False
    failure_reason: str | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(
        cls,
        value: tuple[ActorContextResolutionReasonCode, ...],
    ) -> tuple[ActorContextResolutionReasonCode, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def nested_evidence_must_match_bundle(self) -> ActorContextResolutionBundle:
        for item in (self.status, self.audit_event, self.provenance):
            if getattr(item, "source", self.source) != self.source:
                raise ValueError("nested source must match bundle source")
        if self.audit_event.reason_codes != self.reason_codes:
            raise ValueError("audit reason_codes must match bundle")
        if self.actor_context.dev_mode and self.source != "development_simulation":
            raise ValueError("dev_mode is only allowed for development simulation")
        if self.source != "development_simulation":
            _require_anonymous_actor_context(self.actor_context)
        return self


def validate_reason_codes(
    value: tuple[ActorContextResolutionReasonCode, ...],
) -> tuple[ActorContextResolutionReasonCode, ...]:
    """Validate actor-context reason codes against the immutable registry."""

    if not value:
        raise ValueError("reason_codes cannot be empty")
    unknown = [code for code in value if code not in ALLOWED_REASON_CODES]
    if unknown:
        raise ValueError("unknown actor context reason code")
    return tuple(value)


def reject_protected_material(value: Any) -> None:
    """Reject protected material from redacted actor-context evidence."""

    _reject_protected_material(value)


def utc_now() -> datetime:
    """Return timezone-aware UTC time."""

    return datetime.now(UTC)


def _require_runtime_hold(model: object) -> None:
    if not bool(getattr(model, "runtime_guard_hold_active", True)):
        raise ValueError("runtime_guard_hold_active must be true")
    if not bool(getattr(model, "runtime_no_go_status", True)):
        raise ValueError("runtime_no_go_status must be true")
    for field_name in (
        "runtime_implementation_approved",
        "production_auth_runtime_enabled",
        "identity_verification_enabled",
        "authenticated_requests_enabled",
        "authenticated_actor_context_enabled",
        "runtime_effect",
        "authorization_reusable",
    ):
        if bool(getattr(model, field_name, False)):
            raise ValueError(f"{field_name} must be false")
    if not bool(getattr(model, "redacted", True)):
        raise ValueError("redacted must be true")
    if getattr(model, "authorization_transaction_id", AUTHORIZATION_TRANSACTION_ID) != (
        AUTHORIZATION_TRANSACTION_ID
    ):
        raise ValueError("authorization_transaction_id must be AION-159-PA-0005")
    if getattr(model, "approval_record_id", APPROVAL_RECORD_ID) != APPROVAL_RECORD_ID:
        raise ValueError("approval_record_id must be AION-159-PA-0005")
    if getattr(
        model,
        "parent_authorization_transaction_id",
        PARENT_AUTHORIZATION_TRANSACTION_ID,
    ) != PARENT_AUTHORIZATION_TRANSACTION_ID:
        raise ValueError("parent_authorization_transaction_id must be AION-157-PA-0004")
    if getattr(model, "implementation_task", IMPLEMENTATION_TASK) != IMPLEMENTATION_TASK:
        raise ValueError("implementation_task must be AION-160")
    if getattr(model, "authorization_scope", AUTHORIZATION_SCOPE) != AUTHORIZATION_SCOPE:
        raise ValueError(
            "authorization_scope must be fail-closed-actor-context-resolution"
        )
    if not bool(getattr(model, "authorization_expires_on_aion_160_merge", True)):
        raise ValueError("authorization_expires_on_aion_160_merge must be true")


def _require_anonymous_actor_context(actor_context: ActorContext) -> None:
    if actor_context.actor_id is not None:
        raise ValueError("actor_context.actor_id must be null")
    if actor_context.actor_type is not None:
        raise ValueError("actor_context.actor_type must be null")
    if actor_context.workspace_id is not None:
        raise ValueError("actor_context.workspace_id must be null")
    if actor_context.roles:
        raise ValueError("actor_context.roles must be empty")
    if actor_context.permissions:
        raise ValueError("actor_context.permissions must be empty")
    if actor_context.security_scope:
        raise ValueError("actor_context.security_scope must be empty")
    if actor_context.dev_mode:
        raise ValueError("actor_context.dev_mode must be false")


def _freeze_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return _FrozenDict({key: _freeze_value(nested) for key, nested in value.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    return value


def _reject_protected_material(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = _normalize_marker(str(key))
            if _contains_protected_marker(normalized_key, _PROTECTED_KEY_PARTS):
                raise ValueError("protected material is not allowed in actor context evidence")
            _reject_protected_material(nested)
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for item in value:
            _reject_protected_material(item)
        return
    if isinstance(value, BaseModel):
        _reject_protected_material(value.model_dump(mode="python"))
        return
    if isinstance(value, str):
        normalized_value = _normalize_marker(value)
        if _contains_protected_marker(normalized_value, _PROTECTED_VALUE_MARKERS):
            raise ValueError("protected material is not allowed in actor context evidence")


def _contains_protected_marker(value: str, markers: set[str] | tuple[str, ...]) -> bool:
    return any(_normalize_marker(marker) in value for marker in markers)


def _normalize_marker(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("-", "_").replace(" ", "_")
    return normalized.lower()


def _fingerprint_for_model(model: BaseModel) -> str:
    payload = model.model_dump(mode="json", exclude={"fingerprint"})
    return sha256_fingerprint(payload)


__all__ = [
    "ACTOR_CONTEXT_RESOLUTION_STATE",
    "ALLOWED_REASON_CODES",
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "ActorContextResolutionAuditEvent",
    "ActorContextResolutionBundle",
    "ActorContextResolutionDiagnosticSnapshot",
    "ActorContextResolutionInput",
    "ActorContextResolutionProvenanceRecord",
    "ActorContextResolutionReasonCode",
    "ActorContextResolutionSource",
    "ActorContextResolutionStatus",
    "DEVELOPMENT_REASON_CODES",
    "IMPLEMENTATION_TASK",
    "INVALID_REQUEST_IDENTITY_REASON_CODES",
    "PARENT_AUTHORIZATION_TRANSACTION_ID",
    "REQUIRED_REASON_CODES",
    "REQUEST_IDENTITY_REASON_CODES",
    "reject_protected_material",
    "utc_now",
    "validate_reason_codes",
]
