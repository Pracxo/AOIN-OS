"""Disabled production-auth request identity contracts."""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime
from typing import Any, Literal, NoReturn

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.production_auth.canonical import sha256_fingerprint

SCHEMA_VERSION = "request-identity/v1"
BOUNDARY_VERSION = "request-identity-boundary/v1"
CANONICALIZATION_VERSION = "production-auth-canonical-json/v1"
REASON_CODE_REGISTRY_VERSION = "request-identity-reason-codes/v1"

AUTHORIZATION_TRANSACTION_ID = "AION-155-PA-0003"
APPROVAL_RECORD_ID = "AION-155-PA-0003"
PARENT_AUTHORIZATION_TRANSACTION_ID = "AION-153-PA-0002"
AUTHORIZATION_SCOPE = "disabled-request-identity-boundary"
IMPLEMENTATION_TASK = "AION-156"
CANDIDATE_ID = "production-auth-request-identity-boundary"
WORKSTREAM = "production-auth-request-integration"

REQUEST_IDENTITY_BOUNDARY_STATE: Literal["implemented_disabled"] = "implemented_disabled"
BOUNDARY_MODE: Literal["observe_only_disabled"] = "observe_only_disabled"
AUTHENTICATION_STATE: Literal["disabled"] = "disabled"

RequestIdentityBoundaryState = Literal["implemented_disabled"]
RequestIdentityBoundaryMode = Literal["observe_only_disabled"]
RequestIdentityAuthenticationState = Literal["disabled"]
RequestIdentitySource = Literal[
    "disabled_verifier",
    "deterministic_disabled_test_verifier",
]
RequestIdentityAuditEventType = Literal[
    "request_identity_boundary_attached",
    "request_identity_boundary_skipped",
    "request_identity_boundary_failed_closed",
    "request_identity_disabled_verification",
]
RequestIdentityVerifierType = Literal["disabled", "deterministic_disabled_test"]

REQUIRED_REASON_CODES: tuple[str, ...] = (
    "request_identity_boundary_observe_only",
    "production_auth_runtime_disabled",
    "identity_verification_disabled",
    "authenticated_requests_disabled",
    "anonymous_disabled_context_attached",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
)
ALLOWED_AUDIT_EVENT_TYPES: tuple[str, ...] = (
    "request_identity_boundary_attached",
    "request_identity_boundary_skipped",
    "request_identity_boundary_failed_closed",
    "request_identity_disabled_verification",
)

_PROTECTED_KEY_PARTS = {
    "access_token",
    "api_key",
    "apikey",
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
    "session_token",
    "token",
    "token_value",
}
_PROTECTED_KEY_MARKERS = {
    "claim",
    "claims",
    "secret",
    "session",
}
_PROTECTED_VALUE_MARKERS = (
    "access token",
    "refresh token",
    "id token",
    "session token",
    "authorization header",
    "private key",
    "client secret",
    "raw identity claim",
    "provider payload",
    "raw prompt",
    "hidden reasoning",
    "password",
    "credential",
    "cookie",
    "bearer ",
)


class RequestIdentityVersionedModel(BaseModel):
    """Common schema fields for request identity contracts."""

    schema_version: str = SCHEMA_VERSION
    boundary_version: str = BOUNDARY_VERSION
    canonicalization_version: str = CANONICALIZATION_VERSION
    reason_code_registry_version: str = REASON_CODE_REGISTRY_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value

    @field_validator("boundary_version")
    @classmethod
    def boundary_version_must_match(cls, value: str) -> str:
        if value != BOUNDARY_VERSION:
            raise ValueError(f"boundary_version must be {BOUNDARY_VERSION}")
        return value

    @field_validator("canonicalization_version")
    @classmethod
    def canonicalization_version_must_match(cls, value: str) -> str:
        if value != CANONICALIZATION_VERSION:
            raise ValueError(f"canonicalization_version must be {CANONICALIZATION_VERSION}")
        return value

    @field_validator("reason_code_registry_version")
    @classmethod
    def reason_code_registry_version_must_match(cls, value: str) -> str:
        if value != REASON_CODE_REGISTRY_VERSION:
            raise ValueError(
                f"reason_code_registry_version must be {REASON_CODE_REGISTRY_VERSION}"
            )
        return value


class RequestIdentityFingerprintedModel(RequestIdentityVersionedModel):
    """Versioned request identity evidence with deterministic fingerprinting."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> RequestIdentityFingerprintedModel:
        expected = _fingerprint_for_model(self)
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical evidence payload")
        return self


class _FrozenDict(dict[str, Any]):
    """Small immutable dict for nested evidence metadata."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("request identity evidence metadata is immutable")

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


class RequestIdentityVerificationInput(RequestIdentityVersionedModel):
    """Safe correlation-only input for the disabled request identity verifier."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    identity_source: RequestIdentitySource = "disabled_verifier"
    boundary_mode: RequestIdentityBoundaryMode = BOUNDARY_MODE
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("request_id", "trace_id", "correlation_id")
    @classmethod
    def correlation_values_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _reject_protected_material(value)
        return value

    @field_validator("authorization_transaction_id", "approval_record_id")
    @classmethod
    def authorization_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("authorization_transaction_id must be AION-155-PA-0003")
        return value

    @field_validator("parent_authorization_transaction_id")
    @classmethod
    def parent_authorization_must_match(cls, value: str) -> str:
        if value != PARENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("parent_authorization_transaction_id must be AION-153-PA-0002")
        return value

    @field_validator("implementation_task")
    @classmethod
    def implementation_task_must_match(cls, value: str) -> str:
        if value != IMPLEMENTATION_TASK:
            raise ValueError("implementation_task must be AION-156")
        return value

    @field_validator("authorization_scope")
    @classmethod
    def authorization_scope_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_SCOPE:
            raise ValueError("authorization_scope must be disabled-request-identity-boundary")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return dict(value)


class RequestIdentityVerificationResult(RequestIdentityFingerprintedModel):
    """Anonymous disabled verification result."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    verification_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    identity_source: RequestIdentitySource = "disabled_verifier"
    boundary_mode: RequestIdentityBoundaryMode = BOUNDARY_MODE
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    authentication_state: RequestIdentityAuthenticationState = AUTHENTICATION_STATE
    authenticated: bool = False
    actor_id: None = None
    subject: None = None
    roles: tuple[str, ...] = Field(default_factory=tuple)
    runtime_effect: bool = False
    redacted: bool = True
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def result_must_remain_disabled(self) -> RequestIdentityVerificationResult:
        _require_disabled_identity_state(self)
        return self


class RequestIdentityContext(RequestIdentityFingerprintedModel):
    """Immutable request-scoped anonymous disabled identity context."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    context_id: str = Field(min_length=1)
    verification_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    identity_source: RequestIdentitySource = "disabled_verifier"
    boundary_mode: RequestIdentityBoundaryMode = BOUNDARY_MODE
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    authentication_state: RequestIdentityAuthenticationState = AUTHENTICATION_STATE
    authenticated: bool = False
    actor_id: None = None
    subject: None = None
    roles: tuple[str, ...] = Field(default_factory=tuple)
    runtime_effect: bool = False
    redacted: bool = True
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def context_must_remain_disabled(self) -> RequestIdentityContext:
        _require_disabled_identity_state(self)
        return self


class RequestIdentityAuditEvent(RequestIdentityFingerprintedModel):
    """Redacted request identity audit event."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    event_id: str = Field(min_length=1)
    event_type: RequestIdentityAuditEventType
    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    context_id: str | None = None
    verification_id: str | None = None
    identity_source: RequestIdentitySource = "disabled_verifier"
    boundary_mode: RequestIdentityBoundaryMode = BOUNDARY_MODE
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    authentication_state: RequestIdentityAuthenticationState = AUTHENTICATION_STATE
    authenticated: bool = False
    actor_id: None = None
    subject: None = None
    roles: tuple[str, ...] = Field(default_factory=tuple)
    runtime_effect: bool = False
    redacted: bool = True
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def audit_must_be_disabled_and_redacted(self) -> RequestIdentityAuditEvent:
        _require_disabled_identity_state(self)
        return self


class RequestIdentityProvenanceRecord(RequestIdentityFingerprintedModel):
    """Redacted provenance record for request identity evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    provenance_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    source_refs: tuple[str, ...] = Field(min_length=1)
    verifier_type: RequestIdentityVerifierType = "disabled"
    identity_source: RequestIdentitySource = "disabled_verifier"
    boundary_mode: RequestIdentityBoundaryMode = BOUNDARY_MODE
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    runtime_effect: bool = False
    redacted: bool = True
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_refs")
    @classmethod
    def source_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            _reject_protected_material(item)
        return tuple(value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def provenance_must_be_disabled_and_redacted(self) -> RequestIdentityProvenanceRecord:
        _require_redacted_runtime_hold(self)
        return self


class RequestIdentityBoundaryStatus(RequestIdentityFingerprintedModel):
    """Safe status for the disabled request identity boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    status_id: str = Field(min_length=1)
    request_identity_boundary_implemented: bool = True
    request_identity_boundary_state: RequestIdentityBoundaryState = REQUEST_IDENTITY_BOUNDARY_STATE
    request_identity_boundary_default_enabled: bool = False
    request_identity_boundary_registered: bool = False
    request_identity_boundary_mode: RequestIdentityBoundaryMode = BOUNDARY_MODE
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_156_merge: bool = True
    runtime_guard_hold_active: bool = True
    runtime_no_go_status: bool = True
    runtime_implementation_approved: bool = False
    production_auth_runtime_enabled: bool = False
    identity_verification_enabled: bool = False
    authenticated_requests_enabled: bool = False
    runtime_enablement_guard_release_approved: bool = False
    runtime_enablement_guard_final_lock_release_approved: bool = False
    runtime_enablement_master_lock_release_approved: bool = False
    runtime_effect: bool = False
    redacted: bool = True
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def status_must_hold_runtime_disabled(self) -> RequestIdentityBoundaryStatus:
        _require_boundary_status(self)
        return self


class RequestIdentityDiagnosticSnapshot(RequestIdentityFingerprintedModel):
    """Safe diagnostics for the disabled request identity boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    snapshot_id: str = Field(min_length=1)
    request_identity_boundary_implemented: bool = True
    request_identity_boundary_state: RequestIdentityBoundaryState = REQUEST_IDENTITY_BOUNDARY_STATE
    request_identity_boundary_default_enabled: bool = False
    request_identity_boundary_registered: bool = False
    request_identity_boundary_mode: RequestIdentityBoundaryMode = BOUNDARY_MODE
    verifier_type: RequestIdentityVerifierType = "disabled"
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_156_merge: bool = True
    identity_verification_enabled: bool = False
    authenticated_requests_enabled: bool = False
    production_auth_runtime_enabled: bool = False
    runtime_no_go_status: bool = True
    runtime_effect: bool = False
    blocker_count: int = Field(default=len(REQUIRED_REASON_CODES), ge=0)
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    redacted: bool = True
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def diagnostic_must_hold_runtime_disabled(self) -> RequestIdentityDiagnosticSnapshot:
        _require_boundary_status(self)
        if self.blocker_count != len(self.reason_codes):
            raise ValueError("blocker_count must match reason_codes")
        return self


class RequestIdentityBoundaryBundle(RequestIdentityFingerprintedModel):
    """Correlated request identity context, audit, provenance, and status."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    bundle_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    verification: RequestIdentityVerificationResult
    identity_context: RequestIdentityContext
    audit_event: RequestIdentityAuditEvent
    provenance: RequestIdentityProvenanceRecord
    status: RequestIdentityBoundaryStatus
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    runtime_effect: bool = False
    redacted: bool = True
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def bundle_must_be_correlated_and_disabled(self) -> RequestIdentityBoundaryBundle:
        _require_redacted_runtime_hold(self)
        for item in (
            self.verification,
            self.identity_context,
            self.audit_event,
            self.provenance,
        ):
            if item.request_id != self.request_id:
                raise ValueError("bundle request_id must match nested evidence")
            if item.trace_id != self.trace_id:
                raise ValueError("bundle trace_id must match nested evidence")
            if item.correlation_id != self.correlation_id:
                raise ValueError("bundle correlation_id must match nested evidence")
        return self


def utc_now() -> datetime:
    """Return timezone-aware UTC time."""

    return datetime.now(UTC)


def validate_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    """Validate request identity reason codes against the local registry."""

    if not value:
        raise ValueError("reason_codes cannot be empty")
    unknown = [code for code in value if code not in REQUIRED_REASON_CODES]
    if unknown:
        raise ValueError("unknown request identity reason code")
    return tuple(value)


def _require_disabled_identity_state(model: object) -> None:
    _require_redacted_runtime_hold(model)
    if getattr(model, "authentication_state", AUTHENTICATION_STATE) != AUTHENTICATION_STATE:
        raise ValueError("authentication_state must be disabled")
    if bool(getattr(model, "authenticated", False)):
        raise ValueError("authenticated must be false")
    if getattr(model, "actor_id", None) is not None:
        raise ValueError("actor_id must be null")
    if getattr(model, "subject", None) is not None:
        raise ValueError("subject must be null")
    if tuple(getattr(model, "roles", ())) != ():
        raise ValueError("roles must be empty")


def _require_boundary_status(model: object) -> None:
    _require_redacted_runtime_hold(model)
    if not getattr(model, "request_identity_boundary_implemented", True):
        raise ValueError("request_identity_boundary_implemented must be true")
    if getattr(model, "request_identity_boundary_state", REQUEST_IDENTITY_BOUNDARY_STATE) != (
        REQUEST_IDENTITY_BOUNDARY_STATE
    ):
        raise ValueError("request_identity_boundary_state must be implemented_disabled")
    if bool(getattr(model, "request_identity_boundary_default_enabled", False)):
        raise ValueError("request_identity_boundary_default_enabled must be false")
    if bool(getattr(model, "identity_verification_enabled", False)):
        raise ValueError("identity_verification_enabled must be false")
    if bool(getattr(model, "authenticated_requests_enabled", False)):
        raise ValueError("authenticated_requests_enabled must be false")
    if bool(getattr(model, "production_auth_runtime_enabled", False)):
        raise ValueError("production_auth_runtime_enabled must be false")
    if not bool(getattr(model, "runtime_no_go_status", True)):
        raise ValueError("runtime_no_go_status must be true")


def _require_redacted_runtime_hold(model: object) -> None:
    if bool(getattr(model, "runtime_effect", False)):
        raise ValueError("runtime_effect must be false")
    if not bool(getattr(model, "redacted", True)):
        raise ValueError("redacted must be true")
    if getattr(model, "authorization_transaction_id", AUTHORIZATION_TRANSACTION_ID) != (
        AUTHORIZATION_TRANSACTION_ID
    ):
        raise ValueError("authorization_transaction_id must be AION-155-PA-0003")
    if getattr(model, "approval_record_id", APPROVAL_RECORD_ID) != APPROVAL_RECORD_ID:
        raise ValueError("approval_record_id must be AION-155-PA-0003")
    if getattr(
        model,
        "parent_authorization_transaction_id",
        PARENT_AUTHORIZATION_TRANSACTION_ID,
    ) != PARENT_AUTHORIZATION_TRANSACTION_ID:
        raise ValueError("parent_authorization_transaction_id must be AION-153-PA-0002")
    if getattr(model, "implementation_task", IMPLEMENTATION_TASK) != IMPLEMENTATION_TASK:
        raise ValueError("implementation_task must be AION-156")
    if getattr(model, "authorization_scope", AUTHORIZATION_SCOPE) != AUTHORIZATION_SCOPE:
        raise ValueError("authorization_scope must be disabled-request-identity-boundary")


def _reject_protected_material(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = _normalize_key(str(key))
            if any(part in normalized for part in _PROTECTED_KEY_PARTS) or any(
                marker in normalized for marker in _PROTECTED_KEY_MARKERS
            ):
                raise ValueError("payload must not contain protected material keys")
            _reject_protected_material(nested)
        return
    if isinstance(value, list | tuple | set):
        for item in value:
            _reject_protected_material(item)
        return
    if isinstance(value, str):
        reject_hidden_or_secret_text(value, "request identity payload")
        normalized = _normalize_value(value)
        if any(marker in normalized for marker in _PROTECTED_VALUE_MARKERS):
            raise ValueError("payload must not contain protected material values")


def _freeze_mapping(value: dict[str, Any]) -> _FrozenDict:
    return _FrozenDict(value)


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return normalized.replace("-", "_").replace(" ", "_")


def _normalize_value(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().replace("-", " ")


def _fingerprint_for_model(model: BaseModel) -> str:
    payload = model.model_dump(mode="json", exclude={"fingerprint"})
    return sha256_fingerprint(payload)


__all__ = [
    "ALLOWED_AUDIT_EVENT_TYPES",
    "APPROVAL_RECORD_ID",
    "AUTHENTICATION_STATE",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "BOUNDARY_MODE",
    "BOUNDARY_VERSION",
    "CANONICALIZATION_VERSION",
    "CANDIDATE_ID",
    "IMPLEMENTATION_TASK",
    "PARENT_AUTHORIZATION_TRANSACTION_ID",
    "REASON_CODE_REGISTRY_VERSION",
    "REQUEST_IDENTITY_BOUNDARY_STATE",
    "REQUIRED_REASON_CODES",
    "SCHEMA_VERSION",
    "WORKSTREAM",
    "RequestIdentityAuditEvent",
    "RequestIdentityAuditEventType",
    "RequestIdentityAuthenticationState",
    "RequestIdentityBoundaryBundle",
    "RequestIdentityBoundaryMode",
    "RequestIdentityBoundaryState",
    "RequestIdentityBoundaryStatus",
    "RequestIdentityContext",
    "RequestIdentityDiagnosticSnapshot",
    "RequestIdentityProvenanceRecord",
    "RequestIdentitySource",
    "RequestIdentityVerificationInput",
    "RequestIdentityVerificationResult",
    "RequestIdentityVerifierType",
    "utc_now",
    "validate_reason_codes",
]
