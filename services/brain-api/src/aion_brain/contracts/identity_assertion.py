"""Offline Ed25519 identity assertion verification contracts."""

from __future__ import annotations

import base64
import binascii
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal, NoReturn

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.production_auth.canonical import canonical_json_bytes, sha256_fingerprint

SCHEMA_VERSION = "identity-assertion/v1"
PAYLOAD_SCHEMA_VERSION = "identity-assertion-payload/v1"
VERIFICATION_SCHEMA_VERSION = "identity-assertion-verification/v1"
PUBLIC_KEY_SCHEMA_VERSION = "identity-assertion-public-key/v1"
CANONICALIZATION_VERSION = "production-auth-canonical-json/v1"
REASON_CODE_REGISTRY_VERSION = "identity-assertion-reason-codes/v1"

AUTHORIZATION_TRANSACTION_ID = "AION-161-PA-0006"
APPROVAL_RECORD_ID = "AION-161-PA-0006"
PARENT_AUTHORIZATION_TRANSACTION_ID = "AION-159-PA-0005"
AUTHORIZATION_SCOPE = "offline-ed25519-identity-assertion-verification"
IMPLEMENTATION_TASK = "AION-162"
CANDIDATE_ID = "production-auth-offline-identity-assertion-verification"
WORKSTREAM = "production-auth-verification-core"

DOMAIN_SEPARATOR = b"AION-IDENTITY-ASSERTION-V1\0"
MAXIMUM_ASSERTION_LIFETIME_SECONDS = 300
DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS = 30
MAXIMUM_METADATA_CANONICAL_BYTES = 4096
MAXIMUM_PAYLOAD_CANONICAL_BYTES = 16384

OFFLINE_IDENTITY_ASSERTION_VERIFICATION_STATE: Literal["implemented_unintegrated"] = (
    "implemented_unintegrated"
)
FIXED_ALGORITHM: Literal["Ed25519"] = "Ed25519"

IdentityAssertionReasonCode = Literal[
    "identity_assertion_verified",
    "identity_assertion_rejected",
    "payload_canonicalized",
    "public_key_resolved",
    "signature_valid",
    "signature_invalid",
    "public_key_unknown",
    "public_key_issuer_mismatch",
    "public_key_revoked",
    "public_key_inactive",
    "public_key_retired",
    "issuer_mismatch",
    "audience_mismatch",
    "future_issued_at",
    "not_yet_valid",
    "assertion_expired",
    "assertion_lifetime_exceeded",
    "malformed_envelope",
    "malformed_public_key",
    "malformed_signature",
    "metadata_rejected",
    "claim_constraint_violation",
    "runtime_authentication_disabled",
    "actor_context_application_disabled",
    "request_identity_context_application_disabled",
    "runtime_integration_disabled",
    "replay_protection_not_implemented",
    "authorization_scope_implementation_only",
    "runtime_no_go_status_locked",
]
IdentityAssertionAuditEventType = Literal[
    "identity_assertion_verification_succeeded",
    "identity_assertion_verification_rejected",
]

ALLOWED_REASON_CODES: tuple[IdentityAssertionReasonCode, ...] = (
    "identity_assertion_verified",
    "identity_assertion_rejected",
    "payload_canonicalized",
    "public_key_resolved",
    "signature_valid",
    "signature_invalid",
    "public_key_unknown",
    "public_key_issuer_mismatch",
    "public_key_revoked",
    "public_key_inactive",
    "public_key_retired",
    "issuer_mismatch",
    "audience_mismatch",
    "future_issued_at",
    "not_yet_valid",
    "assertion_expired",
    "assertion_lifetime_exceeded",
    "malformed_envelope",
    "malformed_public_key",
    "malformed_signature",
    "metadata_rejected",
    "claim_constraint_violation",
    "runtime_authentication_disabled",
    "actor_context_application_disabled",
    "request_identity_context_application_disabled",
    "runtime_integration_disabled",
    "replay_protection_not_implemented",
    "authorization_scope_implementation_only",
    "runtime_no_go_status_locked",
)
MANDATORY_RUNTIME_BOUNDARY_REASON_CODES: tuple[IdentityAssertionReasonCode, ...] = (
    "runtime_authentication_disabled",
    "actor_context_application_disabled",
    "request_identity_context_application_disabled",
    "runtime_integration_disabled",
    "replay_protection_not_implemented",
    "authorization_scope_implementation_only",
    "runtime_no_go_status_locked",
)
SUCCESS_REASON_CODES: tuple[IdentityAssertionReasonCode, ...] = (
    "identity_assertion_verified",
    "payload_canonicalized",
    "public_key_resolved",
    "signature_valid",
    *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
)

_ASSERTION_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_BASE64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")
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
    "identity_assertion",
    "password",
    "private_key",
    "private_" "key_base64",
    "private_" "key_seed",
    "provider_payload",
    "raw_assertion",
    "raw_identity_claim",
    "raw_prompt",
    "refresh_token",
    "session",
    "session_token",
    "signature",
    "signing_" "key",
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
    "private key",
    "provider payload",
    "raw assertion",
    "raw identity claim",
    "raw prompt",
    "refresh token",
    "session token",
    "signing key",
)


class _FrozenDict(dict[str, Any]):
    """Small immutable dict for nested identity assertion metadata."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("identity assertion metadata is immutable")

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


class IdentityAssertionPayload(BaseModel):
    """Strict canonical payload signed by an offline Ed25519 issuer."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = PAYLOAD_SCHEMA_VERSION
    assertion_id: str
    issuer: str = Field(min_length=1, max_length=256)
    audience: str = Field(min_length=1, max_length=256)
    subject: str = Field(min_length=1, max_length=256)
    actor_id: str = Field(min_length=1, max_length=256)
    workspace_id: str | None = Field(default=None, max_length=256)
    roles: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    permissions: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    security_scope: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    issued_at: datetime
    not_before: datetime
    expires_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != PAYLOAD_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {PAYLOAD_SCHEMA_VERSION}")
        return value

    @field_validator("assertion_id")
    @classmethod
    def assertion_id_must_be_safe(cls, value: str) -> str:
        return validate_assertion_id(value)

    @field_validator("issuer", "audience", "subject", "actor_id")
    @classmethod
    def identity_text_must_be_safe(cls, value: str) -> str:
        return _validate_nonempty_untrimmed_text(value, max_length=256)

    @field_validator("workspace_id")
    @classmethod
    def workspace_id_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_nonempty_untrimmed_text(value, max_length=256)

    @field_validator("roles", mode="before")
    @classmethod
    def roles_must_be_unique_sorted(cls, value: object) -> tuple[str, ...]:
        return _validate_claims(value, field_name="roles", max_items=64, max_length=128)

    @field_validator("permissions", mode="before")
    @classmethod
    def permissions_must_be_unique_sorted(cls, value: object) -> tuple[str, ...]:
        return _validate_claims(
            value,
            field_name="permissions",
            max_items=128,
            max_length=192,
        )

    @field_validator("security_scope", mode="before")
    @classmethod
    def security_scope_must_be_unique_sorted(cls, value: object) -> tuple[str, ...]:
        return _validate_claims(
            value,
            field_name="security_scope",
            max_items=128,
            max_length=256,
        )

    @field_validator("issued_at", "not_before", "expires_at")
    @classmethod
    def datetimes_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        frozen = _freeze_mapping(value)
        if len(canonical_json_bytes(frozen)) > MAXIMUM_METADATA_CANONICAL_BYTES:
            raise ValueError("metadata canonical JSON exceeds maximum size")
        return frozen

    @model_validator(mode="after")
    def payload_temporal_and_size_must_be_safe(self) -> IdentityAssertionPayload:
        if self.issued_at > self.not_before:
            raise ValueError("issued_at must be before or equal to not_before")
        if self.not_before >= self.expires_at:
            raise ValueError("not_before must be before expires_at")
        lifetime = (self.expires_at - self.issued_at).total_seconds()
        if lifetime > MAXIMUM_ASSERTION_LIFETIME_SECONDS:
            raise ValueError("assertion lifetime exceeds maximum")
        payload = self.model_dump(mode="json")
        if len(canonical_json_bytes(payload)) > MAXIMUM_PAYLOAD_CANONICAL_BYTES:
            raise ValueError("payload canonical JSON exceeds maximum size")
        return self


class IdentityAssertionEnvelope(BaseModel):
    """Strict assertion envelope with no algorithm negotiation fields."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = SCHEMA_VERSION
    key_id: str
    payload: IdentityAssertionPayload
    signature: str

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value

    @field_validator("key_id")
    @classmethod
    def key_id_must_be_safe(cls, value: str) -> str:
        return validate_key_id(value)

    @field_validator("signature")
    @classmethod
    def signature_must_be_base64url(cls, value: str) -> str:
        _decode_base64url_unpadded(value, expected_length=64)
        return value


class TrustedIdentityAssertionPublicKey(BaseModel):
    """Public verification key trusted for a specific issuer and interval."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = PUBLIC_KEY_SCHEMA_VERSION
    key_id: str
    issuer: str = Field(min_length=1, max_length=256)
    public_key_base64url: str
    active_from: datetime
    active_until: datetime | None = None
    revoked: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != PUBLIC_KEY_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {PUBLIC_KEY_SCHEMA_VERSION}")
        return value

    @field_validator("key_id")
    @classmethod
    def key_id_must_be_safe(cls, value: str) -> str:
        return validate_key_id(value)

    @field_validator("issuer")
    @classmethod
    def issuer_must_be_safe(cls, value: str) -> str:
        return _validate_nonempty_untrimmed_text(value, max_length=256)

    @field_validator("public_key_base64url")
    @classmethod
    def public_key_must_be_base64url(cls, value: str) -> str:
        _decode_base64url_unpadded(value, expected_length=32)
        return value

    @field_validator("active_from", "active_until")
    @classmethod
    def datetimes_must_be_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        frozen = _freeze_mapping(value)
        if len(canonical_json_bytes(frozen)) > MAXIMUM_METADATA_CANONICAL_BYTES:
            raise ValueError("metadata canonical JSON exceeds maximum size")
        return frozen

    @model_validator(mode="after")
    def active_interval_must_be_safe(self) -> TrustedIdentityAssertionPublicKey:
        if self.active_until is not None and self.active_until <= self.active_from:
            raise ValueError("active_until must be after active_from")
        return self


class IdentityAssertionVerificationPolicy(BaseModel):
    """Verifier policy fixed to one issuer and one audience."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    expected_issuer: str = Field(min_length=1, max_length=256)
    expected_audience: str = Field(min_length=1, max_length=256)
    maximum_assertion_lifetime_seconds: int = Field(
        default=MAXIMUM_ASSERTION_LIFETIME_SECONDS,
        ge=1,
        le=MAXIMUM_ASSERTION_LIFETIME_SECONDS,
    )
    allowed_clock_skew_seconds: int = Field(
        default=DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS,
        ge=0,
        le=DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS,
    )

    @field_validator("expected_issuer", "expected_audience")
    @classmethod
    def expected_values_must_be_exact(cls, value: str) -> str:
        return _validate_nonempty_untrimmed_text(value, max_length=256)


class IdentityAssertionVersionedEvidence(BaseModel):
    """Shared authorization and runtime-boundary fields for evidence."""

    schema_version: str = VERIFICATION_SCHEMA_VERSION
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
    authorization_expires_on_aion_162_merge: bool = True
    offline_identity_assertion_verification_implemented: bool = True
    offline_identity_assertion_verification_state: Literal[
        "implemented_unintegrated"
    ] = OFFLINE_IDENTITY_ASSERTION_VERIFICATION_STATE
    fixed_algorithm: Literal["Ed25519"] = FIXED_ALGORITHM
    canonical_payload_enabled: bool = True
    domain_separation_enabled: bool = True
    public_key_registry_enabled: bool = True
    runtime_private_key_material_present: bool = False
    request_authenticated: bool = False
    actor_context_applied: bool = False
    request_identity_context_applied: bool = False
    runtime_effect: bool = False
    runtime_integration_allowed: bool = False
    replay_check_performed: bool = False
    replay_protection_required_before_request_integration: bool = True
    production_auth_runtime_enabled: bool = False
    identity_verification_enabled: bool = False
    authenticated_requests_enabled: bool = False
    identity_assertion_header_parsing_enabled: bool = False
    authorization_header_parsing_enabled: bool = False
    cookie_parsing_enabled: bool = False
    identity_assertion_middleware_registered: bool = False
    external_identity_provider_enabled: bool = False
    jwks_network_fetch_enabled: bool = False
    provider_discovery_enabled: bool = False
    external_calls_enabled: bool = False
    identity_assertion_endpoint_enabled: bool = False
    runtime_api_routes_added: bool = False
    openapi_security_scheme_added: bool = False
    sdk_runtime_resource_added: bool = False
    cli_runtime_command_added: bool = False
    new_package_manifest_added: bool = False
    lockfiles_added: bool = False
    migrations_added: bool = False
    v02_tag_created: bool = False
    v02_release_created: bool = False
    redacted: bool = True

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != VERIFICATION_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {VERIFICATION_SCHEMA_VERSION}")
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
    def runtime_boundary_must_hold(self) -> IdentityAssertionVersionedEvidence:
        _require_runtime_boundary(self)
        return self


class IdentityAssertionFingerprintedEvidence(IdentityAssertionVersionedEvidence):
    """Versioned identity assertion evidence with deterministic fingerprinting."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(
        self,
    ) -> IdentityAssertionFingerprintedEvidence:
        expected = _fingerprint_for_model(self)
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical evidence payload")
        return self


class IdentityAssertionClaimCounts(BaseModel):
    """Redacted claim counts for safe verification evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    roles: int = Field(ge=0, le=64)
    permissions: int = Field(ge=0, le=128)
    security_scope: int = Field(ge=0, le=128)
    workspace_present: bool
    metadata_keys: int = Field(ge=0)


class IdentityAssertionVerificationResult(IdentityAssertionFingerprintedEvidence):
    """Redacted result for one offline verification attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    verification_id: str = Field(min_length=1)
    assertion_id: str | None = None
    key_id: str | None = None
    issuer: str | None = None
    audience: str | None = None
    verified: bool = False
    rejected: bool = True
    primary_reason_code: IdentityAssertionReasonCode
    reason_codes: tuple[IdentityAssertionReasonCode, ...]
    claim_counts: IdentityAssertionClaimCounts
    assertion_fingerprint: str | None = None
    verified_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(
        cls,
        value: tuple[IdentityAssertionReasonCode, ...],
    ) -> tuple[IdentityAssertionReasonCode, ...]:
        return validate_reason_codes(value)

    @field_validator("verified_at")
    @classmethod
    def verified_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def result_state_must_match_reason_codes(self) -> IdentityAssertionVerificationResult:
        if self.verified == self.rejected:
            raise ValueError("exactly one of verified or rejected must be true")
        if self.verified and self.primary_reason_code != "identity_assertion_verified":
            raise ValueError("verified result must use identity_assertion_verified")
        if self.rejected and self.primary_reason_code == "identity_assertion_verified":
            raise ValueError("rejected result cannot use identity_assertion_verified")
        if self.primary_reason_code not in self.reason_codes:
            raise ValueError("primary_reason_code must be present in reason_codes")
        return self


class IdentityAssertionAuditEvent(IdentityAssertionFingerprintedEvidence):
    """Redacted audit event for an offline verification attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    event_id: str = Field(min_length=1)
    event_type: IdentityAssertionAuditEventType
    verification_id: str = Field(min_length=1)
    assertion_id_present: bool
    key_id: str | None = None
    issuer: str | None = None
    audience: str | None = None
    verified: bool = False
    rejected: bool = True
    reason_codes: tuple[IdentityAssertionReasonCode, ...]
    claim_counts: IdentityAssertionClaimCounts
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(
        cls,
        value: tuple[IdentityAssertionReasonCode, ...],
    ) -> tuple[IdentityAssertionReasonCode, ...]:
        return validate_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class IdentityAssertionProvenanceRecord(IdentityAssertionFingerprintedEvidence):
    """Redacted provenance for offline verification evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    provenance_id: str = Field(min_length=1)
    verification_id: str = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)
    verifier_name: str = "OfflineEd25519IdentityAssertionVerifier"
    verifier_version: str = VERIFICATION_SCHEMA_VERSION
    public_key_registry_key_count: int = Field(ge=0)
    canonicalization_reused: bool = True
    public_key_only_runtime: bool = True
    raw_assertion_stored: bool = False
    raw_signature_stored: bool = False
    full_public_key_stored: bool = False
    verified_claims_persisted: bool = False
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_refs")
    @classmethod
    def source_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_protected_material(item)
        return tuple(value)

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class IdentityAssertionDiagnosticSnapshot(IdentityAssertionFingerprintedEvidence):
    """Safe diagnostic state for the unintegrated verification core."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    snapshot_id: str = Field(min_length=1)
    verifier_name: str = "OfflineEd25519IdentityAssertionVerifier"
    fixed_algorithm_available: bool = True
    trusted_public_key_count: int = Field(ge=0)
    allowed_clock_skew_seconds: int = Field(ge=0, le=DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS)
    maximum_assertion_lifetime_seconds: int = Field(
        ge=1,
        le=MAXIMUM_ASSERTION_LIFETIME_SECONDS,
    )
    runtime_no_go_status: bool = True
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)


class IdentityAssertionVerificationBundle(IdentityAssertionFingerprintedEvidence):
    """Correlated verification result, audit event, provenance, and diagnostics."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    bundle_id: str = Field(min_length=1)
    verification_id: str = Field(min_length=1)
    result: IdentityAssertionVerificationResult
    audit_event: IdentityAssertionAuditEvent
    provenance: IdentityAssertionProvenanceRecord
    diagnostic_snapshot: IdentityAssertionDiagnosticSnapshot
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def nested_evidence_must_match_bundle(self) -> IdentityAssertionVerificationBundle:
        if self.result.verification_id != self.verification_id:
            raise ValueError("result verification_id must match bundle")
        if self.audit_event.verification_id != self.verification_id:
            raise ValueError("audit_event verification_id must match bundle")
        if self.provenance.verification_id != self.verification_id:
            raise ValueError("provenance verification_id must match bundle")
        if self.result.verified != self.audit_event.verified:
            raise ValueError("audit verified state must match result")
        return self


def validate_assertion_id(value: str) -> str:
    """Validate an assertion ID without accepting path or unicode forms."""

    if not isinstance(value, str) or not _ASSERTION_ID_RE.fullmatch(value):
        raise ValueError("assertion_id must be safe ASCII")
    return value


def validate_key_id(value: str) -> str:
    """Validate an exact public-key identifier with no fallback syntax."""

    if not isinstance(value, str) or not _KEY_ID_RE.fullmatch(value):
        raise ValueError("key_id must be safe ASCII")
    return value


def validate_reason_codes(
    value: tuple[IdentityAssertionReasonCode, ...],
) -> tuple[IdentityAssertionReasonCode, ...]:
    """Validate reason codes against the immutable registry."""

    if not value:
        raise ValueError("reason_codes cannot be empty")
    if len(set(value)) != len(value):
        raise ValueError("duplicate identity assertion reason code")
    unknown = [code for code in value if code not in ALLOWED_REASON_CODES]
    if unknown:
        raise ValueError("unknown identity assertion reason code")
    return tuple(value)


def normalize_utc_datetime(value: datetime) -> datetime:
    """Require timezone-aware UTC datetimes and normalize to datetime.UTC."""

    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError("datetime must be timezone-aware UTC")
    if offset.total_seconds() != 0:
        raise ValueError("datetime must use UTC offset")
    return value.astimezone(UTC)


def reject_protected_material(value: Any) -> None:
    """Reject protected material from assertion metadata and evidence."""

    _reject_protected_material(value)


def claim_counts_for_payload(
    payload: IdentityAssertionPayload | None,
) -> IdentityAssertionClaimCounts:
    """Return redacted claim counts for a payload, or zero counts for malformed input."""

    if payload is None:
        return IdentityAssertionClaimCounts(
            roles=0,
            permissions=0,
            security_scope=0,
            workspace_present=False,
            metadata_keys=0,
        )
    return IdentityAssertionClaimCounts(
        roles=len(payload.roles),
        permissions=len(payload.permissions),
        security_scope=len(payload.security_scope),
        workspace_present=payload.workspace_id is not None,
        metadata_keys=len(payload.metadata),
    )


def assertion_fingerprint(payload: IdentityAssertionPayload | None) -> str | None:
    """Return a payload-only fingerprint without signature or key ID material."""

    if payload is None:
        return None
    return sha256_fingerprint(payload.model_dump(mode="json"))


def _decode_base64url_unpadded(value: str, expected_length: int | None = None) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("base64url value is malformed")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("base64url value is malformed") from exc
    if "=" in value or not _BASE64URL_RE.fullmatch(value):
        raise ValueError("base64url value is malformed")
    if len(value) % 4 == 1:
        raise ValueError("base64url value is malformed")
    padded = value + ("=" * ((4 - len(value) % 4) % 4))
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (binascii.Error, ValueError) as exc:
        raise ValueError("base64url value is malformed") from exc
    recoded = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
    if recoded != value:
        raise ValueError("base64url value is malformed")
    if expected_length is not None and len(decoded) != expected_length:
        raise ValueError("base64url value length is invalid")
    return decoded


def _validate_nonempty_untrimmed_text(value: str, *, max_length: int) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise ValueError("identity assertion text is invalid")
    if value.strip() != value:
        raise ValueError("identity assertion text must not contain trim whitespace")
    if any(ch.isspace() for ch in value):
        raise ValueError("identity assertion text must not contain whitespace")
    return value


def _validate_claims(
    value: object,
    *,
    field_name: str,
    max_items: int,
    max_length: int,
) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str | bytes | bytearray) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    items = tuple(value)
    if len(items) > max_items:
        raise ValueError(f"{field_name} exceeds maximum count")
    cleaned: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} entries must be strings")
        cleaned.append(_validate_nonempty_untrimmed_text(item, max_length=max_length))
    if len(set(cleaned)) != len(cleaned):
        raise ValueError(f"{field_name} entries must be unique")
    return tuple(sorted(cleaned))


def _freeze_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return _FrozenDict({key: _freeze_value(nested) for key, nested in value.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("metadata must contain finite floats")
        return value
    if isinstance(value, str | int | bool) or value is None:
        return value
    raise ValueError("metadata contains unsupported value")


def _reject_protected_material(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError("metadata keys must be strings")
            normalized_key = _normalize_marker(key)
            if _contains_protected_marker(normalized_key, _PROTECTED_KEY_PARTS):
                raise ValueError("protected material is not allowed in identity assertion evidence")
            _reject_protected_material(nested)
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for item in value:
            _reject_protected_material(item)
        return
    if isinstance(value, BaseModel):
        _reject_protected_material(value.model_dump(mode="python"))
        return
    if isinstance(value, bytes | bytearray):
        raise ValueError("bytes are not allowed in identity assertion metadata")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("metadata must contain finite floats")
    if isinstance(value, str):
        normalized_value = _normalize_marker(value)
        if _contains_protected_marker(normalized_value, _PROTECTED_VALUE_MARKERS):
            raise ValueError("protected material is not allowed in identity assertion evidence")
        return
    if isinstance(value, int | bool) or value is None:
        return
    raise ValueError("metadata contains unsupported value")


def _contains_protected_marker(value: str, markers: set[str] | tuple[str, ...]) -> bool:
    return any(_normalize_marker(marker) in value for marker in markers)


def _normalize_marker(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("-", "_").replace(" ", "_")
    return normalized.lower()


def _require_runtime_boundary(model: object) -> None:
    true_fields = (
        "authorization_expires_on_aion_162_merge",
        "offline_identity_assertion_verification_implemented",
        "canonical_payload_enabled",
        "domain_separation_enabled",
        "public_key_registry_enabled",
        "replay_protection_required_before_request_integration",
        "redacted",
    )
    for field_name in true_fields:
        if not bool(getattr(model, field_name, True)):
            raise ValueError(f"{field_name} must be true")
    false_fields = (
        "authorization_reusable",
        "runtime_private_key_material_present",
        "request_authenticated",
        "actor_context_applied",
        "request_identity_context_applied",
        "runtime_effect",
        "runtime_integration_allowed",
        "replay_check_performed",
        "production_auth_runtime_enabled",
        "identity_verification_enabled",
        "authenticated_requests_enabled",
        "identity_assertion_header_parsing_enabled",
        "authorization_header_parsing_enabled",
        "cookie_parsing_enabled",
        "identity_assertion_middleware_registered",
        "external_identity_provider_enabled",
        "jwks_network_fetch_enabled",
        "provider_discovery_enabled",
        "external_calls_enabled",
        "identity_assertion_endpoint_enabled",
        "runtime_api_routes_added",
        "openapi_security_scheme_added",
        "sdk_runtime_resource_added",
        "cli_runtime_command_added",
        "new_package_manifest_added",
        "lockfiles_added",
        "migrations_added",
        "v02_tag_created",
        "v02_release_created",
    )
    for field_name in false_fields:
        if bool(getattr(model, field_name, False)):
            raise ValueError(f"{field_name} must be false")


def _fingerprint_for_model(model: BaseModel) -> str:
    payload = model.model_dump(mode="json", exclude={"fingerprint"})
    return sha256_fingerprint(payload)


__all__ = [
    "ALLOWED_REASON_CODES",
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CANONICALIZATION_VERSION",
    "CANDIDATE_ID",
    "DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS",
    "DOMAIN_SEPARATOR",
    "FIXED_ALGORITHM",
    "IMPLEMENTATION_TASK",
    "MANDATORY_RUNTIME_BOUNDARY_REASON_CODES",
    "MAXIMUM_ASSERTION_LIFETIME_SECONDS",
    "MAXIMUM_METADATA_CANONICAL_BYTES",
    "MAXIMUM_PAYLOAD_CANONICAL_BYTES",
    "OFFLINE_IDENTITY_ASSERTION_VERIFICATION_STATE",
    "PARENT_AUTHORIZATION_TRANSACTION_ID",
    "PAYLOAD_SCHEMA_VERSION",
    "PUBLIC_KEY_SCHEMA_VERSION",
    "REASON_CODE_REGISTRY_VERSION",
    "SCHEMA_VERSION",
    "SUCCESS_REASON_CODES",
    "VERIFICATION_SCHEMA_VERSION",
    "WORKSTREAM",
    "IdentityAssertionAuditEvent",
    "IdentityAssertionAuditEventType",
    "IdentityAssertionClaimCounts",
    "IdentityAssertionDiagnosticSnapshot",
    "IdentityAssertionEnvelope",
    "IdentityAssertionPayload",
    "IdentityAssertionProvenanceRecord",
    "IdentityAssertionReasonCode",
    "IdentityAssertionVerificationBundle",
    "IdentityAssertionVerificationPolicy",
    "IdentityAssertionVerificationResult",
    "TrustedIdentityAssertionPublicKey",
    "assertion_fingerprint",
    "claim_counts_for_payload",
    "normalize_utc_datetime",
    "reject_protected_material",
    "validate_assertion_id",
    "validate_key_id",
    "validate_reason_codes",
]
