"""AION-246 provider-neutral external-cognition gateway contracts."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from math import ceil, isfinite
from typing import Any, ClassVar, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EXTERNAL_COGNITION_CONTRACT_SCHEMA_VERSION = "aion-external-cognition/v1"
EXTERNAL_COGNITION_AUTHORIZATION_SCHEMA_VERSION = "aion-external-cognition-authorization/v1"
EXTERNAL_COGNITION_COMPONENT_BINDING_SCHEMA_VERSION = (
    "aion-external-cognition-component-binding/v1"
)
EXTERNAL_COGNITION_PROVIDER_MANIFEST_SCHEMA_VERSION = (
    "aion-external-cognition-provider-manifest/v1"
)
EXTERNAL_COGNITION_MODEL_MANIFEST_SCHEMA_VERSION = "aion-external-cognition-model-manifest/v1"
EXTERNAL_COGNITION_MODEL_CAPABILITY_SCHEMA_VERSION = (
    "aion-external-cognition-model-capability/v1"
)
EXTERNAL_COGNITION_REQUEST_SCHEMA_VERSION = "aion-external-cognition-request/v1"
EXTERNAL_COGNITION_RESPONSE_SCHEMA_VERSION = "aion-external-cognition-response/v1"
EXTERNAL_COGNITION_MESSAGE_SCHEMA_VERSION = "aion-external-cognition-message-projection/v1"
EXTERNAL_COGNITION_STRUCTURED_OUTPUT_SCHEMA_VERSION = (
    "aion-external-cognition-structured-output/v1"
)
EXTERNAL_COGNITION_ROUTING_SCHEMA_VERSION = "aion-external-cognition-routing/v1"
EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION = "aion-external-cognition-budget/v1"
EXTERNAL_COGNITION_TRUST_SCHEMA_VERSION = "aion-external-cognition-trust/v1"
EXTERNAL_COGNITION_UNCERTAINTY_SCHEMA_VERSION = "aion-external-cognition-uncertainty/v1"
EXTERNAL_COGNITION_ERROR_SCHEMA_VERSION = "aion-external-cognition-provider-error/v1"
EXTERNAL_COGNITION_CIRCUIT_BREAKER_SCHEMA_VERSION = (
    "aion-external-cognition-circuit-breaker/v1"
)
EXTERNAL_COGNITION_FIXTURE_SCHEMA_VERSION = "aion-external-cognition-fixture/v1"
EXTERNAL_COGNITION_REPLAY_SCHEMA_VERSION = "aion-external-cognition-replay/v1"
EXTERNAL_COGNITION_OBSERVABILITY_SCHEMA_VERSION = "aion-external-cognition-observability/v1"
EXTERNAL_COGNITION_AUDIT_SCHEMA_VERSION = "aion-external-cognition-audit/v1"
EXTERNAL_COGNITION_INTEGRITY_SCHEMA_VERSION = "aion-external-cognition-integrity/v1"
EXTERNAL_COGNITION_EVIDENCE_SCHEMA_VERSION = "aion-external-cognition-evidence/v1"

PROGRAM_ID = "AION-ADAPTIVE-INTELLIGENCE-001"
AUTHORIZATION_TRANSACTION_ID = "AION-245-AI-0001"
APPROVAL_RECORD_ID = "AION-245-AI-0001"
IMPLEMENTATION_TASK = "AION-246"
FORMAL_CLOSEOUT_TASK = "AION-247"
FINAL_PLANNED_TASK = "AION-260"
FIXTURE_CONFIRMATION_TEXT = "RUN_DETERMINISTIC_EXTERNAL_COGNITION_FIXTURE_PILOT"
ZERO_FINGERPRINT = "0" * 64

MAXIMUM_PROVIDER_MANIFESTS = 8
MAXIMUM_MODEL_MANIFESTS = 32
MAXIMUM_MODEL_CAPABILITY_RECORDS = 256
MAXIMUM_ROUTING_POLICIES = 100
MAXIMUM_ROUTING_RULES = 500
MAXIMUM_REQUEST_TEMPLATES = 100
MAXIMUM_STRUCTURED_OUTPUT_SCHEMAS = 100
MAXIMUM_FIXTURE_SESSIONS = 20
MAXIMUM_FIXTURE_REQUESTS_PER_SESSION = 100
MAXIMUM_TOTAL_FIXTURE_REQUESTS = 1000
MAXIMUM_MESSAGES_PER_REQUEST = 256
MAXIMUM_REQUEST_PAYLOAD_BYTES = 2_097_152
MAXIMUM_RESPONSE_PAYLOAD_BYTES = 4_194_304
MAXIMUM_DECLARED_CONTEXT_TOKENS = 2_000_000
MAXIMUM_DECLARED_OUTPUT_TOKENS = 262_144
MAXIMUM_CONCURRENCY = 4
MAXIMUM_RETRY_ATTEMPTS = 3
MAXIMUM_CIRCUIT_BREAKER_RECORDS = 100
MAXIMUM_OPERATOR_REVIEW_ITEMS = 200
MAXIMUM_EVIDENCE_RECORDS = 10_000
MAXIMUM_EVIDENCE_BYTES = 104_857_600
MAXIMUM_LOCAL_FIXTURE_PILOTS = 20

SAFE_IDENTIFIER_RE = r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}"
LOWER_SHA256_RE = r"[0-9a-f]{64}"
TOKEN_ESTIMATOR_VERSION = "aion-byte-estimator/v1"

PROTECTED_KEY_PARTS = (
    "authorization",
    "bearer",
    "chain_of_thought",
    "connection_string",
    "cookie",
    "credential",
    "hidden_reasoning",
    "key",
    "password",
    "private",
    "prompt",
    "raw_body",
    "raw_context",
    "raw_output",
    "raw_prompt",
    "raw_response",
    "secret",
    "source_code",
    "source_patch",
    "token",
)
PROTECTED_VALUE_MARKERS = (
    "api key",
    "authorization header",
    "bearer ",
    "chain-of-thought",
    "connection string",
    "credential",
    "hidden reasoning",
    "password",
    "private key",
    "raw prompt",
    "raw response",
    "secret",
    "token",
)


class ExternalCognitionMode(StrEnum):
    """Authorized execution mode labels."""

    deterministic_fixture = "deterministic_fixture"
    operator_invoked_local = "operator_invoked_local"


class ExternalCognitionProviderKind(StrEnum):
    """Provider manifest kind labels."""

    deterministic_fixture = "deterministic_fixture"
    future_external_provider = "future_external_provider"


class ExternalCognitionMessageRole(StrEnum):
    """Normalized message roles."""

    system = "system"
    user = "user"
    assistant = "assistant"


class ExternalCognitionRequestIntent(StrEnum):
    """AION-246 request intent labels."""

    reasoning = "reasoning"
    code = "code"
    extraction = "extraction"
    classification = "classification"
    summarization = "summarization"
    verification = "verification"
    multilingual = "multilingual"
    long_context = "long_context"


class ExternalCognitionOutputMode(StrEnum):
    """Allowed response mode labels."""

    text = "text"
    structured_json = "structured_json"


class ExternalCognitionCapabilityKind(StrEnum):
    """Provider-neutral capability labels."""

    general_reasoning = "general_reasoning"
    code_reasoning = "code_reasoning"
    structured_extraction = "structured_extraction"
    classification = "classification"
    summarization = "summarization"
    fact_verification = "fact_verification"
    multilingual_reasoning = "multilingual_reasoning"
    long_context = "long_context"
    restricted_structured_output = "restricted_structured_output"


class ExternalCognitionRouteOutcome(StrEnum):
    """Route-plan outcomes."""

    selected = "selected"
    rejected = "rejected"
    fallback_selected = "fallback_selected"
    operator_review_required = "operator_review_required"


class ExternalCognitionBudgetOutcome(StrEnum):
    """Budget decision outcomes."""

    passed = "passed"
    rejected = "rejected"


class ExternalCognitionTrustClass(StrEnum):
    """Trust classifications for all retained responses."""

    untrusted_fixture_output = "untrusted_fixture_output"
    schema_validated_untrusted = "schema_validated_untrusted"
    operator_review_required = "operator_review_required"
    rejected = "rejected"


class ExternalCognitionProviderErrorClass(StrEnum):
    """Normalized provider error classes."""

    timeout = "timeout"
    rate_limited = "rate_limited"
    unavailable = "unavailable"
    invalid_request = "invalid_request"
    malformed_response = "malformed_response"
    safety_rejected = "safety_rejected"
    internal_error = "internal_error"


class ExternalCognitionCircuitState(StrEnum):
    """Circuit-breaker state labels."""

    closed = "closed"
    open = "open"
    half_open = "half_open"


class ExternalCognitionReplayOutcome(StrEnum):
    """Replay decision labels."""

    new = "new"
    exact_replay = "exact_replay"
    changed_replay_rejected = "changed_replay_rejected"


class ExternalCognitionIntegrityStatus(StrEnum):
    """Integrity report status labels."""

    passed = "passed"
    failed = "failed"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def external_cognition_fingerprint(payload: Any) -> str:
    """Return the deterministic SHA-256 fingerprint for a canonical JSON payload."""

    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256(encoded).hexdigest()


def content_fingerprint(kind: str, value: str | bytes | None) -> str:
    """Fingerprint transient content without retaining it."""

    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
        byte_count = len(value)
    else:
        text = value or ""
        byte_count = len(text.encode("utf-8"))
    return external_cognition_fingerprint(
        {"byte_count": byte_count, "kind": kind, "value": text}
    )


def estimate_tokens_from_bytes(byte_count: int) -> int:
    """Estimate tokens deterministically from UTF-8 byte count."""

    if byte_count < 0:
        raise ValueError("byte count must be non-negative")
    return int(ceil(byte_count / 3))


def ensure_identifier(value: str, *, field_name: str = "identifier") -> str:
    """Validate a bounded ASCII identifier."""

    if re.fullmatch(SAFE_IDENTIFIER_RE, value) is None:
        raise ValueError(f"{field_name} must be a safe bounded ASCII identifier")
    return value


def ensure_sha256(value: str, *, field_name: str = "fingerprint") -> str:
    """Validate a lowercase SHA-256 fingerprint."""

    if re.fullmatch(LOWER_SHA256_RE, value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 value")
    return value


def ensure_utc(value: datetime) -> datetime:
    """Normalize and require a timezone-aware UTC timestamp."""

    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def ensure_sorted_unique(
    values: object,
    *,
    field_name: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    """Return sorted unique strings and reject empty, duplicate, or wildcard entries."""

    if values is None:
        iterable: Iterable[object] = ()
    elif isinstance(values, str):
        raise ValueError(f"{field_name} must be a collection")
    elif isinstance(values, Iterable):
        iterable = values
    else:
        raise ValueError(f"{field_name} must be a collection")
    result = tuple(sorted(str(getattr(item, "value", item)) for item in iterable))
    if not allow_empty and not result:
        raise ValueError(f"{field_name} must not be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must be unique")
    for item in result:
        if not item.strip() or item != item.strip() or item == "*":
            raise ValueError(f"{field_name} contains an unsafe value")
    return result


def reject_protected_material(value: Any) -> None:
    """Reject protected material recursively without echoing rejected values."""

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                normalized = str(key).lower().replace("-", "_")
                if any(part in normalized for part in PROTECTED_KEY_PARTS):
                    raise ValueError("protected material is not allowed")
                walk(nested)
            return
        if isinstance(item, (list, tuple, set)):
            for nested in item:
                walk(nested)
            return
        if isinstance(item, str):
            lowered = item.lower()
            if any(marker in lowered for marker in PROTECTED_VALUE_MARKERS):
                raise ValueError("protected material is not allowed")

    walk(value)


def _reject_non_finite(value: Any) -> None:
    if isinstance(value, Mapping):
        for nested in value.values():
            _reject_non_finite(nested)
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            _reject_non_finite(nested)
    elif isinstance(value, float) and not isfinite(value):
        raise ValueError("non-finite numeric values are not supported")


def _json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return ensure_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _json_safe(nested) for key, nested in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(nested) for nested in value]
    if isinstance(value, set):
        return sorted(_json_safe(nested) for nested in value)
    if isinstance(value, float) and not isfinite(value):
        raise TypeError("non-finite numeric values are not supported")
    return value


class ExternalCognitionBaseModel(BaseModel):
    """Strict Pydantic v2 base for AION-246 records."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def common_values_must_be_safe(self) -> Self:
        _reject_non_finite(self.model_dump(mode="python"))
        return self


class ExternalCognitionFingerprintedModel(ExternalCognitionBaseModel):
    """Model that self-populates and verifies one canonical fingerprint field."""

    _fingerprint_field: ClassVar[str | None] = None

    @model_validator(mode="after")
    def fingerprint_must_match(self) -> Self:
        field_name = self._fingerprint_field
        if field_name is None:
            return self
        expected = external_cognition_fingerprint(
            self.model_dump(mode="json", exclude={field_name})
        )
        current = getattr(self, field_name)
        if current is None:
            object.__setattr__(self, field_name, expected)
        elif current != expected:
            raise ValueError("fingerprint must match canonical external-cognition payload")
        return self


class ExternalCognitionAuthorizationEnvelope(ExternalCognitionFingerprintedModel):
    """AION-245-AI-0001 authorization envelope for one fixture-only session."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "authorization_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_AUTHORIZATION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    implementation_task: str = IMPLEMENTATION_TASK
    formal_closeout_task: str = FORMAL_CLOSEOUT_TASK
    session_id: str
    operator_identity_fingerprint: str
    operator_invoked: bool = True
    deterministic_fixture_only: bool = True
    provider_neutral: bool = True
    existing_model_gateway_composed: bool = True
    network_enabled: bool = False
    credential_input_enabled: bool = False
    raw_prompt_persistence: bool = False
    raw_response_persistence: bool = False
    memory_write: bool = False
    tool_execution: bool = False
    background_execution: bool = False
    created_at: datetime
    expires_at: datetime
    authorization_fingerprint: str | None = None

    @field_validator("session_id")
    @classmethod
    def session_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value, field_name="session_id")

    @field_validator("operator_identity_fingerprint")
    @classmethod
    def operator_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def authorization_must_match_aion245(self) -> Self:
        if (
            self.program_id != PROGRAM_ID
            or self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or self.approval_record_id != APPROVAL_RECORD_ID
            or self.implementation_task != IMPLEMENTATION_TASK
            or self.formal_closeout_task != FORMAL_CLOSEOUT_TASK
            or self.expires_at <= self.created_at
            or not self.operator_invoked
            or not self.deterministic_fixture_only
            or not self.provider_neutral
            or not self.existing_model_gateway_composed
            or self.network_enabled
            or self.credential_input_enabled
            or self.raw_prompt_persistence
            or self.raw_response_persistence
            or self.memory_write
            or self.tool_execution
            or self.background_execution
        ):
            raise ValueError("AION-245-AI-0001 external-cognition authorization mismatch")
        return self


class ExternalCognitionComponentBinding(ExternalCognitionFingerprintedModel):
    """Read-only binding to secure runtime and existing model-gateway lineage."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_COMPONENT_BINDING_SCHEMA_VERSION
    binding_id: str
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    current_main_commit: str
    secure_runtime_contract_fingerprint: str
    secure_runtime_session_fingerprint: str
    existing_model_gateway_contract_fingerprint: str
    existing_model_gateway_service_fingerprint: str
    existing_provider_manifest_projection_fingerprint: str
    existing_model_manifest_projection_fingerprint: str
    existing_route_policy_projection_fingerprint: str
    resource_limit_fingerprint: str
    created_at: datetime
    binding_fingerprint: str | None = None
    read_only: bool = True
    deterministic_fixture_only: bool = True
    network_effect: bool = False
    provider_effect: bool = False
    memory_effect: bool = False
    tool_effect: bool = False

    @field_validator("binding_id")
    @classmethod
    def binding_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator(
        "secure_runtime_contract_fingerprint",
        "secure_runtime_session_fingerprint",
        "existing_model_gateway_contract_fingerprint",
        "existing_model_gateway_service_fingerprint",
        "existing_provider_manifest_projection_fingerprint",
        "existing_model_manifest_projection_fingerprint",
        "existing_route_policy_projection_fingerprint",
        "resource_limit_fingerprint",
    )
    @classmethod
    def component_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def component_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def component_binding_must_be_no_effect(self) -> Self:
        if (
            self.program_id != PROGRAM_ID
            or self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or not self.current_main_commit
            or not self.read_only
            or not self.deterministic_fixture_only
            or self.network_effect
            or self.provider_effect
            or self.memory_effect
            or self.tool_effect
        ):
            raise ValueError("external-cognition component binding violates no-effect boundary")
        return self


class ExternalCognitionSessionPlan(ExternalCognitionFingerprintedModel):
    """Bounded session plan for one operator-invoked fixture session."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_COMPONENT_BINDING_SCHEMA_VERSION
    session_plan_id: str
    authorization_envelope: ExternalCognitionAuthorizationEnvelope
    component_binding: ExternalCognitionComponentBinding
    maximum_requests: int = Field(default=MAXIMUM_FIXTURE_REQUESTS_PER_SESSION, ge=1)
    maximum_concurrent_requests: int = Field(default=MAXIMUM_CONCURRENCY, ge=1)
    created_at: datetime
    expires_at: datetime
    operator_invoked: bool = True
    deterministic_fixture_only: bool = True
    background_execution: bool = False
    scheduled_execution: bool = False
    production_runtime: bool = False
    plan_fingerprint: str | None = None

    @field_validator("session_plan_id")
    @classmethod
    def plan_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def session_plan_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def session_plan_must_match_authorization(self) -> Self:
        if (
            self.expires_at <= self.created_at
            or self.expires_at > self.authorization_envelope.expires_at
            or self.maximum_requests > MAXIMUM_FIXTURE_REQUESTS_PER_SESSION
            or self.maximum_concurrent_requests > MAXIMUM_CONCURRENCY
            or not self.operator_invoked
            or not self.deterministic_fixture_only
            or self.background_execution
            or self.scheduled_execution
            or self.production_runtime
        ):
            raise ValueError("external-cognition session plan exceeds authorization")
        return self


class ExternalCognitionSession(ExternalCognitionFingerprintedModel):
    """Immutable session snapshot."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "session_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_COMPONENT_BINDING_SCHEMA_VERSION
    session_id: str
    session_plan: ExternalCognitionSessionPlan
    active_request_ids: tuple[str, ...] = Field(default_factory=tuple)
    completed_request_ids: tuple[str, ...] = Field(default_factory=tuple)
    audit_chain_head: str = ZERO_FINGERPRINT
    evidence_chain_head: str = ZERO_FINGERPRINT
    created_at: datetime
    expires_at: datetime
    closed_at: datetime | None = None
    provider_effect: bool = False
    network_effect: bool = False
    memory_effect: bool = False
    tool_effect: bool = False
    session_fingerprint: str | None = None

    @field_validator("session_id")
    @classmethod
    def session_identifier_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("active_request_ids", "completed_request_ids", mode="before")
    @classmethod
    def request_ids_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value or (), field_name="request ids", allow_empty=True)

    @field_validator("audit_chain_head", "evidence_chain_head")
    @classmethod
    def chain_heads_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at", "closed_at")
    @classmethod
    def session_timestamps_must_be_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_utc(value)

    @model_validator(mode="after")
    def session_must_remain_no_effect(self) -> Self:
        if (
            len(self.active_request_ids) > self.session_plan.maximum_concurrent_requests
            or self.provider_effect
            or self.network_effect
            or self.memory_effect
            or self.tool_effect
        ):
            raise ValueError("external-cognition session violates no-effect boundary")
        return self


class InMemoryExternalCognitionSessionRepository:
    """In-memory session repository with maximum one active session."""

    def __init__(self) -> None:
        self._sessions: dict[str, ExternalCognitionSession] = {}

    def start_session(self, plan: ExternalCognitionSessionPlan) -> ExternalCognitionSession:
        if self.active_session_count() >= 1:
            raise ValueError("only one active external-cognition fixture session is allowed")
        session = ExternalCognitionSession(
            session_id=plan.authorization_envelope.session_id,
            session_plan=plan,
            created_at=plan.created_at,
            expires_at=plan.expires_at,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> ExternalCognitionSession:
        return self._sessions[session_id]

    def close_session(self, session_id: str, closed_at: datetime) -> ExternalCognitionSession:
        session = self._sessions[session_id]
        closed = ExternalCognitionSession(
            **{
                **session.model_dump(),
                "closed_at": ensure_utc(closed_at),
                "active_request_ids": (),
                "session_fingerprint": None,
            }
        )
        self._sessions[session_id] = closed
        return closed

    def active_session_count(self) -> int:
        return sum(1 for session in self._sessions.values() if session.closed_at is None)

    def list_sessions(self) -> tuple[ExternalCognitionSession, ...]:
        return tuple(self._sessions[key] for key in sorted(self._sessions))


class ExternalCognitionProviderManifest(ExternalCognitionFingerprintedModel):
    """Immutable provider manifest."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "manifest_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_PROVIDER_MANIFEST_SCHEMA_VERSION
    provider_id: str
    provider_kind: ExternalCognitionProviderKind
    provider_display_code: str
    fixture_only: bool = True
    network_required: bool = False
    credential_required: bool = False
    endpoint_present: bool = False
    supported_output_modes: tuple[ExternalCognitionOutputMode, ...]
    supported_capability_codes: tuple[ExternalCognitionCapabilityKind, ...]
    declared_availability_class: str
    declared_cost_class_code: str
    declared_latency_class_code: str
    created_at: datetime
    manifest_fingerprint: str | None = None

    @field_validator(
        "provider_id",
        "provider_display_code",
        "declared_availability_class",
        "declared_cost_class_code",
        "declared_latency_class_code",
    )
    @classmethod
    def provider_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("supported_output_modes", mode="before")
    @classmethod
    def provider_output_modes_must_be_sorted(
        cls, value: object
    ) -> tuple[ExternalCognitionOutputMode, ...]:
        return tuple(ExternalCognitionOutputMode(item) for item in ensure_sorted_unique(
            value, field_name="supported output modes"
        ))

    @field_validator("supported_capability_codes", mode="before")
    @classmethod
    def provider_capabilities_must_be_sorted(
        cls, value: object
    ) -> tuple[ExternalCognitionCapabilityKind, ...]:
        return tuple(ExternalCognitionCapabilityKind(item) for item in ensure_sorted_unique(
            value, field_name="supported capability codes"
        ))

    @field_validator("created_at")
    @classmethod
    def provider_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def provider_must_be_fixture_only(self) -> Self:
        if (
            self.provider_kind != ExternalCognitionProviderKind.deterministic_fixture
            or not self.fixture_only
            or self.network_required
            or self.credential_required
            or self.endpoint_present
        ):
            raise ValueError("AION-246 providers must be deterministic fixtures only")
        return self


class ExternalCognitionModelCapabilityRecord(ExternalCognitionFingerprintedModel):
    """Immutable capability record for one model/provider capability."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "capability_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_MODEL_CAPABILITY_SCHEMA_VERSION
    capability_record_id: str
    provider_id: str
    model_id: str
    capability_kind: ExternalCognitionCapabilityKind
    output_modes: tuple[ExternalCognitionOutputMode, ...]
    declared_context_tokens: int = Field(gt=0, le=MAXIMUM_DECLARED_CONTEXT_TOKENS)
    declared_output_tokens: int = Field(gt=0, le=MAXIMUM_DECLARED_OUTPUT_TOKENS)
    structured_output_supported: bool = False
    tool_calling_supported: bool = False
    fixture_only: bool = True
    capability_fingerprint: str | None = None

    @field_validator("capability_record_id", "provider_id", "model_id")
    @classmethod
    def capability_ids_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("output_modes", mode="before")
    @classmethod
    def capability_output_modes_must_be_sorted(
        cls, value: object
    ) -> tuple[ExternalCognitionOutputMode, ...]:
        return tuple(ExternalCognitionOutputMode(item) for item in ensure_sorted_unique(
            value, field_name="capability output modes"
        ))

    @model_validator(mode="after")
    def capability_must_not_enable_tools(self) -> Self:
        if self.tool_calling_supported or not self.fixture_only:
            raise ValueError("capability records cannot enable tools or live providers")
        if (
            self.capability_kind == ExternalCognitionCapabilityKind.restricted_structured_output
            and not self.structured_output_supported
        ):
            raise ValueError("restricted structured output capability must declare schema support")
        return self


class ExternalCognitionModelManifest(ExternalCognitionFingerprintedModel):
    """Immutable model manifest."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "manifest_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_MODEL_MANIFEST_SCHEMA_VERSION
    model_id: str
    provider_id: str
    model_family_code: str
    model_version_code: str
    capability_record_ids: tuple[str, ...]
    declared_context_token_limit: int = Field(gt=0, le=MAXIMUM_DECLARED_CONTEXT_TOKENS)
    declared_output_token_limit: int = Field(gt=0, le=MAXIMUM_DECLARED_OUTPUT_TOKENS)
    declared_cost_units: int = Field(gt=0)
    declared_latency_units: int = Field(gt=0)
    structured_output_supported: bool
    tool_calling_supported: bool = False
    network_enabled: bool = False
    fixture_only: bool = True
    manifest_fingerprint: str | None = None

    @field_validator("model_id", "provider_id", "model_family_code", "model_version_code")
    @classmethod
    def model_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("capability_record_ids", mode="before")
    @classmethod
    def model_capability_ids_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value, field_name="capability record ids")

    @model_validator(mode="after")
    def model_manifest_must_be_fixture_only(self) -> Self:
        if self.tool_calling_supported or self.network_enabled or not self.fixture_only:
            raise ValueError("model manifests cannot enable tools, network, or live providers")
        return self


class InMemoryExternalCognitionProviderRegistry:
    """Immutable in-memory provider manifest registry."""

    def __init__(self, manifests: Sequence[ExternalCognitionProviderManifest]) -> None:
        if len(manifests) > MAXIMUM_PROVIDER_MANIFESTS:
            raise ValueError("provider manifest limit exceeded")
        by_id: dict[str, ExternalCognitionProviderManifest] = {}
        for manifest in manifests:
            if manifest.provider_id in by_id:
                raise ValueError("duplicate provider ID")
            by_id[manifest.provider_id] = manifest
        self._manifests = by_id

    def get(self, provider_id: str) -> ExternalCognitionProviderManifest:
        return self._manifests[provider_id]

    def list_manifests(self) -> tuple[ExternalCognitionProviderManifest, ...]:
        return tuple(self._manifests[key] for key in sorted(self._manifests))


class InMemoryExternalCognitionModelRegistry:
    """Immutable in-memory model and capability registry."""

    def __init__(
        self,
        *,
        provider_registry: InMemoryExternalCognitionProviderRegistry,
        models: Sequence[ExternalCognitionModelManifest],
        capabilities: Sequence[ExternalCognitionModelCapabilityRecord],
    ) -> None:
        if len(models) > MAXIMUM_MODEL_MANIFESTS:
            raise ValueError("model manifest limit exceeded")
        if len(capabilities) > MAXIMUM_MODEL_CAPABILITY_RECORDS:
            raise ValueError("model capability limit exceeded")
        capability_by_id: dict[str, ExternalCognitionModelCapabilityRecord] = {}
        for capability in capabilities:
            if capability.capability_record_id in capability_by_id:
                raise ValueError("duplicate capability record ID")
            provider_registry.get(capability.provider_id)
            capability_by_id[capability.capability_record_id] = capability
        model_by_id: dict[str, ExternalCognitionModelManifest] = {}
        for model in models:
            if model.model_id in model_by_id:
                raise ValueError("duplicate model ID")
            provider_registry.get(model.provider_id)
            for capability_id in model.capability_record_ids:
                capability_record = capability_by_id.get(capability_id)
                if capability_record is None:
                    raise ValueError("unknown capability reference")
                if (
                    capability_record.model_id != model.model_id
                    or capability_record.provider_id != model.provider_id
                ):
                    raise ValueError("capability reference mismatch")
            model_by_id[model.model_id] = model
        self._models = model_by_id
        self._capabilities = capability_by_id

    def get_model(self, model_id: str) -> ExternalCognitionModelManifest:
        return self._models[model_id]

    def get_capability(
        self, capability_record_id: str
    ) -> ExternalCognitionModelCapabilityRecord:
        return self._capabilities[capability_record_id]

    def list_models(self) -> tuple[ExternalCognitionModelManifest, ...]:
        return tuple(self._models[key] for key in sorted(self._models))

    def list_capabilities(self) -> tuple[ExternalCognitionModelCapabilityRecord, ...]:
        return tuple(self._capabilities[key] for key in sorted(self._capabilities))

    def capabilities_for_model(
        self, model_id: str
    ) -> tuple[ExternalCognitionModelCapabilityRecord, ...]:
        model = self.get_model(model_id)
        return tuple(self._capabilities[key] for key in model.capability_record_ids)


class ExternalCognitionMessageProjection(ExternalCognitionFingerprintedModel):
    """Retained message projection without message body."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "message_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_MESSAGE_SCHEMA_VERSION
    message_id: str
    role: ExternalCognitionMessageRole
    utf8_byte_count: int = Field(ge=0)
    deterministic_token_estimate: int = Field(ge=0)
    content_fingerprint: str
    redaction_finding_count: int = Field(ge=0)
    protected_material_present: bool
    normalized_at: datetime
    message_fingerprint: str | None = None

    @field_validator("message_id")
    @classmethod
    def message_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("content_fingerprint")
    @classmethod
    def content_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("normalized_at")
    @classmethod
    def normalized_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class ExternalCognitionRequestTemplate(ExternalCognitionFingerprintedModel):
    """Fingerprint-only request template."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "template_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_REQUEST_SCHEMA_VERSION
    template_id: str
    request_intent: ExternalCognitionRequestIntent
    requested_capabilities: tuple[ExternalCognitionCapabilityKind, ...]
    template_body_fingerprint: str
    raw_template_retained: bool = False
    template_fingerprint: str | None = None

    @field_validator("template_id")
    @classmethod
    def template_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("template_body_fingerprint")
    @classmethod
    def template_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("requested_capabilities", mode="before")
    @classmethod
    def template_capabilities_must_be_sorted(
        cls, value: object
    ) -> tuple[ExternalCognitionCapabilityKind, ...]:
        return tuple(ExternalCognitionCapabilityKind(item) for item in ensure_sorted_unique(
            value, field_name="template capabilities"
        ))

    @model_validator(mode="after")
    def template_must_not_retain_raw_body(self) -> Self:
        if self.raw_template_retained:
            raise ValueError("request templates cannot retain raw prompt bodies")
        return self


class ExternalCognitionRequestEnvelope(ExternalCognitionFingerprintedModel):
    """Provider-neutral request envelope with no raw prompt body."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "request_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_REQUEST_SCHEMA_VERSION
    request_id: str
    session_id: str
    authorization_fingerprint: str
    component_binding_fingerprint: str
    request_intent: ExternalCognitionRequestIntent
    requested_capability_codes: tuple[ExternalCognitionCapabilityKind, ...]
    message_projection_fingerprints: tuple[str, ...]
    structured_output_schema_fingerprint: str | None = None
    context_budget_fingerprint: str
    output_budget_fingerprint: str
    cost_budget_fingerprint: str
    latency_budget_fingerprint: str
    routing_policy_fingerprint: str
    safe_metadata: Mapping[str, str] = Field(default_factory=dict)
    idempotency_fingerprint: str
    created_at: datetime
    expires_at: datetime
    raw_prompt_retained: bool = False
    tool_role_present: bool = False
    function_call_present: bool = False
    provider_endpoint_present: bool = False
    provider_headers_present: bool = False
    credential_present: bool = False
    memory_write_requested: bool = False
    tool_execution_requested: bool = False
    background_execution_requested: bool = False
    request_fingerprint: str | None = None

    @field_validator("request_id", "session_id")
    @classmethod
    def request_ids_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator(
        "authorization_fingerprint",
        "component_binding_fingerprint",
        "context_budget_fingerprint",
        "output_budget_fingerprint",
        "cost_budget_fingerprint",
        "latency_budget_fingerprint",
        "routing_policy_fingerprint",
        "idempotency_fingerprint",
    )
    @classmethod
    def request_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("structured_output_schema_fingerprint")
    @classmethod
    def optional_schema_fingerprint_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_sha256(value)

    @field_validator("requested_capability_codes", mode="before")
    @classmethod
    def request_capabilities_must_be_sorted(
        cls, value: object
    ) -> tuple[ExternalCognitionCapabilityKind, ...]:
        return tuple(ExternalCognitionCapabilityKind(item) for item in ensure_sorted_unique(
            value, field_name="requested capabilities"
        ))

    @field_validator("message_projection_fingerprints", mode="before")
    @classmethod
    def message_fingerprints_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return tuple(
            ensure_sha256(item)
            for item in ensure_sorted_unique(value, field_name="message fingerprints")
        )

    @field_validator("safe_metadata")
    @classmethod
    def safe_metadata_must_be_clean(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        reject_protected_material(value)
        return dict(sorted(value.items()))

    @field_validator("created_at", "expires_at")
    @classmethod
    def request_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def request_must_be_bounded_and_no_effect(self) -> Self:
        if (
            self.expires_at <= self.created_at
            or len(self.message_projection_fingerprints) > MAXIMUM_MESSAGES_PER_REQUEST
            or self.raw_prompt_retained
            or self.tool_role_present
            or self.function_call_present
            or self.provider_endpoint_present
            or self.provider_headers_present
            or self.credential_present
            or self.memory_write_requested
            or self.tool_execution_requested
            or self.background_execution_requested
        ):
            raise ValueError("external-cognition request violates no-effect boundary")
        return self


class InMemoryExternalCognitionRequestRepository:
    """In-memory request repository with exact-replay detection."""

    def __init__(self) -> None:
        self._request_records: dict[str, ExternalCognitionRequestEnvelope] = {}
        self._safe_results: dict[str, str] = {}

    def check_request_idempotency(
        self, request: ExternalCognitionRequestEnvelope
    ) -> tuple[ExternalCognitionReplayOutcome, str | None]:
        existing = self._request_records.get(request.request_id)
        if existing is None:
            return ExternalCognitionReplayOutcome.new, None
        if existing.request_fingerprint == request.request_fingerprint:
            return ExternalCognitionReplayOutcome.exact_replay, self._safe_results.get(
                request.request_id
            )
        return ExternalCognitionReplayOutcome.changed_replay_rejected, None

    def store_request(
        self, request: ExternalCognitionRequestEnvelope, safe_result_fingerprint: str
    ) -> None:
        self._request_records[request.request_id] = request
        self._safe_results[request.request_id] = safe_result_fingerprint


STRUCTURED_ALLOWED_KEYS = {
    "type",
    "properties",
    "required",
    "items",
    "enum",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "additionalProperties",
}
STRUCTURED_ALLOWED_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
STRUCTURED_PROHIBITED_KEYS = {"$ref", "oneOf", "anyOf", "allOf", "patternProperties", "format"}


class ExternalCognitionStructuredOutputSchema(ExternalCognitionFingerprintedModel):
    """Restricted JSON-schema subset."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "schema_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_STRUCTURED_OUTPUT_SCHEMA_VERSION
    schema_id: str
    schema_definition: Mapping[str, Any]
    schema_depth: int = Field(ge=1, le=12)
    property_count: int = Field(ge=0, le=128)
    additional_properties_allowed: bool = False
    schema_fingerprint: str | None = None

    @field_validator("schema_id")
    @classmethod
    def schema_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @model_validator(mode="after")
    def schema_must_be_restricted(self) -> Self:
        validate_structured_schema_definition(self.schema_definition)
        if self.additional_properties_allowed:
            raise ValueError("structured output schemas must set additionalProperties=false")
        return self


class ExternalCognitionStructuredOutputValidationResult(ExternalCognitionFingerprintedModel):
    """Structured-output validation result that never grants factual trust."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "validation_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_STRUCTURED_OUTPUT_SCHEMA_VERSION
    validation_id: str
    schema_fingerprint: str
    output_fingerprint: str
    accepted: bool
    reason_codes: tuple[str, ...]
    trust_class: ExternalCognitionTrustClass
    factual_truth_confirmed: bool = False
    execution_authorized: bool = False
    created_at: datetime
    validation_fingerprint: str | None = None

    @field_validator("validation_id")
    @classmethod
    def validation_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("schema_fingerprint", "output_fingerprint")
    @classmethod
    def validation_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def validation_reasons_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value or ("none",), field_name="validation reasons")

    @field_validator("created_at")
    @classmethod
    def validation_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def validation_cannot_create_authority(self) -> Self:
        if self.factual_truth_confirmed or self.execution_authorized:
            raise ValueError("schema validation cannot create factual or execution authority")
        validated_untrusted = ExternalCognitionTrustClass.schema_validated_untrusted
        if self.accepted and self.trust_class != validated_untrusted:
            raise ValueError("accepted structured output remains schema_validated_untrusted")
        if not self.accepted and self.trust_class == validated_untrusted:
            raise ValueError("rejected structured output cannot be schema validated")
        return self


def validate_structured_schema_definition(schema: Mapping[str, Any]) -> None:
    """Validate the AION-246 restricted structured-output schema subset."""

    seen: set[int] = set()

    def walk(node: Any, depth: int) -> None:
        if depth > 12:
            raise ValueError("structured schema depth exceeded")
        if isinstance(node, Mapping):
            marker = id(node)
            if marker in seen:
                raise ValueError("recursive structured schema is not allowed")
            seen.add(marker)
            unknown = set(node) - STRUCTURED_ALLOWED_KEYS
            prohibited = set(node) & STRUCTURED_PROHIBITED_KEYS
            if unknown or prohibited:
                raise ValueError("structured schema contains unsupported keywords")
            raw_type = node.get("type")
            if isinstance(raw_type, str) and raw_type not in STRUCTURED_ALLOWED_TYPES:
                raise ValueError("structured schema type is not allowed")
            if node.get("additionalProperties") is not False and raw_type == "object":
                raise ValueError("object schemas must set additionalProperties=false")
            for key, nested in node.items():
                if key == "properties":
                    if not isinstance(nested, Mapping):
                        raise ValueError("structured schema properties must be an object")
                    if len(nested) > 128:
                        raise ValueError("structured schema property count exceeded")
                    for property_name, property_schema in nested.items():
                        ensure_identifier(str(property_name), field_name="schema property")
                        if not isinstance(property_schema, Mapping):
                            raise ValueError("structured schema property must be a schema")
                        walk(property_schema, depth + 1)
                    continue
                walk(nested, depth + 1)
            seen.remove(marker)
            return
        if isinstance(node, (list, tuple)):
            for item in node:
                walk(item, depth + 1)
            return
        if isinstance(node, float) and not isfinite(node):
            raise ValueError("non-finite schema number is not allowed")

    walk(schema, 1)


def validate_structured_output_value(
    schema: Mapping[str, Any],
    value: Any,
) -> tuple[bool, tuple[str, ...]]:
    """Validate a value against the supported schema subset."""

    try:
        _validate_structured_value(schema, value, "$")
    except ValueError as exc:
        return False, (ensure_identifier(str(exc).replace(" ", "_").replace("$", "root")[:80]),)
    return True, ("schema_validated",)


def _validate_structured_value(schema: Mapping[str, Any], value: Any, path: str) -> None:
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, Mapping):
            raise ValueError(f"{path}_type_mismatch")
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise ValueError(f"{path}_invalid_properties")
        required = schema.get("required", ())
        if not isinstance(required, Sequence) or isinstance(required, str):
            raise ValueError(f"{path}_invalid_required")
        if set(value) - set(properties):
            raise ValueError(f"{path}_additional_property")
        for key in required:
            if key not in value:
                raise ValueError(f"{path}_missing_required")
        for key, nested_schema in properties.items():
            if key in value and isinstance(nested_schema, Mapping):
                _validate_structured_value(nested_schema, value[key], f"{path}_{key}")
        return
    if schema_type == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path}_type_mismatch")
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if isinstance(min_items, int) and len(value) < min_items:
            raise ValueError(f"{path}_min_items")
        if isinstance(max_items, int) and len(value) > max_items:
            raise ValueError(f"{path}_max_items")
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for item in value:
                _validate_structured_value(item_schema, item, f"{path}_item")
        return
    if schema_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"{path}_type_mismatch")
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        if isinstance(min_length, int) and len(value) < min_length:
            raise ValueError(f"{path}_min_length")
        if isinstance(max_length, int) and len(value) > max_length:
            raise ValueError(f"{path}_max_length")
    elif schema_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{path}_type_mismatch")
    elif schema_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{path}_type_mismatch")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError(f"{path}_non_finite")
    elif schema_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(f"{path}_type_mismatch")
    elif schema_type == "null" and value is not None:
        raise ValueError(f"{path}_type_mismatch")
    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        raise ValueError(f"{path}_enum")
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(minimum, (int, float)) and value < minimum:
            raise ValueError(f"{path}_minimum")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise ValueError(f"{path}_maximum")


class ExternalCognitionContextBudget(ExternalCognitionFingerprintedModel):
    """Context budget for one request."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION
    maximum_messages: int = Field(default=MAXIMUM_MESSAGES_PER_REQUEST, ge=1)
    maximum_payload_bytes: int = Field(default=MAXIMUM_REQUEST_PAYLOAD_BYTES, ge=1)
    maximum_declared_context_tokens: int = Field(
        default=MAXIMUM_DECLARED_CONTEXT_TOKENS, ge=1
    )
    budget_fingerprint: str | None = None


class ExternalCognitionOutputBudget(ExternalCognitionFingerprintedModel):
    """Output-token and byte budget."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION
    maximum_output_tokens: int = Field(default=MAXIMUM_DECLARED_OUTPUT_TOKENS, ge=1)
    maximum_response_payload_bytes: int = Field(default=MAXIMUM_RESPONSE_PAYLOAD_BYTES, ge=1)
    budget_fingerprint: str | None = None


class ExternalCognitionCostBudget(ExternalCognitionFingerprintedModel):
    """Abstract declared cost budget."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION
    maximum_declared_cost_units: int = Field(default=1_000_000, ge=1)
    live_pricing_claimed: bool = False
    budget_fingerprint: str | None = None

    @model_validator(mode="after")
    def cost_budget_cannot_claim_live_pricing(self) -> Self:
        if self.live_pricing_claimed:
            raise ValueError("cost budget cannot claim live pricing")
        return self


class ExternalCognitionLatencyBudget(ExternalCognitionFingerprintedModel):
    """Declared fixture latency budget."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION
    maximum_declared_latency_units: int = Field(default=1_000_000, ge=1)
    live_latency_claimed: bool = False
    budget_fingerprint: str | None = None

    @model_validator(mode="after")
    def latency_budget_cannot_claim_live_latency(self) -> Self:
        if self.live_latency_claimed:
            raise ValueError("latency budget cannot claim live latency")
        return self


class ExternalCognitionBudgetDecision(ExternalCognitionFingerprintedModel):
    """Fail-closed budget decision."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "decision_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION
    decision_id: str
    budget_fingerprint: str
    usage_fingerprint: str
    outcome: ExternalCognitionBudgetOutcome
    reason_codes: tuple[str, ...]
    override_allowed: bool = False
    created_at: datetime
    decision_fingerprint: str | None = None

    @field_validator("decision_id")
    @classmethod
    def budget_decision_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("budget_fingerprint", "usage_fingerprint")
    @classmethod
    def budget_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def budget_reasons_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value or ("passed",), field_name="budget reasons")

    @field_validator("created_at")
    @classmethod
    def budget_decision_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def budget_decision_cannot_override(self) -> Self:
        if self.override_allowed:
            raise ValueError("budget denials cannot be overridden")
        return self


class ExternalCognitionRetryPolicy(ExternalCognitionFingerprintedModel):
    """Bounded retry policy."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "policy_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION
    policy_id: str
    maximum_attempts: int = Field(default=MAXIMUM_RETRY_ATTEMPTS, ge=0, le=MAXIMUM_RETRY_ATTEMPTS)
    retryable_error_classes: tuple[ExternalCognitionProviderErrorClass, ...] = (
        ExternalCognitionProviderErrorClass.timeout,
        ExternalCognitionProviderErrorClass.rate_limited,
        ExternalCognitionProviderErrorClass.unavailable,
        ExternalCognitionProviderErrorClass.internal_error,
    )
    automatic_live_retry_enabled: bool = False
    policy_fingerprint: str | None = None

    @field_validator("policy_id")
    @classmethod
    def retry_policy_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @model_validator(mode="after")
    def retry_policy_must_be_bounded(self) -> Self:
        if self.automatic_live_retry_enabled:
            raise ValueError("retry policy cannot authorize live retries")
        return self


class ExternalCognitionRetryPlan(ExternalCognitionFingerprintedModel):
    """Deterministic retry plan with live retry disabled."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "retry_plan_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_BUDGET_SCHEMA_VERSION
    retry_plan_id: str
    request_fingerprint: str
    policy_fingerprint: str
    planned_attempts: int = Field(ge=0, le=MAXIMUM_RETRY_ATTEMPTS)
    reason_codes: tuple[str, ...]
    automatic_live_retry_enabled: bool = False
    retry_plan_fingerprint: str | None = None

    @field_validator("retry_plan_id")
    @classmethod
    def retry_plan_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("request_fingerprint", "policy_fingerprint")
    @classmethod
    def retry_plan_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def retry_plan_reasons_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value, field_name="retry plan reasons")

    @model_validator(mode="after")
    def retry_plan_must_be_bounded(self) -> Self:
        if self.automatic_live_retry_enabled:
            raise ValueError("retry plan cannot enable live retry")
        return self


class ExternalCognitionRouteRule(ExternalCognitionFingerprintedModel):
    """Deterministic routing rule."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "rule_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_ROUTING_SCHEMA_VERSION
    rule_id: str
    allowed_provider_ids: tuple[str, ...]
    allowed_model_ids: tuple[str, ...]
    required_capabilities: tuple[ExternalCognitionCapabilityKind, ...]
    output_mode: ExternalCognitionOutputMode
    maximum_declared_cost_units: int = Field(gt=0)
    maximum_declared_latency_units: int = Field(gt=0)
    rule_fingerprint: str | None = None

    @field_validator("rule_id")
    @classmethod
    def route_rule_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("allowed_provider_ids", "allowed_model_ids", mode="before")
    @classmethod
    def route_rule_ids_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value, field_name="route rule IDs")

    @field_validator("required_capabilities", mode="before")
    @classmethod
    def route_rule_capabilities_must_be_sorted(
        cls, value: object
    ) -> tuple[ExternalCognitionCapabilityKind, ...]:
        return tuple(ExternalCognitionCapabilityKind(item) for item in ensure_sorted_unique(
            value, field_name="route rule capabilities"
        ))


class ExternalCognitionRoutePolicy(ExternalCognitionFingerprintedModel):
    """Deterministic route policy."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "policy_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_ROUTING_SCHEMA_VERSION
    policy_id: str
    rules: tuple[ExternalCognitionRouteRule, ...]
    deterministic_tie_break: Literal["model_id"] = "model_id"
    model_generated_routing: bool = False
    learned_routing: bool = False
    random_routing: bool = False
    automatic_live_invocation: bool = False
    policy_fingerprint: str | None = None

    @field_validator("policy_id")
    @classmethod
    def route_policy_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @model_validator(mode="after")
    def route_policy_must_be_deterministic(self) -> Self:
        if len(self.rules) > MAXIMUM_ROUTING_RULES:
            raise ValueError("routing rule limit exceeded")
        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("duplicate routing rule ID")
        if (
            self.model_generated_routing
            or self.learned_routing
            or self.random_routing
            or self.automatic_live_invocation
        ):
            raise ValueError("route policy cannot use dynamic or live routing")
        return self


class ExternalCognitionRouteCandidate(ExternalCognitionFingerprintedModel):
    """One deterministic route candidate."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "candidate_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_ROUTING_SCHEMA_VERSION
    provider_id: str
    model_id: str
    matched_capabilities: tuple[ExternalCognitionCapabilityKind, ...]
    output_mode: ExternalCognitionOutputMode
    declared_context_tokens: int
    declared_output_tokens: int
    declared_cost_units: int
    declared_latency_units: int
    circuit_state: ExternalCognitionCircuitState = ExternalCognitionCircuitState.closed
    rejection_reasons: tuple[str, ...] = Field(default_factory=tuple)
    candidate_fingerprint: str | None = None

    @field_validator("provider_id", "model_id")
    @classmethod
    def route_candidate_ids_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("matched_capabilities", mode="before")
    @classmethod
    def candidate_capabilities_must_be_sorted(
        cls, value: object
    ) -> tuple[ExternalCognitionCapabilityKind, ...]:
        return tuple(ExternalCognitionCapabilityKind(item) for item in ensure_sorted_unique(
            value, field_name="matched capabilities", allow_empty=True
        ))

    @field_validator("rejection_reasons", mode="before")
    @classmethod
    def rejection_reasons_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value or (), field_name="rejection reasons", allow_empty=True)


class ExternalCognitionRoutePlan(ExternalCognitionFingerprintedModel):
    """Route plan and model-gateway compatibility projection."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "route_plan_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_ROUTING_SCHEMA_VERSION
    route_plan_id: str
    request_fingerprint: str
    policy_fingerprint: str
    outcome: ExternalCognitionRouteOutcome
    selected_provider_id: str | None = None
    selected_model_id: str | None = None
    candidates: tuple[ExternalCognitionRouteCandidate, ...]
    rejection_reasons: tuple[str, ...]
    existing_model_gateway_route_fingerprint: str
    existing_model_gateway_compatible: bool
    deterministic_ordering: bool = True
    created_at: datetime
    route_plan_fingerprint: str | None = None

    @field_validator("route_plan_id")
    @classmethod
    def route_plan_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator(
        "request_fingerprint",
        "policy_fingerprint",
        "existing_model_gateway_route_fingerprint",
    )
    @classmethod
    def route_plan_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("selected_provider_id", "selected_model_id")
    @classmethod
    def optional_route_ids_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_identifier(value)

    @field_validator("rejection_reasons", mode="before")
    @classmethod
    def route_rejection_reasons_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value or ("none",), field_name="route rejection reasons")

    @field_validator("created_at")
    @classmethod
    def route_plan_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def route_plan_must_be_deterministic(self) -> Self:
        if not self.deterministic_ordering or not self.existing_model_gateway_compatible:
            raise ValueError("external-cognition routing must remain deterministic and compatible")
        if self.outcome in {
            ExternalCognitionRouteOutcome.selected,
            ExternalCognitionRouteOutcome.fallback_selected,
        } and (self.selected_provider_id is None or self.selected_model_id is None):
            raise ValueError("selected route outcome requires selected provider and model")
        return self


class ExternalCognitionFallbackPlan(ExternalCognitionFingerprintedModel):
    """Deterministic fallback plan."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "fallback_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_ROUTING_SCHEMA_VERSION
    fallback_plan_id: str
    primary_model_id: str
    fallback_model_id: str | None
    fallback_eligible: bool
    reason_codes: tuple[str, ...]
    automatic_live_invocation: bool = False
    fallback_fingerprint: str | None = None

    @field_validator("fallback_plan_id", "primary_model_id")
    @classmethod
    def fallback_ids_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("fallback_model_id")
    @classmethod
    def optional_fallback_id_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_identifier(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def fallback_reasons_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value, field_name="fallback reasons")

    @model_validator(mode="after")
    def fallback_must_not_override_boundaries(self) -> Self:
        if self.automatic_live_invocation:
            raise ValueError("fallback cannot invoke live providers")
        if self.fallback_eligible and self.fallback_model_id == self.primary_model_id:
            raise ValueError("fallback must use an eligible different model")
        return self


class ExternalCognitionTrustAssessment(ExternalCognitionFingerprintedModel):
    """Trust assessment for untrusted fixture outputs."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "trust_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_TRUST_SCHEMA_VERSION
    trust_assessment_id: str
    trust_class: ExternalCognitionTrustClass
    schema_validation_fingerprint: str | None = None
    operator_review_required: bool
    factual_truth_confirmed: bool = False
    memory_write_authorized: bool = False
    tool_execution_authorized: bool = False
    created_at: datetime
    trust_fingerprint: str | None = None

    @field_validator("trust_assessment_id")
    @classmethod
    def trust_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("schema_validation_fingerprint")
    @classmethod
    def optional_trust_fingerprint_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def trust_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def trust_must_not_create_authority(self) -> Self:
        if (
            self.factual_truth_confirmed
            or self.memory_write_authorized
            or self.tool_execution_authorized
        ):
            raise ValueError("fixture output cannot become factual trust or execution authority")
        return self


class ExternalCognitionUncertaintyProjection(ExternalCognitionFingerprintedModel):
    """Explicit uncertainty projection."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "uncertainty_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_UNCERTAINTY_SCHEMA_VERSION
    uncertainty_id: str
    declared_confidence: float = Field(ge=0.0, le=1.0)
    confidence_source_code: str
    disagreement_count: int = Field(ge=0)
    missing_evidence_count: int = Field(ge=0)
    unresolved_claim_count: int = Field(ge=0)
    calibration_status_code: str
    operator_review_required: bool
    uncertainty_fingerprint: str | None = None

    @field_validator("uncertainty_id", "confidence_source_code", "calibration_status_code")
    @classmethod
    def uncertainty_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)


class ExternalCognitionProviderError(ExternalCognitionFingerprintedModel):
    """Redacted normalized provider error projection."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "error_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_ERROR_SCHEMA_VERSION
    error_id: str
    normalized_error_class: ExternalCognitionProviderErrorClass
    retryable: bool
    fallback_eligible: bool
    circuit_breaker_effect: ExternalCognitionCircuitState
    safe_error_code: str
    raw_exception_message_retained: bool = False
    provider_response_body_retained: bool = False
    error_fingerprint: str | None = None

    @field_validator("error_id", "safe_error_code")
    @classmethod
    def error_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @model_validator(mode="after")
    def error_must_be_redacted(self) -> Self:
        if self.raw_exception_message_retained or self.provider_response_body_retained:
            raise ValueError("provider errors cannot retain raw provider material")
        return self


class ExternalCognitionProviderErrorNormalization(ExternalCognitionFingerprintedModel):
    """Provider-error normalization evidence."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "normalization_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_ERROR_SCHEMA_VERSION
    normalization_id: str
    input_error_fingerprint: str
    normalized_error: ExternalCognitionProviderError
    normalization_fingerprint: str | None = None

    @field_validator("normalization_id")
    @classmethod
    def normalization_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("input_error_fingerprint")
    @classmethod
    def input_error_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)


class ExternalCognitionRedactionFinding(ExternalCognitionFingerprintedModel):
    """Redaction finding with no retained value."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "finding_fingerprint"

    finding_code: str
    path_fingerprint: str
    value_type_code: str
    replacement_code: str = "redacted"
    finding_fingerprint: str | None = None

    @field_validator("finding_code", "value_type_code", "replacement_code")
    @classmethod
    def finding_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("path_fingerprint")
    @classmethod
    def finding_path_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)


class ExternalCognitionRedactionResult(ExternalCognitionFingerprintedModel):
    """Redaction result retaining findings and fingerprints only."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "redaction_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_EVIDENCE_SCHEMA_VERSION
    result_id: str
    findings: tuple[ExternalCognitionRedactionFinding, ...] = Field(default_factory=tuple)
    finding_count: int = Field(ge=0)
    redaction_fingerprint: str | None = None

    @field_validator("result_id")
    @classmethod
    def redaction_result_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @model_validator(mode="after")
    def redaction_count_must_match(self) -> Self:
        if self.finding_count != len(self.findings):
            raise ValueError("redaction finding count mismatch")
        return self


def redact_payload_projection(payload: Any, *, result_id: str) -> ExternalCognitionRedactionResult:
    """Project protected-material findings without retaining protected values."""

    findings: list[ExternalCognitionRedactionFinding] = []

    def walk(item: Any, path: str) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                normalized = str(key).lower().replace("-", "_")
                next_path = f"{path}.{normalized}"
                if any(part in normalized for part in PROTECTED_KEY_PARTS):
                    findings.append(
                        ExternalCognitionRedactionFinding(
                            finding_code="protected_key",
                            path_fingerprint=external_cognition_fingerprint(next_path),
                            value_type_code=type(nested).__name__.lower(),
                        )
                    )
                walk(nested, next_path)
            return
        if isinstance(item, (list, tuple, set)):
            for index, nested in enumerate(item):
                walk(nested, f"{path}.{index}")
            return
        if isinstance(item, str):
            lowered = item.lower()
            if any(marker in lowered for marker in PROTECTED_VALUE_MARKERS) or re.search(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", item
            ):
                findings.append(
                    ExternalCognitionRedactionFinding(
                        finding_code="protected_value",
                        path_fingerprint=external_cognition_fingerprint(path),
                        value_type_code="string",
                    )
                )

    walk(payload, "$")
    return ExternalCognitionRedactionResult(
        result_id=result_id,
        findings=tuple(findings),
        finding_count=len(findings),
    )


class ExternalCognitionCircuitBreakerPolicy(ExternalCognitionFingerprintedModel):
    """Bounded deterministic circuit-breaker policy."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "policy_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_CIRCUIT_BREAKER_SCHEMA_VERSION
    policy_id: str
    failure_threshold: int = Field(default=2, ge=1, le=MAXIMUM_RETRY_ATTEMPTS)
    half_open_fixture_probe_allowed: bool = True
    background_recovery_enabled: bool = False
    scheduled_probe_enabled: bool = False
    live_provider_health_call_enabled: bool = False
    policy_fingerprint: str | None = None

    @field_validator("policy_id")
    @classmethod
    def circuit_policy_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @model_validator(mode="after")
    def circuit_policy_must_be_local(self) -> Self:
        if (
            self.background_recovery_enabled
            or self.scheduled_probe_enabled
            or self.live_provider_health_call_enabled
        ):
            raise ValueError("circuit breaker cannot use background or live health checks")
        return self


class ExternalCognitionCircuitBreakerState(ExternalCognitionFingerprintedModel):
    """Circuit-breaker state for one model."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "state_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_CIRCUIT_BREAKER_SCHEMA_VERSION
    model_id: str
    state: ExternalCognitionCircuitState = ExternalCognitionCircuitState.closed
    consecutive_failures: int = Field(default=0, ge=0)
    last_transition_code: str = "initial"
    state_fingerprint: str | None = None

    @field_validator("model_id", "last_transition_code")
    @classmethod
    def circuit_state_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)


class ExternalCognitionCircuitBreakerDecision(ExternalCognitionFingerprintedModel):
    """Circuit-breaker decision."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "decision_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_CIRCUIT_BREAKER_SCHEMA_VERSION
    decision_id: str
    prior_state_fingerprint: str
    next_state: ExternalCognitionCircuitBreakerState
    allowed: bool
    reason_codes: tuple[str, ...]
    operator_override_allowed: bool = False
    decision_fingerprint: str | None = None

    @field_validator("decision_id")
    @classmethod
    def circuit_decision_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("prior_state_fingerprint")
    @classmethod
    def prior_circuit_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def circuit_reason_codes_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value, field_name="circuit reason codes")

    @model_validator(mode="after")
    def circuit_decision_must_not_override_open(self) -> Self:
        if self.operator_override_allowed:
            raise ValueError("operator review cannot override an open circuit")
        return self


class InMemoryExternalCognitionCircuitBreakerRepository:
    """In-memory circuit state repository."""

    def __init__(self, policy: ExternalCognitionCircuitBreakerPolicy) -> None:
        self.policy = policy
        self._states: dict[str, ExternalCognitionCircuitBreakerState] = {}

    def state_for_model(self, model_id: str) -> ExternalCognitionCircuitBreakerState:
        return self._states.get(
            model_id,
            ExternalCognitionCircuitBreakerState(model_id=model_id),
        )

    def record_failure(self, model_id: str) -> ExternalCognitionCircuitBreakerState:
        current = self.state_for_model(model_id)
        failures = current.consecutive_failures + 1
        next_state = (
            ExternalCognitionCircuitState.open
            if failures >= self.policy.failure_threshold
            else ExternalCognitionCircuitState.closed
        )
        state = ExternalCognitionCircuitBreakerState(
            model_id=model_id,
            state=next_state,
            consecutive_failures=failures,
            last_transition_code="failure_recorded",
        )
        self._states[model_id] = state
        return state

    def half_open_fixture(self, model_id: str) -> ExternalCognitionCircuitBreakerState:
        state = ExternalCognitionCircuitBreakerState(
            model_id=model_id,
            state=ExternalCognitionCircuitState.half_open,
            consecutive_failures=self.state_for_model(model_id).consecutive_failures,
            last_transition_code="fixture_half_open",
        )
        self._states[model_id] = state
        return state


class ExternalCognitionFixtureRecord(ExternalCognitionFingerprintedModel):
    """Fixture record binding a deterministic safe response projection."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "fixture_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_FIXTURE_SCHEMA_VERSION
    fixture_id: str
    request_intent: ExternalCognitionRequestIntent
    required_capability: ExternalCognitionCapabilityKind
    provider_id: str
    model_id: str
    response_mode: ExternalCognitionOutputMode
    transient_fixture_result_code: str
    declared_token_use: int = Field(ge=0)
    declared_cost_units: int = Field(ge=0)
    declared_latency_units: int = Field(ge=0)
    trust_class: ExternalCognitionTrustClass
    uncertainty_projection: ExternalCognitionUncertaintyProjection
    normalized_error: ExternalCognitionProviderError | None = None
    fixture_fingerprint: str | None = None

    @field_validator("fixture_id", "provider_id", "model_id", "transient_fixture_result_code")
    @classmethod
    def fixture_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)


class ExternalCognitionTransientFixtureResponse:
    """Transient fixture response; raw output is intentionally not serializable."""

    def __init__(
        self,
        *,
        fixture_record: ExternalCognitionFixtureRecord,
        transient_output: object | None,
        response_byte_count: int,
    ) -> None:
        self.fixture_record = fixture_record
        self.transient_output = transient_output
        self.response_byte_count = response_byte_count

    def __repr__(self) -> str:
        return "ExternalCognitionTransientFixtureResponse(<redacted>)"


class DeterministicExternalCognitionFixtureProvider:
    """Deterministic local fixture provider with no live-provider adapter."""

    def __init__(self, records: Sequence[ExternalCognitionFixtureRecord]) -> None:
        self._records = {record.fixture_id: record for record in records}
        self.invocation_count = 0

    def fixture_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._records))

    def invoke(
        self,
        *,
        fixture_id: str,
        transient_output: object | None = None,
    ) -> ExternalCognitionTransientFixtureResponse:
        record = self._records[fixture_id]
        self.invocation_count += 1
        output = (
            transient_output
            if transient_output is not None
            else record.transient_fixture_result_code
        )
        response_bytes = len(json.dumps(_json_safe(output), sort_keys=True).encode("utf-8"))
        return ExternalCognitionTransientFixtureResponse(
            fixture_record=record,
            transient_output=output,
            response_byte_count=response_bytes,
        )


class ExternalCognitionReplayRecord(ExternalCognitionFingerprintedModel):
    """Replay ledger record by request ID and request fingerprint."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "replay_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_REPLAY_SCHEMA_VERSION
    request_id: str
    request_fingerprint: str
    safe_response_fingerprint: str
    outcome: ExternalCognitionReplayOutcome
    fixture_invoked: bool
    created_at: datetime
    replay_fingerprint: str | None = None

    @field_validator("request_id")
    @classmethod
    def replay_request_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("request_fingerprint", "safe_response_fingerprint")
    @classmethod
    def replay_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def replay_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class InMemoryExternalCognitionReplayRepository:
    """In-memory exact-replay repository."""

    def __init__(self) -> None:
        self._records: dict[str, ExternalCognitionReplayRecord] = {}

    def observe(
        self,
        *,
        request: ExternalCognitionRequestEnvelope,
        safe_response_fingerprint: str,
        created_at: datetime,
    ) -> ExternalCognitionReplayRecord:
        existing = self._records.get(request.request_id)
        if existing is None:
            record = ExternalCognitionReplayRecord(
                request_id=request.request_id,
                request_fingerprint=request.request_fingerprint or "",
                safe_response_fingerprint=safe_response_fingerprint,
                outcome=ExternalCognitionReplayOutcome.new,
                fixture_invoked=True,
                created_at=created_at,
            )
            self._records[request.request_id] = record
            return record
        if existing.request_fingerprint == request.request_fingerprint:
            return ExternalCognitionReplayRecord(
                request_id=request.request_id,
                request_fingerprint=existing.request_fingerprint,
                safe_response_fingerprint=existing.safe_response_fingerprint,
                outcome=ExternalCognitionReplayOutcome.exact_replay,
                fixture_invoked=False,
                created_at=created_at,
            )
        return ExternalCognitionReplayRecord(
            request_id=request.request_id,
            request_fingerprint=request.request_fingerprint or "",
            safe_response_fingerprint=ZERO_FINGERPRINT,
            outcome=ExternalCognitionReplayOutcome.changed_replay_rejected,
            fixture_invoked=False,
            created_at=created_at,
        )


class ExternalCognitionResponseEnvelope(ExternalCognitionFingerprintedModel):
    """Retained response envelope without raw output."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "response_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_RESPONSE_SCHEMA_VERSION
    response_id: str
    request_fingerprint: str
    provider_manifest_fingerprint: str
    model_manifest_fingerprint: str
    route_plan_fingerprint: str
    fallback_plan_fingerprint: str | None = None
    retry_plan_fingerprint: str | None = None
    response_content_fingerprint: str
    response_byte_count: int = Field(ge=0)
    deterministic_token_usage: int = Field(ge=0)
    structured_output_validation_fingerprint: str | None = None
    trust_assessment: ExternalCognitionTrustAssessment
    uncertainty_projection: ExternalCognitionUncertaintyProjection
    normalized_error: ExternalCognitionProviderError | None = None
    operator_review_required: bool
    created_at: datetime
    raw_response_absent: bool = True
    production_effect: bool = False
    response_fingerprint: str | None = None

    @field_validator("response_id")
    @classmethod
    def response_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator(
        "request_fingerprint",
        "provider_manifest_fingerprint",
        "model_manifest_fingerprint",
        "route_plan_fingerprint",
        "response_content_fingerprint",
    )
    @classmethod
    def response_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator(
        "fallback_plan_fingerprint",
        "retry_plan_fingerprint",
        "structured_output_validation_fingerprint",
    )
    @classmethod
    def optional_response_fingerprints_must_be_safe(
        cls, value: str | None
    ) -> str | None:
        return None if value is None else ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def response_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def response_must_not_retain_raw_output(self) -> Self:
        if not self.raw_response_absent or self.production_effect:
            raise ValueError("response envelope cannot retain raw output or production effects")
        return self


class ExternalCognitionOperatorReviewRecord(ExternalCognitionFingerprintedModel):
    """Operator-review record by safe fingerprints only."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "review_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_RESPONSE_SCHEMA_VERSION
    review_id: str
    response_fingerprint: str
    trust_class: ExternalCognitionTrustClass
    reason_codes: tuple[str, ...]
    created_at: datetime
    raw_output_absent: bool = True
    review_fingerprint: str | None = None

    @field_validator("review_id")
    @classmethod
    def review_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("response_fingerprint")
    @classmethod
    def review_response_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def review_reasons_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(value, field_name="operator review reasons")

    @field_validator("created_at")
    @classmethod
    def review_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class ExternalCognitionAuditRecord(ExternalCognitionFingerprintedModel):
    """Redacted audit record."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "audit_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_AUDIT_SCHEMA_VERSION
    audit_id: str
    session_id: str
    event_type: str
    outcome: str
    subject_fingerprint: str = ZERO_FINGERPRINT
    prior_audit_fingerprint: str = ZERO_FINGERPRINT
    created_at: datetime
    audit_fingerprint: str | None = None
    raw_payload_absent: bool = True

    @field_validator("audit_id", "session_id", "event_type", "outcome")
    @classmethod
    def audit_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("subject_fingerprint", "prior_audit_fingerprint")
    @classmethod
    def audit_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def audit_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def audit_must_be_redacted(self) -> Self:
        if not self.raw_payload_absent:
            raise ValueError("audit records cannot retain raw payloads")
        return self


class InMemoryExternalCognitionAuditLedger:
    """In-memory redacted audit ledger."""

    def __init__(self) -> None:
        self._records: dict[str, list[ExternalCognitionAuditRecord]] = {}

    def append(
        self,
        *,
        session_id: str,
        event_type: str,
        outcome: str,
        created_at: datetime,
        subject_fingerprint: str = ZERO_FINGERPRINT,
    ) -> ExternalCognitionAuditRecord:
        records = self._records.setdefault(session_id, [])
        record = ExternalCognitionAuditRecord(
            audit_id=f"audit-{session_id}-{len(records) + 1}",
            session_id=session_id,
            event_type=event_type,
            outcome=outcome,
            subject_fingerprint=subject_fingerprint,
            prior_audit_fingerprint=(
                records[-1].audit_fingerprint or ZERO_FINGERPRINT
                if records
                else ZERO_FINGERPRINT
            ),
            created_at=created_at,
        )
        records.append(record)
        return record

    def chain_head(self, session_id: str) -> str:
        records = self._records.get(session_id, [])
        return (
            records[-1].audit_fingerprint or ZERO_FINGERPRINT
            if records
            else ZERO_FINGERPRINT
        )

    def list_records(self, session_id: str) -> tuple[ExternalCognitionAuditRecord, ...]:
        return tuple(self._records.get(session_id, ()))


class ExternalCognitionObservabilitySnapshot(ExternalCognitionFingerprintedModel):
    """Redacted observability snapshot."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "snapshot_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_OBSERVABILITY_SCHEMA_VERSION
    snapshot_id: str
    session_id: str
    counters: Mapping[str, int]
    trust_class_counts: Mapping[str, int]
    uncertainty_counts: Mapping[str, int]
    circuit_states: Mapping[str, str]
    audit_chain_head: str
    evidence_chain_head: str
    created_at: datetime
    snapshot_fingerprint: str | None = None

    @field_validator("snapshot_id", "session_id")
    @classmethod
    def snapshot_strings_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("audit_chain_head", "evidence_chain_head")
    @classmethod
    def snapshot_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def snapshot_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("counters", "trust_class_counts", "uncertainty_counts", "circuit_states")
    @classmethod
    def snapshot_mappings_must_be_safe(
        cls, value: Mapping[str, int] | Mapping[str, str]
    ) -> Mapping[str, int] | Mapping[str, str]:
        reject_protected_material(value)
        return cast(Mapping[str, int] | Mapping[str, str], dict(sorted(value.items())))


class ExternalCognitionIntegrityReport(ExternalCognitionFingerprintedModel):
    """Integrity report for the fixture-only evidence chain."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "report_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_INTEGRITY_SCHEMA_VERSION
    report_id: str
    status: ExternalCognitionIntegrityStatus
    checked_categories: tuple[str, ...]
    finding_codes: tuple[str, ...] = Field(default_factory=tuple)
    prohibited_effect_counters: Mapping[str, int]
    audit_chain_head: str
    evidence_chain_head: str
    created_at: datetime
    report_fingerprint: str | None = None

    @field_validator("report_id")
    @classmethod
    def report_id_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator("checked_categories", "finding_codes", mode="before")
    @classmethod
    def report_sets_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_sorted_unique(
            value or (),
            field_name="integrity report set",
            allow_empty=True,
        )

    @field_validator("audit_chain_head", "evidence_chain_head")
    @classmethod
    def report_chain_heads_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def report_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def integrity_report_must_match_zero_effects(self) -> Self:
        if any(value != 0 for value in self.prohibited_effect_counters.values()):
            raise ValueError("integrity report contains prohibited effects")
        if self.status == ExternalCognitionIntegrityStatus.passed and self.finding_codes:
            raise ValueError("passed integrity report cannot contain findings")
        return self


class ExternalCognitionEvidenceBundle(ExternalCognitionFingerprintedModel):
    """Redacted committed evidence bundle."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "evidence_fingerprint"

    schema_version: str = EXTERNAL_COGNITION_EVIDENCE_SCHEMA_VERSION
    evidence_id: str
    program_id: str = PROGRAM_ID
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    session_id: str
    audit_chain_head: str
    evidence_chain_head: str
    observability_fingerprint: str
    integrity_report_fingerprint: str
    counters: Mapping[str, int]
    prohibited_effect_counters: Mapping[str, int]
    redacted: bool = True
    provider_effect: bool = False
    network_effect: bool = False
    memory_effect: bool = False
    tool_effect: bool = False
    production_effect: bool = False
    created_at: datetime
    evidence_fingerprint: str | None = None

    @field_validator("evidence_id", "session_id")
    @classmethod
    def evidence_ids_must_be_safe(cls, value: str) -> str:
        return ensure_identifier(value)

    @field_validator(
        "audit_chain_head",
        "evidence_chain_head",
        "observability_fingerprint",
        "integrity_report_fingerprint",
    )
    @classmethod
    def evidence_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def evidence_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def evidence_must_be_redacted_and_zero_effect(self) -> Self:
        if (
            not self.redacted
            or self.provider_effect
            or self.network_effect
            or self.memory_effect
            or self.tool_effect
            or self.production_effect
            or any(value != 0 for value in self.prohibited_effect_counters.values())
        ):
            raise ValueError("external-cognition evidence must remain redacted and no-effect")
        return self


PROHIBITED_EFFECT_COUNTERS: dict[str, int] = {
    "actual_model_provider_calls": 0,
    "provider_network_adapter_calls": 0,
    "public_network_calls": 0,
    "external_network_egress_calls": 0,
    "dns_resolutions": 0,
    "provider_credentials_generated": 0,
    "provider_credentials_read": 0,
    "provider_credentials_persisted": 0,
    "provider_tokens_read": 0,
    "provider_tokens_persisted": 0,
    "authorization_headers_created": 0,
    "raw_prompts_persisted": 0,
    "raw_responses_persisted": 0,
    "hidden_reasoning_records": 0,
    "model_output_triggered_executions": 0,
    "model_output_tool_calls": 0,
    "memory_writes": 0,
    "verified_knowledge_promotions": 0,
    "belief_mutations": 0,
    "external_connector_calls": 0,
    "external_tool_executions": 0,
    "background_cycles": 0,
    "scheduled_provider_calls": 0,
    "source_mutations": 0,
    "git_operations": 0,
    "runtime_created_pull_requests": 0,
    "automatic_merges": 0,
    "production_deployments": 0,
    "model_weight_changes": 0,
}
