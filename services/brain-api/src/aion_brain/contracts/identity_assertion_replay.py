"""Persistent identity assertion replay-protection contracts."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal, NoReturn

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.identity_assertion import (
    IdentityAssertionVerificationBundle,
    normalize_utc_datetime,
    reject_protected_material,
)
from aion_brain.production_auth.canonical import sha256_fingerprint

REPLAY_KEY_SCHEMA_VERSION = "identity-assertion-replay-key/v1"
REPLAY_RECORD_SCHEMA_VERSION = "identity-assertion-replay-record/v1"
REPLAY_POLICY_SCHEMA_VERSION = "identity-assertion-replay-policy/v1"
REPLAY_RESULT_SCHEMA_VERSION = "identity-assertion-replay-result/v1"
REPLAY_EVIDENCE_SCHEMA_VERSION = "identity-assertion-replay-evidence/v1"
REPLAY_PIPELINE_SCHEMA_VERSION = "identity-assertion-replay-pipeline/v1"
REPLAY_REASON_CODE_REGISTRY_VERSION = "identity-assertion-replay-reason-codes/v1"
REPLAY_KEY_DOMAIN_SEPARATOR = b"AION-IDENTITY-ASSERTION-REPLAY-V1\0"
ISSUER_FINGERPRINT_SCHEMA_VERSION = "identity-assertion-issuer-fingerprint/v1"

AUTHORIZATION_TRANSACTION_ID = "AION-163-PA-0007"
APPROVAL_RECORD_ID = "AION-163-PA-0007"
PARENT_AUTHORIZATION_TRANSACTION_ID = "AION-161-PA-0006"
CANDIDATE_ID = "production-auth-identity-assertion-replay-protection"
WORKSTREAM = "production-auth-verification-integrity"
IMPLEMENTATION_TASK = "AION-164"
AUTHORIZATION_SCOPE = "persistent-identity-assertion-replay-protection-core"

DEFAULT_MINIMUM_RETENTION_SECONDS = 86_400
DEFAULT_MAXIMUM_RETENTION_SECONDS = 604_800
DEFAULT_CLEANUP_BATCH_SIZE = 1_000
DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS = 30
TABLE_NAME = "aion_identity_assertion_replay_claims"
IDENTITY_ASSERTION_REPLAY_STATE: Literal["implemented_unintegrated"] = (
    "implemented_unintegrated"
)

IdentityAssertionReplayRepositoryOutcome = Literal[
    "claimed",
    "replay_detected",
    "identifier_collision",
    "repository_unavailable",
    "schema_unavailable",
]
IdentityAssertionReplayProtectionOutcome = Literal[
    "claimed",
    "replay_detected",
    "identifier_collision",
    "verification_rejected",
    "verification_bundle_mismatch",
    "assertion_expired",
    "repository_unavailable",
    "schema_unavailable",
]
OfflineIdentityAssertionVerificationPipelineOutcome = Literal[
    "verified_once",
    "replay_detected",
    "identifier_collision",
    "verification_rejected",
    "verification_bundle_mismatch",
    "assertion_expired",
    "repository_unavailable",
    "schema_unavailable",
]
IdentityAssertionReplayAuditEventType = Literal[
    "identity_assertion_replay_claim_succeeded",
    "identity_assertion_replay_detected",
    "identity_assertion_identifier_collision_detected",
    "identity_assertion_replay_failed_closed",
    "identity_assertion_replay_cleanup_completed",
]
IdentityAssertionReplayReasonCode = Literal[
    "identity_assertion_replay_claimed",
    "identity_assertion_replay_detected",
    "identity_assertion_identifier_collision",
    "identity_assertion_verification_required",
    "identity_assertion_verification_rejected",
    "identity_assertion_verification_bundle_mismatch",
    "identity_assertion_expired_before_replay_claim",
    "identity_assertion_replay_repository_unavailable",
    "identity_assertion_replay_schema_unavailable",
    "identity_assertion_replay_record_retained",
    "identity_assertion_replay_cleanup_completed",
    "identity_assertion_replay_cleanup_failed_closed",
    "identity_assertion_replay_policy_invalid",
    "replay_protection_performed",
    "replay_protection_failed_closed",
    "request_authentication_not_applied",
    "actor_context_not_applied",
    "request_identity_context_not_applied",
    "runtime_integration_disabled",
    "runtime_authentication_disabled",
    "authorization_scope_implementation_only",
    "runtime_no_go_status_locked",
]

ALLOWED_REASON_CODES: tuple[IdentityAssertionReplayReasonCode, ...] = (
    "identity_assertion_replay_claimed",
    "identity_assertion_replay_detected",
    "identity_assertion_identifier_collision",
    "identity_assertion_verification_required",
    "identity_assertion_verification_rejected",
    "identity_assertion_verification_bundle_mismatch",
    "identity_assertion_expired_before_replay_claim",
    "identity_assertion_replay_repository_unavailable",
    "identity_assertion_replay_schema_unavailable",
    "identity_assertion_replay_record_retained",
    "identity_assertion_replay_cleanup_completed",
    "identity_assertion_replay_cleanup_failed_closed",
    "identity_assertion_replay_policy_invalid",
    "replay_protection_performed",
    "replay_protection_failed_closed",
    "request_authentication_not_applied",
    "actor_context_not_applied",
    "request_identity_context_not_applied",
    "runtime_integration_disabled",
    "runtime_authentication_disabled",
    "authorization_scope_implementation_only",
    "runtime_no_go_status_locked",
)
MANDATORY_RUNTIME_BOUNDARY_REASON_CODES: tuple[IdentityAssertionReplayReasonCode, ...] = (
    "request_authentication_not_applied",
    "actor_context_not_applied",
    "request_identity_context_not_applied",
    "runtime_integration_disabled",
    "runtime_authentication_disabled",
    "authorization_scope_implementation_only",
    "runtime_no_go_status_locked",
)
REPOSITORY_REASON_CODES: dict[
    IdentityAssertionReplayRepositoryOutcome,
    tuple[IdentityAssertionReplayReasonCode, ...],
] = {
    "claimed": (
        "identity_assertion_replay_claimed",
        "identity_assertion_replay_record_retained",
        "replay_protection_performed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
    "replay_detected": (
        "identity_assertion_replay_detected",
        "replay_protection_failed_closed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
    "identifier_collision": (
        "identity_assertion_identifier_collision",
        "replay_protection_failed_closed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
    "repository_unavailable": (
        "identity_assertion_replay_repository_unavailable",
        "replay_protection_failed_closed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
    "schema_unavailable": (
        "identity_assertion_replay_schema_unavailable",
        "replay_protection_failed_closed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
}
PROTECTION_REASON_CODES: dict[
    IdentityAssertionReplayProtectionOutcome,
    tuple[IdentityAssertionReplayReasonCode, ...],
] = {
    "claimed": (
        "identity_assertion_verification_required",
        *REPOSITORY_REASON_CODES["claimed"],
    ),
    "replay_detected": (
        "identity_assertion_verification_required",
        *REPOSITORY_REASON_CODES["replay_detected"],
    ),
    "identifier_collision": (
        "identity_assertion_verification_required",
        *REPOSITORY_REASON_CODES["identifier_collision"],
    ),
    "repository_unavailable": (
        "identity_assertion_verification_required",
        *REPOSITORY_REASON_CODES["repository_unavailable"],
    ),
    "schema_unavailable": (
        "identity_assertion_verification_required",
        *REPOSITORY_REASON_CODES["schema_unavailable"],
    ),
    "verification_rejected": (
        "identity_assertion_verification_required",
        "identity_assertion_verification_rejected",
        "replay_protection_failed_closed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
    "verification_bundle_mismatch": (
        "identity_assertion_verification_required",
        "identity_assertion_verification_bundle_mismatch",
        "replay_protection_failed_closed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
    "assertion_expired": (
        "identity_assertion_verification_required",
        "identity_assertion_expired_before_replay_claim",
        "replay_protection_failed_closed",
        *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    ),
}
_HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")


class _FrozenDict(dict[str, Any]):
    """Small immutable dict for replay evidence metadata."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("identity assertion replay metadata is immutable")

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


class IdentityAssertionReplayPolicy(BaseModel):
    """Replay retention and cleanup policy for offline-only verification evidence."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: str = REPLAY_POLICY_SCHEMA_VERSION
    minimum_retention_seconds: int = Field(
        default=DEFAULT_MINIMUM_RETENTION_SECONDS,
        ge=300,
        le=DEFAULT_MAXIMUM_RETENTION_SECONDS,
    )
    maximum_retention_seconds: int = Field(
        default=DEFAULT_MAXIMUM_RETENTION_SECONDS,
        ge=300,
        le=2_592_000,
    )
    cleanup_batch_size: int = Field(default=DEFAULT_CLEANUP_BATCH_SIZE, ge=1, le=10_000)
    allowed_clock_skew_seconds: int = Field(
        default=DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS,
        ge=0,
        le=DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS,
    )

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != REPLAY_POLICY_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {REPLAY_POLICY_SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def maximum_must_cover_minimum(self) -> IdentityAssertionReplayPolicy:
        if self.maximum_retention_seconds < self.minimum_retention_seconds:
            raise ValueError("maximum_retention_seconds must cover minimum_retention_seconds")
        return self


class IdentityAssertionReplayVersionedEvidence(BaseModel):
    """Shared AION-164 authorization and runtime-hold fields."""

    schema_version: str = REPLAY_EVIDENCE_SCHEMA_VERSION
    canonicalization_version: str = "production-auth-canonical-json/v1"
    reason_code_registry_version: str = REPLAY_REASON_CODE_REGISTRY_VERSION
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    candidate_id: str = CANDIDATE_ID
    workstream: str = WORKSTREAM
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_164_merge: bool = True
    identity_assertion_replay_protection_implemented: bool = True
    identity_assertion_replay_protection_state: Literal[
        "implemented_unintegrated"
    ] = IDENTITY_ASSERTION_REPLAY_STATE
    persistent_replay_ledger_available: bool = True
    persistent_replay_ledger_enabled: bool = True
    atomic_unique_insert_enabled: bool = True
    domain_separated_replay_key_enabled: bool = True
    identifier_collision_detection_enabled: bool = True
    insert_first_claim_enabled: bool = True
    unique_replay_key_constraint_enabled: bool = True
    dedicated_replay_metadata_used: bool = True
    auto_create_default: bool = False
    test_auto_create_supported: bool = True
    production_schema_auto_create_enabled: bool = False
    dependency_changes_added: int = 0
    idempotency_service_reused_as_replay_ledger: bool = False
    raw_issuer_persisted: bool = False
    raw_assertion_id_persisted: bool = False
    raw_assertion_stored: bool = False
    raw_signature_stored: bool = False
    verified_claims_persisted: bool = False
    request_authenticated: bool = False
    request_authentication_applied: bool = False
    request_integration_enabled: bool = False
    actor_context_applied: bool = False
    request_identity_context_applied: bool = False
    runtime_effect: bool = False
    runtime_integration_allowed: bool = False
    kernel_container_registration_enabled: bool = False
    middleware_integration_enabled: bool = False
    replay_repository_runtime_registered: bool = False
    replay_protection_core_runtime_enabled: bool = False
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
    background_cleanup_scheduler_enabled: bool = False
    in_memory_runtime_replay_store_enabled: bool = False
    new_package_manifest_added: bool = False
    lockfiles_added: bool = False
    migrations_added: bool = False
    v02_tag_created: bool = False
    v02_release_created: bool = False
    redacted: bool = True

    @model_validator(mode="after")
    def runtime_boundary_must_hold(self) -> IdentityAssertionReplayVersionedEvidence:
        _require_runtime_boundary(self)
        return self


class IdentityAssertionReplayFingerprintedEvidence(IdentityAssertionReplayVersionedEvidence):
    """Replay evidence with deterministic redacted fingerprints."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(
        self,
    ) -> IdentityAssertionReplayFingerprintedEvidence:
        expected = _fingerprint_for_model(self)
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical replay evidence payload")
        return self


class IdentityAssertionReplayRecord(BaseModel):
    """Safe persistent replay ledger record: hashes and timestamps only."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = REPLAY_RECORD_SCHEMA_VERSION
    replay_key: str
    issuer_fingerprint: str
    assertion_fingerprint: str
    claimed_at: datetime
    assertion_expires_at: datetime
    retain_until: datetime
    created_at: datetime

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != REPLAY_RECORD_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {REPLAY_RECORD_SCHEMA_VERSION}")
        return value

    @field_validator("replay_key", "issuer_fingerprint", "assertion_fingerprint")
    @classmethod
    def fingerprints_must_be_lowercase_hex(cls, value: str) -> str:
        if not isinstance(value, str) or not _HEX_64_RE.fullmatch(value):
            raise ValueError("replay identifiers must be 64 lowercase hexadecimal characters")
        return value

    @field_validator(
        "claimed_at",
        "assertion_expires_at",
        "retain_until",
        "created_at",
    )
    @classmethod
    def datetimes_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def record_must_be_atomic_and_retained(self) -> IdentityAssertionReplayRecord:
        if self.claimed_at > self.assertion_expires_at:
            raise ValueError("claimed_at must not be after assertion_expires_at")
        if self.created_at != self.claimed_at:
            raise ValueError("created_at must match claimed_at")
        if self.retain_until < self.assertion_expires_at:
            raise ValueError("retain_until must not precede assertion_expires_at")
        if self.retain_until < self.claimed_at:
            raise ValueError("retain_until must not precede claimed_at")
        return self


class IdentityAssertionReplayRepositoryResult(IdentityAssertionReplayFingerprintedEvidence):
    """Repository claim outcome with fail-closed reason codes."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = REPLAY_RESULT_SCHEMA_VERSION
    operation_id: str = Field(min_length=1)
    outcome: IdentityAssertionReplayRepositoryOutcome
    claim_created: bool
    replay_detected: bool
    identifier_collision: bool
    repository_available: bool
    schema_available: bool
    fail_closed: bool
    existing_assertion_fingerprint_matches: bool
    record: IdentityAssertionReplayRecord | None = None
    primary_reason_code: IdentityAssertionReplayReasonCode
    reason_codes: tuple[IdentityAssertionReplayReasonCode, ...]
    created_at: datetime

    @field_validator("schema_version")
    @classmethod
    def result_schema_version_must_match(cls, value: str) -> str:
        if value != REPLAY_RESULT_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {REPLAY_RESULT_SCHEMA_VERSION}")
        return value

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_known(
        cls,
        value: tuple[IdentityAssertionReplayReasonCode, ...],
    ) -> tuple[IdentityAssertionReplayReasonCode, ...]:
        return validate_replay_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def repository_state_must_match_outcome(self) -> IdentityAssertionReplayRepositoryResult:
        _require_reason_code(self.reason_codes, self.primary_reason_code)
        if self.primary_reason_code != _primary_repository_reason_code(self.outcome):
            raise ValueError("primary_reason_code must match repository outcome")
        if self.outcome == "claimed":
            _require_state(self.claim_created and not self.replay_detected)
            _require_state(not self.identifier_collision and not self.fail_closed)
            _require_state(self.repository_available and self.schema_available)
            _require_state(not self.existing_assertion_fingerprint_matches)
            _require_state(self.record is not None)
        elif self.outcome == "replay_detected":
            _require_state(not self.claim_created and self.replay_detected)
            _require_state(not self.identifier_collision and self.fail_closed)
            _require_state(self.existing_assertion_fingerprint_matches)
            _require_state(self.repository_available and self.schema_available)
            _require_state(self.record is not None)
        elif self.outcome == "identifier_collision":
            _require_state(not self.claim_created and not self.replay_detected)
            _require_state(self.identifier_collision and self.fail_closed)
            _require_state(not self.existing_assertion_fingerprint_matches)
            _require_state(self.repository_available and self.schema_available)
            _require_state(self.record is not None)
        elif self.outcome == "schema_unavailable":
            _require_failure_result(self)
            _require_state(not self.schema_available)
        elif self.outcome == "repository_unavailable":
            _require_failure_result(self)
            _require_state(not self.repository_available)
        return self


class IdentityAssertionReplayProtectionResult(IdentityAssertionReplayFingerprintedEvidence):
    """Replay protection result for one verified assertion."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = REPLAY_RESULT_SCHEMA_VERSION
    replay_protection_id: str = Field(min_length=1)
    outcome: IdentityAssertionReplayProtectionOutcome
    cryptographic_verification_required: bool = True
    cryptographic_verification_verified: bool
    replay_check_performed: bool
    replay_protection_passed: bool
    claim_created: bool
    replay_detected: bool
    identifier_collision: bool
    repository_available: bool
    schema_available: bool
    fail_closed: bool
    replay_key: str | None = None
    issuer_fingerprint: str | None = None
    assertion_fingerprint: str | None = None
    retain_until: datetime | None = None
    primary_reason_code: IdentityAssertionReplayReasonCode
    reason_codes: tuple[IdentityAssertionReplayReasonCode, ...]
    checked_at: datetime

    @field_validator("schema_version")
    @classmethod
    def protection_schema_version_must_match(cls, value: str) -> str:
        if value != REPLAY_RESULT_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {REPLAY_RESULT_SCHEMA_VERSION}")
        return value

    @field_validator("replay_key", "issuer_fingerprint", "assertion_fingerprint")
    @classmethod
    def optional_fingerprints_must_be_lowercase_hex(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _HEX_64_RE.fullmatch(value):
            raise ValueError("replay evidence identifiers must be 64 lowercase hex")
        return value

    @field_validator("reason_codes")
    @classmethod
    def protection_reason_codes_must_be_known(
        cls,
        value: tuple[IdentityAssertionReplayReasonCode, ...],
    ) -> tuple[IdentityAssertionReplayReasonCode, ...]:
        return validate_replay_reason_codes(value)

    @field_validator("checked_at", "retain_until")
    @classmethod
    def optional_datetimes_must_be_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else normalize_utc_datetime(value)

    @model_validator(mode="after")
    def protection_state_must_match_outcome(self) -> IdentityAssertionReplayProtectionResult:
        _require_state(self.cryptographic_verification_required)
        _require_reason_code(self.reason_codes, self.primary_reason_code)
        if self.primary_reason_code != _primary_protection_reason_code(self.outcome):
            raise ValueError("primary_reason_code must match protection outcome")
        if self.outcome == "claimed":
            _require_state(self.cryptographic_verification_verified)
            _require_state(self.replay_check_performed and self.replay_protection_passed)
            _require_state(self.claim_created and not self.replay_detected)
            _require_state(not self.identifier_collision and not self.fail_closed)
            _require_state(self.repository_available and self.schema_available)
        else:
            _require_state(not self.replay_protection_passed and self.fail_closed)
        if self.outcome == "verification_rejected":
            _require_state(not self.cryptographic_verification_verified)
            _require_state(not self.replay_check_performed)
        elif self.outcome == "verification_bundle_mismatch":
            _require_state(self.cryptographic_verification_verified)
            _require_state(not self.replay_check_performed)
        elif self.outcome == "assertion_expired":
            _require_state(self.cryptographic_verification_verified)
            _require_state(not self.replay_check_performed)
        elif self.outcome == "replay_detected":
            _require_state(self.cryptographic_verification_verified and self.replay_check_performed)
            _require_state(not self.claim_created and self.replay_detected)
            _require_state(not self.identifier_collision)
        elif self.outcome == "identifier_collision":
            _require_state(self.cryptographic_verification_verified and self.replay_check_performed)
            _require_state(not self.claim_created and not self.replay_detected)
            _require_state(self.identifier_collision)
        elif self.outcome == "schema_unavailable":
            _require_state(self.cryptographic_verification_verified and self.replay_check_performed)
            _require_state(not self.claim_created and not self.schema_available)
        elif self.outcome == "repository_unavailable":
            _require_state(self.cryptographic_verification_verified and self.replay_check_performed)
            _require_state(not self.claim_created and not self.repository_available)
        return self


class IdentityAssertionReplayAuditEvent(IdentityAssertionReplayFingerprintedEvidence):
    """Redacted audit event for a replay protection decision."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    event_id: str = Field(min_length=1)
    event_type: IdentityAssertionReplayAuditEventType
    replay_protection_id: str = Field(min_length=1)
    replay_key: str | None = None
    issuer_fingerprint: str | None = None
    assertion_fingerprint: str | None = None
    outcome: IdentityAssertionReplayProtectionOutcome
    claim_created: bool
    replay_detected: bool
    identifier_collision: bool
    repository_available: bool
    schema_available: bool
    retain_until: datetime | None = None
    reason_codes: tuple[IdentityAssertionReplayReasonCode, ...]
    created_at: datetime

    @field_validator("reason_codes")
    @classmethod
    def audit_reason_codes_must_be_known(
        cls,
        value: tuple[IdentityAssertionReplayReasonCode, ...],
    ) -> tuple[IdentityAssertionReplayReasonCode, ...]:
        return validate_replay_reason_codes(value)

    @field_validator("created_at", "retain_until")
    @classmethod
    def audit_datetimes_must_be_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else normalize_utc_datetime(value)


class IdentityAssertionReplayProvenanceRecord(IdentityAssertionReplayFingerprintedEvidence):
    """Redacted provenance for replay-protection evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    provenance_id: str = Field(min_length=1)
    replay_protection_id: str = Field(min_length=1)
    replay_key: str | None = None
    issuer_fingerprint: str | None = None
    assertion_fingerprint: str | None = None
    repository_implementation_name: str = "IdentityAssertionReplayRepository"
    atomic_insert: bool = True
    unique_constraint: bool = True
    outcome: IdentityAssertionReplayProtectionOutcome
    reason_codes: tuple[IdentityAssertionReplayReasonCode, ...]
    created_at: datetime

    @field_validator("reason_codes")
    @classmethod
    def provenance_reason_codes_must_be_known(
        cls,
        value: tuple[IdentityAssertionReplayReasonCode, ...],
    ) -> tuple[IdentityAssertionReplayReasonCode, ...]:
        return validate_replay_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def provenance_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def provenance_must_match_boundary(self) -> IdentityAssertionReplayProvenanceRecord:
        _require_state(self.atomic_insert)
        _require_state(self.unique_constraint)
        return self


class IdentityAssertionReplayDiagnosticSnapshot(IdentityAssertionReplayFingerprintedEvidence):
    """Safe diagnostic state for the unintegrated replay core."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    snapshot_id: str = Field(min_length=1)
    replay_protection_id: str = Field(min_length=1)
    table_name: str = TABLE_NAME
    repository_available: bool
    schema_available: bool
    minimum_retention_seconds: int = Field(ge=300, le=DEFAULT_MAXIMUM_RETENTION_SECONDS)
    maximum_retention_seconds: int = Field(ge=300, le=2_592_000)
    cleanup_batch_size: int = Field(ge=1, le=10_000)
    allowed_clock_skew_seconds: int = Field(ge=0, le=DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS)
    runtime_no_go_status: bool = True
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def diagnostic_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def diagnostic_must_match_boundary(self) -> IdentityAssertionReplayDiagnosticSnapshot:
        if self.table_name != TABLE_NAME:
            raise ValueError(f"table_name must be {TABLE_NAME}")
        if self.maximum_retention_seconds < self.minimum_retention_seconds:
            raise ValueError("maximum_retention_seconds must cover minimum_retention_seconds")
        return self


class IdentityAssertionReplayProtectionBundle(IdentityAssertionReplayFingerprintedEvidence):
    """Correlated replay result, audit event, provenance, and diagnostics."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    bundle_id: str = Field(min_length=1)
    replay_protection_id: str = Field(min_length=1)
    result: IdentityAssertionReplayProtectionResult
    repository_result: IdentityAssertionReplayRepositoryResult | None = None
    audit_event: IdentityAssertionReplayAuditEvent
    provenance: IdentityAssertionReplayProvenanceRecord
    diagnostic_snapshot: IdentityAssertionReplayDiagnosticSnapshot
    verification_bundle_fingerprint: str = Field(min_length=64, max_length=64)
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at")
    @classmethod
    def bundle_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def bundle_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def nested_evidence_must_match_bundle(self) -> IdentityAssertionReplayProtectionBundle:
        if self.result.replay_protection_id != self.replay_protection_id:
            raise ValueError("result replay_protection_id must match bundle")
        if self.audit_event.replay_protection_id != self.replay_protection_id:
            raise ValueError("audit_event replay_protection_id must match bundle")
        if self.provenance.replay_protection_id != self.replay_protection_id:
            raise ValueError("provenance replay_protection_id must match bundle")
        if self.diagnostic_snapshot.replay_protection_id != self.replay_protection_id:
            raise ValueError("diagnostic_snapshot replay_protection_id must match bundle")
        if self.repository_result is not None:
            if self.repository_result.outcome != self.result.outcome:
                raise ValueError("repository outcome must match protection outcome")
        return self


class OfflineIdentityAssertionVerificationPipelineResult(
    IdentityAssertionReplayFingerprintedEvidence,
):
    """Combined offline verification plus replay-protection pipeline result."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = REPLAY_PIPELINE_SCHEMA_VERSION
    pipeline_id: str = Field(min_length=1)
    replay_protection_id: str | None = None
    cryptographic_verified: bool
    replay_check_performed: bool
    replay_detected: bool
    identifier_collision: bool
    verification_and_replay_checks_passed: bool
    fail_closed: bool
    outcome: OfflineIdentityAssertionVerificationPipelineOutcome
    verification_bundle_fingerprint: str = Field(min_length=64, max_length=64)
    replay_bundle_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)
    reason_codes: tuple[IdentityAssertionReplayReasonCode, ...]
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def pipeline_schema_version_must_match(cls, value: str) -> str:
        if value != REPLAY_PIPELINE_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {REPLAY_PIPELINE_SCHEMA_VERSION}")
        return value

    @field_validator("reason_codes")
    @classmethod
    def pipeline_reason_codes_must_be_known(
        cls,
        value: tuple[IdentityAssertionReplayReasonCode, ...],
    ) -> tuple[IdentityAssertionReplayReasonCode, ...]:
        return validate_replay_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def pipeline_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def pipeline_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def pipeline_state_must_match_outcome(
        self,
    ) -> OfflineIdentityAssertionVerificationPipelineResult:
        if self.outcome == "verified_once":
            _require_state(self.cryptographic_verified)
            _require_state(self.replay_check_performed)
            _require_state(not self.replay_detected and not self.identifier_collision)
            _require_state(self.verification_and_replay_checks_passed and not self.fail_closed)
        elif self.outcome == "verification_rejected":
            _require_state(not self.cryptographic_verified)
            _require_state(not self.replay_check_performed)
            _require_state(not self.verification_and_replay_checks_passed and self.fail_closed)
        else:
            _require_state(self.cryptographic_verified)
            _require_state(self.replay_check_performed)
            _require_state(not self.verification_and_replay_checks_passed and self.fail_closed)
        return self


class OfflineIdentityAssertionVerificationPipelineBundle(
    IdentityAssertionReplayFingerprintedEvidence,
):
    """Correlated verifier and replay-protection bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: str = REPLAY_PIPELINE_SCHEMA_VERSION
    bundle_id: str = Field(min_length=1)
    pipeline_id: str = Field(min_length=1)
    result: OfflineIdentityAssertionVerificationPipelineResult
    verification_bundle: IdentityAssertionVerificationBundle
    replay_bundle: IdentityAssertionReplayProtectionBundle | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def pipeline_bundle_schema_version_must_match(cls, value: str) -> str:
        if value != REPLAY_PIPELINE_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {REPLAY_PIPELINE_SCHEMA_VERSION}")
        return value

    @field_validator("created_at")
    @classmethod
    def pipeline_bundle_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @field_validator("metadata")
    @classmethod
    def pipeline_bundle_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def pipeline_bundle_must_match_result(
        self,
    ) -> OfflineIdentityAssertionVerificationPipelineBundle:
        if self.result.pipeline_id != self.pipeline_id:
            raise ValueError("result pipeline_id must match bundle")
        if self.replay_bundle is None:
            if self.result.replay_check_performed:
                raise ValueError("replay bundle required when replay is performed")
        elif self.replay_bundle.replay_protection_id != self.result.replay_protection_id:
            raise ValueError("replay bundle must match result")
        return self


def validate_replay_reason_codes(
    value: tuple[IdentityAssertionReplayReasonCode, ...],
) -> tuple[IdentityAssertionReplayReasonCode, ...]:
    """Validate replay reason codes and mandatory runtime boundary reason codes."""

    if not value:
        raise ValueError("reason_codes cannot be empty")
    if len(set(value)) != len(value):
        raise ValueError("duplicate identity assertion replay reason code")
    unknown = [code for code in value if code not in ALLOWED_REASON_CODES]
    if unknown:
        raise ValueError("unknown identity assertion replay reason code")
    for mandatory in MANDATORY_RUNTIME_BOUNDARY_REASON_CODES:
        if mandatory not in value:
            raise ValueError("mandatory runtime boundary replay reason code missing")
    return tuple(value)


def repository_reason_codes(
    outcome: IdentityAssertionReplayRepositoryOutcome,
) -> tuple[IdentityAssertionReplayReasonCode, ...]:
    """Return immutable repository reason codes for an outcome."""

    return tuple(REPOSITORY_REASON_CODES[outcome])


def protection_reason_codes(
    outcome: IdentityAssertionReplayProtectionOutcome,
) -> tuple[IdentityAssertionReplayReasonCode, ...]:
    """Return immutable protection reason codes for an outcome."""

    return tuple(PROTECTION_REASON_CODES[outcome])


def _primary_repository_reason_code(
    outcome: IdentityAssertionReplayRepositoryOutcome,
) -> IdentityAssertionReplayReasonCode:
    return REPOSITORY_REASON_CODES[outcome][0]


def _primary_protection_reason_code(
    outcome: IdentityAssertionReplayProtectionOutcome,
) -> IdentityAssertionReplayReasonCode:
    return PROTECTION_REASON_CODES[outcome][0]


def _require_reason_code(
    reason_codes: tuple[IdentityAssertionReplayReasonCode, ...],
    expected: IdentityAssertionReplayReasonCode,
) -> None:
    if expected not in reason_codes:
        raise ValueError("primary replay reason code must be present")


def _require_failure_result(result: IdentityAssertionReplayRepositoryResult) -> None:
    _require_state(not result.claim_created)
    _require_state(not result.replay_detected)
    _require_state(not result.identifier_collision)
    _require_state(result.fail_closed)
    _require_state(result.record is None)


def _require_state(value: bool) -> None:
    if not value:
        raise ValueError("replay outcome state is inconsistent")


def _freeze_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return _FrozenDict({key: _freeze_value(nested) for key, nested in value.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("metadata contains non-finite float")
        return value
    if isinstance(value, str | int | bool) or value is None:
        return value
    raise ValueError("metadata contains unsupported value")


def _require_runtime_boundary(model: object) -> None:
    true_fields = (
        "authorization_expires_on_aion_164_merge",
        "identity_assertion_replay_protection_implemented",
        "persistent_replay_ledger_available",
        "persistent_replay_ledger_enabled",
        "atomic_unique_insert_enabled",
        "domain_separated_replay_key_enabled",
        "identifier_collision_detection_enabled",
        "insert_first_claim_enabled",
        "unique_replay_key_constraint_enabled",
        "dedicated_replay_metadata_used",
        "test_auto_create_supported",
        "redacted",
    )
    for field_name in true_fields:
        if not bool(getattr(model, field_name, True)):
            raise ValueError(f"{field_name} must be true")
    false_fields = (
        "authorization_reusable",
        "auto_create_default",
        "production_schema_auto_create_enabled",
        "idempotency_service_reused_as_replay_ledger",
        "raw_issuer_persisted",
        "raw_assertion_id_persisted",
        "raw_assertion_stored",
        "raw_signature_stored",
        "verified_claims_persisted",
        "request_authenticated",
        "request_authentication_applied",
        "request_integration_enabled",
        "actor_context_applied",
        "request_identity_context_applied",
        "runtime_effect",
        "runtime_integration_allowed",
        "kernel_container_registration_enabled",
        "middleware_integration_enabled",
        "replay_repository_runtime_registered",
        "replay_protection_core_runtime_enabled",
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
        "background_cleanup_scheduler_enabled",
        "in_memory_runtime_replay_store_enabled",
        "new_package_manifest_added",
        "lockfiles_added",
        "migrations_added",
        "v02_tag_created",
        "v02_release_created",
    )
    for field_name in false_fields:
        if bool(getattr(model, field_name, False)):
            raise ValueError(f"{field_name} must be false")
    if int(getattr(model, "dependency_changes_added", 0)) != 0:
        raise ValueError("dependency_changes_added must be 0")


def _fingerprint_for_model(model: BaseModel) -> str:
    payload = model.model_dump(mode="json", exclude={"fingerprint"})
    return sha256_fingerprint(payload)


__all__ = [
    "ALLOWED_REASON_CODES",
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CANDIDATE_ID",
    "DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS",
    "DEFAULT_CLEANUP_BATCH_SIZE",
    "DEFAULT_MAXIMUM_RETENTION_SECONDS",
    "DEFAULT_MINIMUM_RETENTION_SECONDS",
    "IDENTITY_ASSERTION_REPLAY_STATE",
    "IMPLEMENTATION_TASK",
    "ISSUER_FINGERPRINT_SCHEMA_VERSION",
    "MANDATORY_RUNTIME_BOUNDARY_REASON_CODES",
    "OfflineIdentityAssertionVerificationPipelineBundle",
    "OfflineIdentityAssertionVerificationPipelineOutcome",
    "OfflineIdentityAssertionVerificationPipelineResult",
    "PARENT_AUTHORIZATION_TRANSACTION_ID",
    "REPLAY_EVIDENCE_SCHEMA_VERSION",
    "REPLAY_KEY_DOMAIN_SEPARATOR",
    "REPLAY_KEY_SCHEMA_VERSION",
    "REPLAY_PIPELINE_SCHEMA_VERSION",
    "REPLAY_POLICY_SCHEMA_VERSION",
    "REPLAY_REASON_CODE_REGISTRY_VERSION",
    "REPLAY_RECORD_SCHEMA_VERSION",
    "REPLAY_RESULT_SCHEMA_VERSION",
    "TABLE_NAME",
    "WORKSTREAM",
    "IdentityAssertionReplayAuditEvent",
    "IdentityAssertionReplayAuditEventType",
    "IdentityAssertionReplayDiagnosticSnapshot",
    "IdentityAssertionReplayPolicy",
    "IdentityAssertionReplayProtectionBundle",
    "IdentityAssertionReplayProtectionOutcome",
    "IdentityAssertionReplayProtectionResult",
    "IdentityAssertionReplayProvenanceRecord",
    "IdentityAssertionReplayReasonCode",
    "IdentityAssertionReplayRecord",
    "IdentityAssertionReplayRepositoryOutcome",
    "IdentityAssertionReplayRepositoryResult",
    "repository_reason_codes",
    "protection_reason_codes",
    "validate_replay_reason_codes",
]
