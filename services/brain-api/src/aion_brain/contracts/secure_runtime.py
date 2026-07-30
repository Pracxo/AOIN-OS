"""Controlled local secure-runtime foundation contracts for AION-231."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import isfinite
from threading import RLock
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.guardrails import GuardrailDecision
from aion_brain.contracts.identity_assertion import (
    AUTHORIZATION_TRANSACTION_ID as IDENTITY_COMPONENT_AUTHORIZATION_ID,
)
from aion_brain.contracts.identity_assertion import (
    IdentityAssertionEnvelope,
    assertion_fingerprint,
    normalize_utc_datetime,
    reject_protected_material,
)
from aion_brain.contracts.identity_assertion_replay import (
    AUTHORIZATION_TRANSACTION_ID as REPLAY_COMPONENT_AUTHORIZATION_ID,
)
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.risk import RiskAssessment
from aion_brain.contracts.scopes import ActorContext
from aion_brain.production_auth.canonical import sha256_fingerprint

SECURE_RUNTIME_CONTRACT_SCHEMA_VERSION = "aion-secure-runtime/v1"
SECURE_RUNTIME_AUTHORIZATION_SCHEMA_VERSION = "aion-secure-runtime-authorization/v1"
SECURE_OPERATOR_IDENTITY_BINDING_SCHEMA_VERSION = "aion-secure-runtime-operator-identity/v1"
SECURE_REQUEST_IDENTITY_BINDING_SCHEMA_VERSION = "aion-secure-runtime-request-identity/v1"
SECURE_ACTOR_CONTEXT_BINDING_SCHEMA_VERSION = "aion-secure-runtime-actor-context/v1"
SECURE_RUNTIME_SESSION_SCHEMA_VERSION = "aion-secure-runtime-session/v1"
SECURE_RUNTIME_STAGE_COMMAND_SCHEMA_VERSION = "aion-secure-runtime-stage-command/v1"
SECURE_RUNTIME_STAGE_RECEIPT_SCHEMA_VERSION = "aion-secure-runtime-stage-receipt/v1"
SECURE_RUNTIME_REQUEST_SCHEMA_VERSION = "aion-secure-runtime-request/v1"
SECURE_CAPABILITY_PLAN_SCHEMA_VERSION = "aion-secure-runtime-capability-plan/v1"
SECURE_DECISION_BINDING_SCHEMA_VERSION = "aion-secure-runtime-decision-binding/v1"
SECURE_APPROVAL_EVIDENCE_SCHEMA_VERSION = "aion-secure-runtime-approval-evidence/v1"
SECURE_SIDE_EFFECT_BUDGET_SCHEMA_VERSION = "aion-secure-runtime-side-effect-budget/v1"
SECURE_RUNTIME_GUARD_SCHEMA_VERSION = "aion-secure-runtime-guard/v1"
SECURE_RUNTIME_KILL_SWITCH_SCHEMA_VERSION = "aion-secure-runtime-kill-switch/v1"
SECURE_SIMULATED_DISPATCH_SCHEMA_VERSION = "aion-secure-runtime-simulated-dispatch/v1"
SECURE_RUNTIME_AUDIT_SCHEMA_VERSION = "aion-secure-runtime-audit/v1"
SECURE_RUNTIME_OBSERVABILITY_SCHEMA_VERSION = "aion-secure-runtime-observability/v1"
SECURE_RUNTIME_HEALTH_SCHEMA_VERSION = "aion-secure-runtime-health/v1"
SECURE_RUNTIME_CHECKPOINT_SCHEMA_VERSION = "aion-secure-runtime-checkpoint/v1"
SECURE_RUNTIME_INTEGRITY_SCHEMA_VERSION = "aion-secure-runtime-integrity/v1"
SECURE_RUNTIME_EVIDENCE_SCHEMA_VERSION = "aion-secure-runtime-evidence/v1"
SECURE_RUNTIME_REASON_REGISTRY_VERSION = "aion-secure-runtime-reasons/v1"

PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
AUTHORIZATION_TRANSACTION_ID = "AION-230-SRI-0001"
APPROVAL_RECORD_ID = "AION-230-SRI-0001"
IMPLEMENTATION_TASK = "AION-231"
FORMAL_CLOSEOUT_TASK = "AION-232"
AUTHORIZATION_SCOPE = (
    "local-operator-authenticated-session-offline-identity-request-context-"
    "actor-context-replay-guarded-capability-dispatch-policy-risk-approval-"
    "kill-switch-audit-observability-foundation-core"
)
LOCAL_OPERATOR_CONFIRMATION_TEXT = "START_CONTROLLED_LOCAL_OPERATOR_RUNTIME"
ZERO_FINGERPRINT = "0000000000000000000000000000000000000000000000000000000000000000"

SAFE_IDENTIFIER_RE = r"^[A-Za-z0-9._:-]{1,128}$"
LOWER_SHA256_RE = r"^[0-9a-f]{64}$"
MAXIMUM_SESSION_SECONDS = 3600
MAXIMUM_REQUESTS_PER_SESSION = 100
MAXIMUM_CONCURRENT_REQUESTS = 4
MAXIMUM_APPROVAL_EVIDENCE_RECORDS = 4


class SecureRuntimeMode(StrEnum):
    """Allowed local runtime modes."""

    deterministic_simulation = "deterministic_simulation"
    operator_invoked_local = "operator_invoked_local"


class SecureRuntimeSessionState(StrEnum):
    """Explicit local secure-runtime state machine states."""

    drafted = "drafted"
    authorized = "authorized"
    identity_assertion_verified = "identity_assertion_verified"
    request_identity_bound = "request_identity_bound"
    actor_context_bound = "actor_context_bound"
    replay_validation_passed = "replay_validation_passed"
    runtime_guard_ready = "runtime_guard_ready"
    session_active = "session_active"
    request_validated = "request_validated"
    capability_plan_created = "capability_plan_created"
    policy_evaluated = "policy_evaluated"
    risk_evaluated = "risk_evaluated"
    guardrails_evaluated = "guardrails_evaluated"
    approval_validated = "approval_validated"
    simulated_dispatch_completed = "simulated_dispatch_completed"
    response_recorded = "response_recorded"
    session_closed = "session_closed"
    abstained = "abstained"
    blocked = "blocked"
    killed = "killed"
    expired = "expired"
    failed = "failed"


class SecureRuntimeStageDisposition(StrEnum):
    """Stage receipt disposition."""

    executed = "executed"
    explicit_no_op = "explicit_no_op"
    abstained = "abstained"
    blocked = "blocked"
    killed = "killed"
    expired = "expired"
    failed = "failed"


class SecureRuntimeCapabilityRisk(StrEnum):
    """Closed capability risk classes."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class SecureRuntimeGuardOutcome(StrEnum):
    """Runtime guard outcomes for simulation-only dispatch."""

    allow_simulation = "allow_simulation"
    require_approval = "require_approval"
    abstain = "abstain"
    block = "block"
    kill = "kill"


class SecureRuntimeKillSwitchStatus(StrEnum):
    """Operator kill-switch state."""

    clear = "clear"
    active = "active"


class SecureRuntimeDispatchStatus(StrEnum):
    """Simulation-only dispatch status."""

    simulated = "simulated"
    blocked = "blocked"
    killed = "killed"
    abstained = "abstained"


class SecureRuntimeIntegrityStatus(StrEnum):
    """Integrity audit status."""

    passed = "passed"
    failed = "failed"


TERMINAL_STATES = {
    SecureRuntimeSessionState.abstained,
    SecureRuntimeSessionState.blocked,
    SecureRuntimeSessionState.killed,
    SecureRuntimeSessionState.expired,
    SecureRuntimeSessionState.failed,
    SecureRuntimeSessionState.session_closed,
}
ALLOWED_STATE_TRANSITIONS: dict[
    SecureRuntimeSessionState, tuple[SecureRuntimeSessionState, ...]
] = {
    SecureRuntimeSessionState.drafted: (SecureRuntimeSessionState.authorized,),
    SecureRuntimeSessionState.authorized: (SecureRuntimeSessionState.identity_assertion_verified,),
    SecureRuntimeSessionState.identity_assertion_verified: (
        SecureRuntimeSessionState.request_identity_bound,
    ),
    SecureRuntimeSessionState.request_identity_bound: (
        SecureRuntimeSessionState.actor_context_bound,
    ),
    SecureRuntimeSessionState.actor_context_bound: (
        SecureRuntimeSessionState.replay_validation_passed,
    ),
    SecureRuntimeSessionState.replay_validation_passed: (
        SecureRuntimeSessionState.runtime_guard_ready,
    ),
    SecureRuntimeSessionState.runtime_guard_ready: (SecureRuntimeSessionState.session_active,),
    SecureRuntimeSessionState.session_active: (
        SecureRuntimeSessionState.request_validated,
        SecureRuntimeSessionState.session_closed,
    ),
    SecureRuntimeSessionState.request_validated: (
        SecureRuntimeSessionState.capability_plan_created,
    ),
    SecureRuntimeSessionState.capability_plan_created: (
        SecureRuntimeSessionState.policy_evaluated,
    ),
    SecureRuntimeSessionState.policy_evaluated: (SecureRuntimeSessionState.risk_evaluated,),
    SecureRuntimeSessionState.risk_evaluated: (SecureRuntimeSessionState.guardrails_evaluated,),
    SecureRuntimeSessionState.guardrails_evaluated: (SecureRuntimeSessionState.approval_validated,),
    SecureRuntimeSessionState.approval_validated: (
        SecureRuntimeSessionState.simulated_dispatch_completed,
    ),
    SecureRuntimeSessionState.simulated_dispatch_completed: (
        SecureRuntimeSessionState.response_recorded,
    ),
    SecureRuntimeSessionState.response_recorded: (
        SecureRuntimeSessionState.request_validated,
        SecureRuntimeSessionState.session_closed,
    ),
}


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def secure_runtime_fingerprint(payload: Any) -> str:
    """Return the repository-standard deterministic SHA-256 fingerprint."""

    return sha256_fingerprint(_json_safe(payload))


def local_operator_confirmation_fingerprint() -> str:
    """Fingerprint the exact local operator confirmation phrase."""

    return secure_runtime_fingerprint(
        {"confirmation": LOCAL_OPERATOR_CONFIRMATION_TEXT, "program_id": PROGRAM_ID}
    )


def text_fingerprint(kind: str, value: str | None) -> str:
    """Fingerprint a redacted text value by kind without retaining raw text."""

    return secure_runtime_fingerprint({"kind": kind, "value": value or ""})


def ensure_safe_identifier(value: str, *, field_name: str = "identifier") -> str:
    """Validate a bounded ASCII identifier."""

    import re

    if not isinstance(value, str) or re.fullmatch(SAFE_IDENTIFIER_RE, value) is None:
        raise ValueError(f"{field_name} must be a safe bounded ASCII identifier")
    return value


def ensure_sha256(value: str, *, field_name: str = "fingerprint") -> str:
    """Validate a lowercase SHA-256 fingerprint."""

    import re

    if not isinstance(value, str) or re.fullmatch(LOWER_SHA256_RE, value) is None:
        raise ValueError(f"{field_name} must be a 64-character lowercase SHA-256 value")
    return value


def ensure_utc(value: datetime) -> datetime:
    """Normalize and require timezone-aware UTC timestamps."""

    return normalize_utc_datetime(value)


def ensure_sorted_unique(values: object, *, field_name: str) -> tuple[str, ...]:
    """Return a sorted unique tuple and reject wildcards or blanks."""

    if values is None:
        iterable: Iterable[object] = ()
    elif isinstance(values, str):
        raise ValueError(f"{field_name} must be a collection")
    elif isinstance(values, Iterable):
        iterable = values
    else:
        raise ValueError(f"{field_name} must be a collection")
    result = tuple(sorted(str(item) for item in iterable))
    if not result:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} must be unique")
    for item in result:
        if not item.strip() or item != item.strip() or item == "*":
            raise ValueError(f"{field_name} contains an unsafe value")
    return result


def reject_secure_runtime_protected_material(value: Any) -> None:
    """Reject protected material recursively without echoing rejected values."""

    reject_protected_material(value)
    forbidden_keys = {
        "assertion",
        "assertion_payload",
        "assertion_signature",
        "authorization_header",
        "client_secret",
        "cookie",
        "credential",
        "decision_payload",
        "diff",
        "hidden_reasoning",
        "password",
        "private_key",
        "private_" + "key_seed",
        "prompt",
        "public_key_base64url",
        "raw_assertion",
        "raw_body",
        "raw_prompt",
        "refresh_token",
        "request_body",
        "session_token",
        "signature",
        "source_patch",
        "token",
    }
    forbidden_value_markers = (
        "authorization header",
        "bearer ",
        "client secret",
        "hidden reasoning",
        "private key",
        "raw assertion",
        "raw prompt",
        "refresh token",
        "session token",
    )

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                normalized = str(key).lower().replace("-", "_")
                if normalized in forbidden_keys:
                    raise ValueError("protected material is not allowed")
                walk(nested)
            return
        if isinstance(item, (list, tuple, set)):
            for nested in item:
                walk(nested)
            return
        if isinstance(item, str):
            lowered = item.lower()
            if any(marker in lowered for marker in forbidden_value_markers):
                raise ValueError("protected material is not allowed")

    walk(value)


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
    if isinstance(value, float):
        if not isfinite(value):
            raise TypeError("non-finite numeric values are not supported")
        return value
    return value


class SecureRuntimeBaseModel(BaseModel):
    """Base strict Pydantic v2 model for AION-231 contracts."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class SecureRuntimeFingerprintedModel(SecureRuntimeBaseModel):
    """Model that self-populates and verifies one named fingerprint field."""

    _fingerprint_field: ClassVar[str | None] = None

    @model_validator(mode="after")
    def secure_runtime_fingerprint_must_match(self) -> Self:
        field_name = self._fingerprint_field
        if field_name is None:
            return self
        expected = secure_runtime_fingerprint(self.model_dump(mode="json", exclude={field_name}))
        current = getattr(self, field_name)
        if current is None:
            object.__setattr__(self, field_name, expected)
        elif current != expected:
            raise ValueError("fingerprint must match canonical secure runtime payload")
        return self


class SecureCapabilityManifest(SecureRuntimeFingerprintedModel):
    """Immutable entry in the closed simulation-only capability registry."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "manifest_fingerprint"

    capability_code: str
    action_type: str
    resource_type: str
    required_permissions: tuple[str, ...]
    required_security_scopes: tuple[str, ...]
    risk: SecureRuntimeCapabilityRisk
    approval_required: bool
    side_effect_class: Literal["none"] = "none"
    simulation_only: bool = True
    actual_execution_available: bool = False
    production_effect: bool = False
    manifest_fingerprint: str | None = None

    @field_validator("required_permissions", "required_security_scopes", mode="before")
    @classmethod
    def capability_requirements_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("capability requirements must be a collection")
        return ensure_sorted_unique(value or (), field_name="capability requirements")

    @model_validator(mode="after")
    def capability_manifest_must_be_simulation_only(self) -> Self:
        if not self.simulation_only or self.actual_execution_available or self.production_effect:
            raise ValueError("capability manifests must remain simulation-only")
        if self.side_effect_class != "none":
            raise ValueError("capability manifests cannot declare side effects")
        return self


def _capability_manifest(
    *,
    capability_code: str,
    action_type: str,
    resource_type: str,
    required_permissions: tuple[str, ...],
    required_security_scopes: tuple[str, ...],
    risk: SecureRuntimeCapabilityRisk,
    approval_required: bool,
) -> SecureCapabilityManifest:
    return SecureCapabilityManifest(
        capability_code=capability_code,
        action_type=action_type,
        resource_type=resource_type,
        required_permissions=required_permissions,
        required_security_scopes=required_security_scopes,
        risk=risk,
        approval_required=approval_required,
    )


CLOSED_CAPABILITY_REGISTRY: dict[str, SecureCapabilityManifest] = {
    "secure_runtime.health.read": _capability_manifest(
        capability_code="secure_runtime.health.read",
        action_type="secure_runtime.health.read",
        resource_type="secure_runtime_health",
        required_permissions=("secure_runtime:read",),
        required_security_scopes=("secure-runtime:health",),
        risk=SecureRuntimeCapabilityRisk.low,
        approval_required=False,
    ),
    "secure_runtime.observability.read": _capability_manifest(
        capability_code="secure_runtime.observability.read",
        action_type="secure_runtime.observability.read",
        resource_type="secure_runtime_observability",
        required_permissions=("secure_runtime:read",),
        required_security_scopes=("secure-runtime:observability",),
        risk=SecureRuntimeCapabilityRisk.low,
        approval_required=False,
    ),
    "secure_runtime.audit.read": _capability_manifest(
        capability_code="secure_runtime.audit.read",
        action_type="secure_runtime.audit.read",
        resource_type="secure_runtime_audit",
        required_permissions=("secure_runtime:audit:read",),
        required_security_scopes=("secure-runtime:audit",),
        risk=SecureRuntimeCapabilityRisk.medium,
        approval_required=True,
    ),
    "secure_runtime.fixture.replay": _capability_manifest(
        capability_code="secure_runtime.fixture.replay",
        action_type="secure_runtime.fixture.replay",
        resource_type="secure_runtime_fixture",
        required_permissions=("secure_runtime:fixture:replay",),
        required_security_scopes=("secure-runtime:fixture-replay",),
        risk=SecureRuntimeCapabilityRisk.low,
        approval_required=False,
    ),
    "brain.think.simulate": _capability_manifest(
        capability_code="brain.think.simulate",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        required_permissions=("brain:think:simulate",),
        required_security_scopes=("secure-runtime:simulate-capability",),
        risk=SecureRuntimeCapabilityRisk.medium,
        approval_required=True,
    ),
}
CLOSED_CAPABILITY_CODES: tuple[str, ...] = tuple(sorted(CLOSED_CAPABILITY_REGISTRY))


def capability_manifest_for(capability_code: str) -> SecureCapabilityManifest:
    """Return an immutable manifest or fail closed for unknown capabilities."""

    if capability_code not in CLOSED_CAPABILITY_REGISTRY:
        raise ValueError("unknown secure-runtime capability")
    return CLOSED_CAPABILITY_REGISTRY[capability_code]


class SecureRuntimeComponentInvocationBinding(SecureRuntimeFingerprintedModel):
    """Current-authority binding for read-only historical component invocation."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    binding_id: str
    current_program_id: str = PROGRAM_ID
    current_authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    component_name: str
    component_implementation_task: str
    component_contract_authorization_id: str
    component_contract_authorization_closed: bool = True
    component_contract_authorization_reactivated: bool = False
    component_invocation_authorized_by_current_parent: bool = True
    session_id: str
    request_id: str | None = None
    input_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    output_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    invoked_at: datetime
    binding_fingerprint: str | None = None
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "request_id")
    @classmethod
    def identifiers_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_safe_identifier(value)

    @field_validator("input_fingerprints", "output_fingerprints")
    @classmethod
    def fingerprints_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in value)

    @field_validator("invoked_at")
    @classmethod
    def invoked_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def current_authority_must_hold(self) -> Self:
        if self.current_program_id != PROGRAM_ID:
            raise ValueError("current program mismatch")
        if self.current_authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("current authorization mismatch")
        if (
            not self.component_contract_authorization_closed
            or self.component_contract_authorization_reactivated
        ):
            raise ValueError("historical component authorization cannot be reactivated")
        if (
            not self.component_invocation_authorized_by_current_parent
            or not self.read_only
            or not self.redacted
            or self.runtime_effect
        ):
            raise ValueError("component invocation binding must remain read-only and redacted")
        return self


class SecureRuntimeAuthorizationEnvelope(SecureRuntimeFingerprintedModel):
    """Explicit local operator authorization envelope for one session."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "envelope_fingerprint"

    schema_version: str = SECURE_RUNTIME_AUTHORIZATION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    implementation_task: str = IMPLEMENTATION_TASK
    formal_closeout_task: str = FORMAL_CLOSEOUT_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    session_id: str
    operator_identity_fingerprint: str
    assertion_fingerprint: str
    expected_issuer: str
    expected_audience: str
    allowed_workspace_id: str
    allowed_roles: tuple[str, ...]
    allowed_permissions: tuple[str, ...]
    allowed_security_scopes: tuple[str, ...]
    allowed_capability_codes: tuple[str, ...]
    maximum_requests: int = Field(ge=1, le=MAXIMUM_REQUESTS_PER_SESSION)
    maximum_concurrent_requests: int = Field(ge=1, le=MAXIMUM_CONCURRENT_REQUESTS)
    maximum_session_seconds: int = Field(ge=1, le=MAXIMUM_SESSION_SECONDS)
    created_at: datetime
    expires_at: datetime
    confirmation_fingerprint: str
    operator_invoked: bool = True
    local_session: bool = True
    production_runtime: bool = False
    external_identity_provider: bool = False
    network_access: bool = False
    credential_persistence: bool = False
    token_persistence: bool = False
    actual_execution: bool = False
    production_effect: bool = False
    envelope_fingerprint: str | None = None

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SECURE_RUNTIME_AUTHORIZATION_SCHEMA_VERSION:
            raise ValueError("schema_version mismatch")
        return value

    @field_validator("session_id")
    @classmethod
    def session_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value, field_name="session_id")

    @field_validator(
        "operator_identity_fingerprint",
        "assertion_fingerprint",
        "confirmation_fingerprint",
    )
    @classmethod
    def authorization_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator(
        "allowed_roles",
        "allowed_permissions",
        "allowed_security_scopes",
        "allowed_capability_codes",
        mode="before",
    )
    @classmethod
    def authorization_sets_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("authorization sets must be collections")
        return ensure_sorted_unique(value or (), field_name="authorization set")

    @field_validator("created_at", "expires_at")
    @classmethod
    def authorization_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def authorization_envelope_must_be_exact(self) -> Self:
        if (
            self.program_id != PROGRAM_ID
            or self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or self.approval_record_id != APPROVAL_RECORD_ID
            or self.implementation_task != IMPLEMENTATION_TASK
            or self.formal_closeout_task != FORMAL_CLOSEOUT_TASK
            or self.authorization_scope != AUTHORIZATION_SCOPE
        ):
            raise ValueError("AION-230-SRI-0001 authorization mismatch")
        if self.expires_at <= self.created_at:
            raise ValueError("authorization envelope must expire after creation")
        if self.expires_at - self.created_at > timedelta(seconds=MAXIMUM_SESSION_SECONDS):
            raise ValueError("authorization envelope exceeds one hour")
        if self.confirmation_fingerprint != local_operator_confirmation_fingerprint():
            raise ValueError("local operator confirmation fingerprint mismatch")
        if set(self.allowed_capability_codes) - set(CLOSED_CAPABILITY_CODES):
            raise ValueError("authorization contains unknown capability")
        if (
            not self.operator_invoked
            or not self.local_session
            or self.production_runtime
            or self.external_identity_provider
            or self.network_access
            or self.credential_persistence
            or self.token_persistence
            or self.actual_execution
            or self.production_effect
        ):
            raise ValueError("authorization envelope cannot grant external or production effects")
        return self


class SecureOperatorIdentityBinding(SecureRuntimeFingerprintedModel):
    """Redacted binding from one verified offline assertion to one local operator."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = SECURE_OPERATOR_IDENTITY_BINDING_SCHEMA_VERSION
    binding_id: str
    current_authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    session_id: str
    assertion_id: str
    assertion_fingerprint: str
    verification_bundle_fingerprint: str
    replay_bundle_fingerprint: str
    replay_key_fingerprint: str
    issuer_fingerprint: str
    subject_fingerprint: str
    operator_identity_fingerprint: str
    workspace_fingerprint: str
    role_fingerprints: tuple[str, ...]
    permission_fingerprints: tuple[str, ...]
    security_scope_fingerprints: tuple[str, ...]
    cryptographic_verification_passed: bool = True
    replay_validation_passed: bool = True
    local_operator_authenticated: bool = True
    production_request_authenticated: bool = False
    component_invocation_bindings: tuple[SecureRuntimeComponentInvocationBinding, ...]
    created_at: datetime
    expires_at: datetime
    binding_fingerprint: str | None = None
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "assertion_id")
    @classmethod
    def identity_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "assertion_fingerprint",
        "verification_bundle_fingerprint",
        "replay_bundle_fingerprint",
        "replay_key_fingerprint",
        "issuer_fingerprint",
        "subject_fingerprint",
        "operator_identity_fingerprint",
        "workspace_fingerprint",
    )
    @classmethod
    def identity_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("role_fingerprints", "permission_fingerprints", "security_scope_fingerprints")
    @classmethod
    def identity_fingerprint_sets_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in sorted(value))

    @field_validator("created_at", "expires_at")
    @classmethod
    def identity_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def identity_binding_must_be_local_and_redacted(self) -> Self:
        if self.current_authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("current authorization mismatch")
        if self.expires_at <= self.created_at:
            raise ValueError("identity binding expiry mismatch")
        if (
            not self.cryptographic_verification_passed
            or not self.replay_validation_passed
            or not self.local_operator_authenticated
            or self.production_request_authenticated
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("identity binding must remain redacted local authentication only")
        return self


class SecureRequestIdentityBinding(SecureRuntimeFingerprintedModel):
    """Secure request identity projected only from verified signed claims."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = SECURE_REQUEST_IDENTITY_BINDING_SCHEMA_VERSION
    binding_id: str
    session_id: str
    request_id: str
    trace_id: str
    correlation_id: str
    operator_identity_fingerprint: str
    actor_id: str
    subject_fingerprint: str
    workspace_id: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    security_scopes: tuple[str, ...]
    assertion_fingerprint: str
    verification_bundle_fingerprint: str
    replay_bundle_fingerprint: str
    authenticated_local_operator: bool = True
    production_authentication: bool = False
    header_identity_used: bool = False
    cookie_identity_used: bool = False
    token_identity_used: bool = False
    external_identity_provider_used: bool = False
    binding_fingerprint: str | None = None
    created_at: datetime
    expires_at: datetime
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "request_id", "trace_id", "correlation_id")
    @classmethod
    def request_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "operator_identity_fingerprint",
        "subject_fingerprint",
        "assertion_fingerprint",
        "verification_bundle_fingerprint",
        "replay_bundle_fingerprint",
    )
    @classmethod
    def request_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("roles", "permissions", "security_scopes", mode="before")
    @classmethod
    def request_sets_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("request identity sets must be collections")
        return ensure_sorted_unique(value or (), field_name="request identity set")

    @field_validator("created_at", "expires_at")
    @classmethod
    def request_identity_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def request_identity_must_not_use_headers_or_tokens(self) -> Self:
        if (
            not self.authenticated_local_operator
            or self.production_authentication
            or self.header_identity_used
            or self.cookie_identity_used
            or self.token_identity_used
            or self.external_identity_provider_used
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("request identity binding cannot trust external identity material")
        return self


class SecureActorContextBinding(SecureRuntimeFingerprintedModel):
    """Verified local operator ActorContext binding."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = SECURE_ACTOR_CONTEXT_BINDING_SCHEMA_VERSION
    binding_id: str
    session_id: str
    request_id: str
    request_identity_binding_fingerprint: str
    actor_context: ActorContext
    actor_context_fingerprint: str
    permission_count: int = Field(ge=0, le=128)
    role_count: int = Field(ge=0, le=64)
    security_scope_count: int = Field(ge=0, le=128)
    local_operator_context: bool = True
    anonymous_context: bool = False
    development_simulation: bool = False
    production_actor_context: bool = False
    created_at: datetime
    binding_fingerprint: str | None = None
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "request_id")
    @classmethod
    def actor_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("request_identity_binding_fingerprint", "actor_context_fingerprint")
    @classmethod
    def actor_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def actor_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def actor_context_must_be_verified_local_operator(self) -> Self:
        if self.actor_context.actor_type != "local_operator":
            raise ValueError("ActorContext must represent a local operator")
        if not self.actor_context.actor_id or not self.actor_context.workspace_id:
            raise ValueError("ActorContext cannot be anonymous")
        if self.actor_context.dev_mode:
            raise ValueError("development simulation is not allowed")
        if self.actor_context_fingerprint != secure_runtime_fingerprint(
            self.actor_context.model_dump(mode="json")
        ):
            raise ValueError("ActorContext fingerprint mismatch")
        if (
            self.permission_count != len(self.actor_context.permissions)
            or self.role_count != len(self.actor_context.roles)
            or self.security_scope_count != len(self.actor_context.security_scope)
        ):
            raise ValueError("ActorContext counts mismatch")
        if (
            not self.local_operator_context
            or self.anonymous_context
            or self.development_simulation
            or self.production_actor_context
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("ActorContext binding must remain local, redacted, and non-production")
        return self


class SecureSideEffectBudget(SecureRuntimeFingerprintedModel):
    """AION-230-SRI-0001 resource and zero-effect budget."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    schema_version: str = SECURE_SIDE_EFFECT_BUDGET_SCHEMA_VERSION
    maximum_local_operator_sessions: int = 1
    maximum_session_seconds: int = 3600
    maximum_requests_per_session: int = 100
    maximum_concurrent_requests: int = 4
    maximum_capability_plans_per_request: int = 10
    maximum_capability_invocations_per_session: int = 100
    maximum_policy_decisions_per_request: int = 20
    maximum_risk_assessments_per_request: int = 20
    maximum_guardrail_decisions_per_request: int = 20
    maximum_approval_evidence_records_per_request: int = 4
    maximum_stage_receipts_per_session: int = 1000
    maximum_audit_records_per_session: int = 10000
    maximum_telemetry_events_per_session: int = 10000
    maximum_operator_review_items_per_session: int = 500
    maximum_trace_bytes_per_session: int = 4194304
    maximum_response_bytes_per_request: int = 1048576
    maximum_fixture_records: int = 5000
    maximum_fixture_bytes: int = 4194304
    maximum_session_checkpoints: int = 20
    maximum_replay_validations_per_request: int = 10
    maximum_kill_switch_checks_per_request: int = 10
    maximum_public_network_calls: int = 0
    maximum_model_provider_calls: int = 0
    maximum_connector_calls: int = 0
    maximum_actual_tool_executions: int = 0
    maximum_shell_commands: int = 0
    maximum_subprocess_executions: int = 0
    maximum_browser_actions: int = 0
    maximum_credentials_persisted: int = 0
    maximum_tokens_persisted: int = 0
    maximum_session_tokens_issued: int = 0
    maximum_external_identity_provider_calls: int = 0
    maximum_modules_activated: int = 0
    maximum_packages_installed: int = 0
    maximum_dynamic_routes_registered: int = 0
    maximum_automatic_approvals: int = 0
    maximum_runtime_created_approvals: int = 0
    maximum_production_writes: int = 0
    maximum_production_memory_writes: int = 0
    maximum_production_policy_mutations: int = 0
    maximum_cognitive_memory_writes: int = 0
    maximum_actual_belief_creations: int = 0
    maximum_actual_belief_mutations: int = 0
    maximum_glm_live_executions: int = 0
    maximum_source_mutations: int = 0
    maximum_git_operations: int = 0
    maximum_runtime_created_pull_requests: int = 0
    maximum_automatic_merges: int = 0
    maximum_production_canary_executions: int = 0
    maximum_deployments: int = 0
    maximum_model_weight_changes: int = 0
    budget_fingerprint: str | None = None


class SecureSideEffectUsage(SecureRuntimeFingerprintedModel):
    """Observed local usage counters for one session/request."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "usage_fingerprint"

    schema_version: str = SECURE_SIDE_EFFECT_BUDGET_SCHEMA_VERSION
    local_operator_sessions: int = Field(default=1, ge=0)
    session_seconds: int = Field(default=0, ge=0)
    requests: int = Field(default=0, ge=0)
    concurrent_requests: int = Field(default=0, ge=0)
    capability_plans_per_request: int = Field(default=0, ge=0)
    capability_invocations_per_session: int = Field(default=0, ge=0)
    policy_decisions_per_request: int = Field(default=0, ge=0)
    risk_assessments_per_request: int = Field(default=0, ge=0)
    guardrail_decisions_per_request: int = Field(default=0, ge=0)
    approval_evidence_records_per_request: int = Field(default=0, ge=0)
    stage_receipts_per_session: int = Field(default=0, ge=0)
    audit_records_per_session: int = Field(default=0, ge=0)
    telemetry_events_per_session: int = Field(default=0, ge=0)
    operator_review_items_per_session: int = Field(default=0, ge=0)
    trace_bytes_per_session: int = Field(default=0, ge=0)
    response_bytes_per_request: int = Field(default=0, ge=0)
    fixture_records: int = Field(default=0, ge=0)
    fixture_bytes: int = Field(default=0, ge=0)
    session_checkpoints: int = Field(default=0, ge=0)
    replay_validations_per_request: int = Field(default=0, ge=0)
    kill_switch_checks_per_request: int = Field(default=0, ge=0)
    public_network_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    actual_tool_executions: int = Field(default=0, ge=0)
    shell_commands: int = Field(default=0, ge=0)
    subprocess_executions: int = Field(default=0, ge=0)
    browser_actions: int = Field(default=0, ge=0)
    credentials_persisted: int = Field(default=0, ge=0)
    tokens_persisted: int = Field(default=0, ge=0)
    session_tokens_issued: int = Field(default=0, ge=0)
    external_identity_provider_calls: int = Field(default=0, ge=0)
    modules_activated: int = Field(default=0, ge=0)
    packages_installed: int = Field(default=0, ge=0)
    dynamic_routes_registered: int = Field(default=0, ge=0)
    automatic_approvals: int = Field(default=0, ge=0)
    runtime_created_approvals: int = Field(default=0, ge=0)
    production_writes: int = Field(default=0, ge=0)
    production_memory_writes: int = Field(default=0, ge=0)
    production_policy_mutations: int = Field(default=0, ge=0)
    cognitive_memory_writes: int = Field(default=0, ge=0)
    actual_belief_creations: int = Field(default=0, ge=0)
    actual_belief_mutations: int = Field(default=0, ge=0)
    glm_live_executions: int = Field(default=0, ge=0)
    source_mutations: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    runtime_created_pull_requests: int = Field(default=0, ge=0)
    automatic_merges: int = Field(default=0, ge=0)
    production_canary_executions: int = Field(default=0, ge=0)
    deployments: int = Field(default=0, ge=0)
    model_weight_changes: int = Field(default=0, ge=0)
    usage_fingerprint: str | None = None

    def prohibited_effects_zero(self) -> bool:
        """Return whether every prohibited-effect counter is zero."""

        return all(
            getattr(self, field_name) == 0 for field_name in PROHIBITED_EFFECT_COUNTER_FIELDS
        )


class SecureSideEffectBudgetDecision(SecureRuntimeFingerprintedModel):
    """Budget enforcement result."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "decision_fingerprint"

    schema_version: str = SECURE_SIDE_EFFECT_BUDGET_SCHEMA_VERSION
    budget_fingerprint: str
    usage_fingerprint: str
    allowed: bool
    reason_codes: tuple[str, ...]
    created_at: datetime
    decision_fingerprint: str | None = None
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("budget_fingerprint", "usage_fingerprint")
    @classmethod
    def budget_decision_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def budget_decision_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


PROHIBITED_EFFECT_COUNTER_FIELDS: tuple[str, ...] = (
    "public_network_calls",
    "model_provider_calls",
    "connector_calls",
    "actual_tool_executions",
    "shell_commands",
    "subprocess_executions",
    "browser_actions",
    "credentials_persisted",
    "tokens_persisted",
    "session_tokens_issued",
    "external_identity_provider_calls",
    "modules_activated",
    "packages_installed",
    "dynamic_routes_registered",
    "automatic_approvals",
    "runtime_created_approvals",
    "production_writes",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "actual_belief_creations",
    "actual_belief_mutations",
    "glm_live_executions",
    "source_mutations",
    "git_operations",
    "runtime_created_pull_requests",
    "automatic_merges",
    "production_canary_executions",
    "deployments",
    "model_weight_changes",
)


class SecureRuntimeKillSwitchState(SecureRuntimeFingerprintedModel):
    """Immutable explicit operator kill-switch state."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "state_fingerprint"

    schema_version: str = SECURE_RUNTIME_KILL_SWITCH_SCHEMA_VERSION
    session_id: str
    status: SecureRuntimeKillSwitchStatus
    reason_code: str
    activation_fingerprint: str
    operator_identity_fingerprint: str
    created_at: datetime
    state_fingerprint: str | None = None
    network_kill_switch: bool = False
    global_process_singleton: bool = False
    os_signal_execution: bool = False

    @field_validator("session_id")
    @classmethod
    def kill_switch_session_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("activation_fingerprint", "operator_identity_fingerprint")
    @classmethod
    def kill_switch_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def kill_switch_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeKillSwitch:
    """Session-scoped kill-switch evaluator."""

    def __init__(self, state: SecureRuntimeKillSwitchState) -> None:
        self._state = state

    @property
    def state(self) -> SecureRuntimeKillSwitchState:
        return self._state

    def check(self) -> SecureRuntimeKillSwitchState:
        return self._state

    def activate(
        self,
        *,
        reason_code: str,
        operator_identity_fingerprint: str,
        created_at: datetime | None = None,
    ) -> SecureRuntimeKillSwitchState:
        if self._state.status == SecureRuntimeKillSwitchStatus.active:
            return self._state
        self._state = SecureRuntimeKillSwitchState(
            session_id=self._state.session_id,
            status=SecureRuntimeKillSwitchStatus.active,
            reason_code=reason_code,
            activation_fingerprint=secure_runtime_fingerprint(
                {
                    "session_id": self._state.session_id,
                    "reason_code": reason_code,
                    "prior": self._state.state_fingerprint,
                }
            ),
            operator_identity_fingerprint=operator_identity_fingerprint,
            created_at=created_at or utc_now(),
        )
        return self._state


class SecureRuntimeSessionPlan(SecureRuntimeFingerprintedModel):
    """One explicit bounded local operator session plan."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: str = SECURE_RUNTIME_SESSION_SCHEMA_VERSION
    session_plan_id: str
    authorization_envelope: SecureRuntimeAuthorizationEnvelope
    operator_identity_binding_fingerprint: str
    request_identity_binding_fingerprint: str
    actor_context_binding_fingerprint: str
    allowed_capability_codes: tuple[str, ...]
    side_effect_budget: SecureSideEffectBudget
    initial_kill_switch_fingerprint: str
    maximum_requests: int = Field(ge=1, le=MAXIMUM_REQUESTS_PER_SESSION)
    maximum_concurrent_requests: int = Field(ge=1, le=MAXIMUM_CONCURRENT_REQUESTS)
    created_at: datetime
    expires_at: datetime
    operator_invoked: bool = True
    automatic_continuation: bool = False
    background_execution: bool = False
    scheduled_execution: bool = False
    production_runtime: bool = False
    plan_fingerprint: str | None = None

    @field_validator("session_plan_id")
    @classmethod
    def session_plan_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "operator_identity_binding_fingerprint",
        "request_identity_binding_fingerprint",
        "actor_context_binding_fingerprint",
        "initial_kill_switch_fingerprint",
    )
    @classmethod
    def session_plan_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("allowed_capability_codes", mode="before")
    @classmethod
    def session_capabilities_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("allowed capabilities must be a collection")
        return ensure_sorted_unique(value or (), field_name="allowed capability codes")

    @field_validator("created_at", "expires_at")
    @classmethod
    def session_plan_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def session_plan_must_match_authorization(self) -> Self:
        if self.expires_at > self.authorization_envelope.expires_at:
            raise ValueError("session plan cannot outlive authorization")
        if self.expires_at <= self.created_at:
            raise ValueError("session plan expires before creation")
        if tuple(self.authorization_envelope.allowed_capability_codes) != tuple(
            self.allowed_capability_codes
        ):
            raise ValueError("session plan capability allowlist mismatch")
        if (
            not self.operator_invoked
            or self.automatic_continuation
            or self.background_execution
            or self.scheduled_execution
            or self.production_runtime
        ):
            raise ValueError("session plan cannot authorize automated or production runtime")
        return self


class SecureRuntimeSession(SecureRuntimeFingerprintedModel):
    """Immutable repository snapshot for one local operator session."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "session_fingerprint"

    schema_version: str = SECURE_RUNTIME_SESSION_SCHEMA_VERSION
    session_id: str
    session_plan: SecureRuntimeSessionPlan
    current_state: SecureRuntimeSessionState = SecureRuntimeSessionState.drafted
    active_request_ids: tuple[str, ...] = Field(default_factory=tuple)
    completed_request_ids: tuple[str, ...] = Field(default_factory=tuple)
    latest_receipt_fingerprint: str = ZERO_FINGERPRINT
    receipt_sequence: int = 0
    created_at: datetime
    expires_at: datetime
    closed_at: datetime | None = None
    killed_at: datetime | None = None
    production_effect: bool = False
    runtime_effect: bool = False
    session_fingerprint: str | None = None

    @field_validator("session_id")
    @classmethod
    def session_identifier_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("active_request_ids", "completed_request_ids")
    @classmethod
    def request_ids_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(ensure_safe_identifier(item) for item in value))

    @field_validator("latest_receipt_fingerprint")
    @classmethod
    def latest_receipt_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at", "closed_at", "killed_at")
    @classmethod
    def session_timestamps_must_be_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_utc(value)


class SecureRuntimeStageCommand(SecureRuntimeFingerprintedModel):
    """Explicit operator command for one state transition."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "command_fingerprint"

    schema_version: str = SECURE_RUNTIME_STAGE_COMMAND_SCHEMA_VERSION
    command_id: str
    session_id: str
    request_id: str | None = None
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    expected_current_state: SecureRuntimeSessionState
    requested_next_state: SecureRuntimeSessionState
    session_plan_fingerprint: str
    input_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    operator_identity_fingerprint: str
    created_at: datetime
    expires_at: datetime
    operator_invoked: bool = True
    automatic_transition: bool = False
    command_fingerprint: str | None = None

    @field_validator("command_id", "session_id", "request_id")
    @classmethod
    def command_identifiers_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_safe_identifier(value)

    @field_validator(
        "session_plan_fingerprint",
        "operator_identity_fingerprint",
    )
    @classmethod
    def command_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("input_fingerprints")
    @classmethod
    def command_input_fingerprints_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def command_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def command_must_be_explicit(self) -> Self:
        if self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("authorization mismatch")
        if self.expires_at <= self.created_at:
            raise ValueError("command expires before creation")
        if not self.operator_invoked or self.automatic_transition:
            raise ValueError("state transition command must be explicit operator invocation")
        return self


class SecureRuntimeStageReceipt(SecureRuntimeFingerprintedModel):
    """Immutable receipt for one state transition."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "receipt_fingerprint"

    schema_version: str = SECURE_RUNTIME_STAGE_RECEIPT_SCHEMA_VERSION
    receipt_id: str
    session_id: str
    request_id: str | None = None
    sequence_number: int = Field(ge=1)
    prior_receipt_fingerprint: str
    state_before: SecureRuntimeSessionState
    state_after: SecureRuntimeSessionState
    disposition: SecureRuntimeStageDisposition
    command_fingerprint: str
    input_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    output_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    decision_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    bounded_counts: dict[str, int] = Field(default_factory=dict)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime
    receipt_fingerprint: str | None = None
    operator_invoked: bool = True
    background_execution: bool = False
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("receipt_id", "session_id", "request_id")
    @classmethod
    def receipt_identifiers_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_safe_identifier(value)

    @field_validator("prior_receipt_fingerprint", "command_fingerprint")
    @classmethod
    def receipt_required_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("input_fingerprints", "output_fingerprints", "decision_fingerprints")
    @classmethod
    def receipt_fingerprint_sets_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in value)

    @field_validator("created_at")
    @classmethod
    def receipt_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("bounded_counts")
    @classmethod
    def receipt_bounded_counts_must_be_safe(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 for count in value.values()):
            raise ValueError("bounded counts cannot be negative")
        return dict(sorted(value.items()))

    @model_validator(mode="after")
    def receipt_must_be_non_effect(self) -> Self:
        if not self.operator_invoked or self.background_execution:
            raise ValueError("receipt must come from explicit local operator flow")
        if self.production_effect or self.runtime_effect:
            raise ValueError("stage receipt cannot record production or runtime effects")
        return self


class SecureRuntimeRequestEnvelope(SecureRuntimeFingerprintedModel):
    """Redacted runtime request envelope with payload represented by fingerprint only."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "request_fingerprint"

    schema_version: str = SECURE_RUNTIME_REQUEST_SCHEMA_VERSION
    request_envelope_id: str
    session_id: str
    request_id: str
    trace_id: str
    correlation_id: str
    actor_context_binding_fingerprint: str
    capability_code: str
    action_type: str
    resource_type: str
    resource_id: str
    requested_permissions: tuple[str, ...]
    requested_security_scopes: tuple[str, ...]
    safe_payload_fingerprint: str
    metadata_fingerprint: str
    created_at: datetime
    expires_at: datetime
    request_body_retained: bool = False
    credential_present: bool = False
    token_present: bool = False
    network_target_present: bool = False
    executable_present: bool = False
    production_target_present: bool = False
    request_fingerprint: str | None = None

    @field_validator(
        "request_envelope_id", "session_id", "request_id", "trace_id", "correlation_id"
    )
    @classmethod
    def request_envelope_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "actor_context_binding_fingerprint",
        "safe_payload_fingerprint",
        "metadata_fingerprint",
    )
    @classmethod
    def request_envelope_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("requested_permissions", "requested_security_scopes", mode="before")
    @classmethod
    def request_envelope_sets_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("request envelope sets must be collections")
        return ensure_sorted_unique(value or (), field_name="request envelope set")

    @field_validator("created_at", "expires_at")
    @classmethod
    def request_envelope_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def request_envelope_must_be_safe(self) -> Self:
        manifest = capability_manifest_for(self.capability_code)
        if self.action_type != manifest.action_type or self.resource_type != manifest.resource_type:
            raise ValueError("capability target substitution detected")
        if (
            self.request_body_retained
            or self.credential_present
            or self.token_present
            or self.network_target_present
            or self.executable_present
            or self.production_target_present
        ):
            raise ValueError("runtime request cannot retain or target protected effects")
        return self


class SecureCapabilityInvocationPlan(SecureRuntimeFingerprintedModel):
    """Deterministic invocation plan for a closed simulation-only capability."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: str = SECURE_CAPABILITY_PLAN_SCHEMA_VERSION
    plan_id: str
    session_id: str
    request_id: str
    trace_id: str
    request_fingerprint: str
    capability_code: str
    action_type: str
    resource_type: str
    resource_id: str
    required_permissions: tuple[str, ...]
    required_security_scopes: tuple[str, ...]
    risk_class: SecureRuntimeCapabilityRisk
    approval_required: bool
    simulation_only: bool = True
    actual_execution_available: bool = False
    expected_policy_binding: str
    expected_risk_binding: str
    expected_guardrail_binding: str
    expected_approval_binding: str
    side_effect_budget_fingerprint: str
    created_at: datetime
    expires_at: datetime
    plan_fingerprint: str | None = None
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("plan_id", "session_id", "request_id", "trace_id")
    @classmethod
    def plan_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "request_fingerprint",
        "side_effect_budget_fingerprint",
        "expected_policy_binding",
        "expected_risk_binding",
        "expected_guardrail_binding",
        "expected_approval_binding",
    )
    @classmethod
    def plan_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("required_permissions", "required_security_scopes", mode="before")
    @classmethod
    def plan_sets_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("plan sets must be collections")
        return ensure_sorted_unique(value or (), field_name="plan set")

    @field_validator("created_at", "expires_at")
    @classmethod
    def plan_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def plan_must_match_closed_manifest(self) -> Self:
        manifest = capability_manifest_for(self.capability_code)
        if (
            self.action_type != manifest.action_type
            or self.resource_type != manifest.resource_type
            or self.required_permissions != manifest.required_permissions
            or self.required_security_scopes != manifest.required_security_scopes
            or self.risk_class != manifest.risk
            or self.approval_required != manifest.approval_required
        ):
            raise ValueError("capability plan does not match closed manifest")
        if (
            not self.simulation_only
            or self.actual_execution_available
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("capability plan must remain simulation-only")
        return self


class _DecisionBindingBase(SecureRuntimeFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = SECURE_DECISION_BINDING_SCHEMA_VERSION
    binding_id: str
    session_id: str
    request_id: str
    capability_plan_fingerprint: str
    source_decision_fingerprint: str
    action_type: str
    resource_type: str
    resource_id: str
    trace_id: str
    decision_outcome: str
    approval_required: bool
    constraints: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime
    binding_fingerprint: str | None = None
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "request_id", "trace_id")
    @classmethod
    def decision_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("capability_plan_fingerprint", "source_decision_fingerprint")
    @classmethod
    def decision_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def decision_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def decision_binding_must_be_read_only(self) -> Self:
        if not self.read_only or not self.redacted or self.runtime_effect:
            raise ValueError("decision binding must remain read-only and redacted")
        return self


class SecurePolicyBinding(_DecisionBindingBase):
    """Read-only binding to an externally supplied PolicyDecision."""


class SecureRiskBinding(_DecisionBindingBase):
    """Read-only binding to an externally supplied RiskAssessment."""

    requested_risk: SecureRuntimeCapabilityRisk
    computed_risk: SecureRuntimeCapabilityRisk

    @model_validator(mode="after")
    def risk_cannot_downgrade_registry(self) -> Self:
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if order[self.computed_risk.value] < order[self.requested_risk.value]:
            raise ValueError("risk binding cannot downgrade registry risk")
        return self


class SecureGuardrailBinding(_DecisionBindingBase):
    """Read-only binding to an externally supplied GuardrailDecision."""

    blocked: bool
    severity: SecureRuntimeCapabilityRisk


class SecureApprovalEvidence(SecureRuntimeFingerprintedModel):
    """One redacted pre-existing approval evidence binding."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "evidence_fingerprint"

    schema_version: str = SECURE_APPROVAL_EVIDENCE_SCHEMA_VERSION
    evidence_id: str
    session_id: str
    request_id: str
    capability_code: str
    approval_request_fingerprint: str
    approval_decision_fingerprint: str
    approval_request_id: str
    approval_decision_id: str
    capability_plan_fingerprint: str
    actor_context_fingerprint: str
    policy_binding_fingerprint: str
    risk_binding_fingerprint: str
    guardrail_binding_fingerprint: str
    side_effect_budget_fingerprint: str
    expires_at: datetime
    created_at: datetime
    approved: bool = True
    requester_differs_from_approver: bool = True
    action_type: str = "secure_runtime.dispatch.simulate"
    resource_type: str = "secure_runtime_capability_plan"
    approval_scope: tuple[str, ...] = ("secure-runtime:simulate-capability",)
    actual_execution_authorized: bool = False
    production_effect_authorized: bool = False
    evidence_fingerprint: str | None = None
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False

    @field_validator(
        "evidence_id", "session_id", "request_id", "approval_request_id", "approval_decision_id"
    )
    @classmethod
    def approval_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "approval_request_fingerprint",
        "approval_decision_fingerprint",
        "capability_plan_fingerprint",
        "actor_context_fingerprint",
        "policy_binding_fingerprint",
        "risk_binding_fingerprint",
        "guardrail_binding_fingerprint",
        "side_effect_budget_fingerprint",
    )
    @classmethod
    def approval_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("expires_at", "created_at")
    @classmethod
    def approval_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def approval_evidence_must_be_preexisting_and_non_effect(self) -> Self:
        if (
            not self.approved
            or not self.requester_differs_from_approver
            or self.actual_execution_authorized
            or self.production_effect_authorized
            or not self.read_only
            or not self.redacted
            or self.runtime_effect
        ):
            raise ValueError("approval evidence cannot authorize execution or production effects")
        if self.action_type != "secure_runtime.dispatch.simulate":
            raise ValueError("approval evidence action mismatch")
        if self.resource_type != "secure_runtime_capability_plan":
            raise ValueError("approval evidence resource mismatch")
        if self.approval_scope != ("secure-runtime:simulate-capability",):
            raise ValueError("approval scope mismatch")
        return self


class SecureApprovalEvidenceBundle(SecureRuntimeFingerprintedModel):
    """Bounded bundle of pre-existing approval evidence records."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "bundle_fingerprint"

    schema_version: str = SECURE_APPROVAL_EVIDENCE_SCHEMA_VERSION
    bundle_id: str
    session_id: str
    request_id: str
    capability_code: str
    approval_required: bool
    evidence: tuple[SecureApprovalEvidence, ...] = Field(default_factory=tuple)
    created_at: datetime
    bundle_fingerprint: str | None = None
    approvals_created_by_runtime: int = 0
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False

    @field_validator("bundle_id", "session_id", "request_id")
    @classmethod
    def approval_bundle_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("created_at")
    @classmethod
    def approval_bundle_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def approval_bundle_must_match_risk(self) -> Self:
        if len(self.evidence) > MAXIMUM_APPROVAL_EVIDENCE_RECORDS:
            raise ValueError("too many approval evidence records")
        if self.approval_required and not self.evidence:
            raise ValueError("approval evidence required")
        if self.approvals_created_by_runtime != 0 or not self.read_only or not self.redacted:
            raise ValueError("runtime cannot create approval evidence")
        return self


class SecureRuntimeGuardDecision(SecureRuntimeFingerprintedModel):
    """Runtime guard decision, never actual execution permission."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "guard_decision_fingerprint"

    schema_version: str = SECURE_RUNTIME_GUARD_SCHEMA_VERSION
    decision_id: str
    session_id: str
    request_id: str
    outcome: SecureRuntimeGuardOutcome
    reason_codes: tuple[str, ...]
    required_approval: bool
    approval_present: bool
    kill_switch_status: SecureRuntimeKillSwitchStatus
    side_effect_budget_decision_fingerprint: str
    capability_plan_fingerprint: str
    policy_binding_fingerprint: str
    risk_binding_fingerprint: str
    guardrail_binding_fingerprint: str
    approval_bundle_fingerprint: str
    created_at: datetime
    guard_decision_fingerprint: str | None = None
    allow_execution: bool = False
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("decision_id", "session_id", "request_id")
    @classmethod
    def guard_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "side_effect_budget_decision_fingerprint",
        "capability_plan_fingerprint",
        "policy_binding_fingerprint",
        "risk_binding_fingerprint",
        "guardrail_binding_fingerprint",
        "approval_bundle_fingerprint",
    )
    @classmethod
    def guard_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def guard_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def guard_never_allows_execution(self) -> Self:
        if self.allow_execution or self.production_effect or self.runtime_effect:
            raise ValueError("runtime guard cannot allow execution or production effects")
        return self


class SecureSimulatedDispatchResult(SecureRuntimeFingerprintedModel):
    """Deterministic simulation-only dispatch result."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "result_fingerprint"

    schema_version: str = SECURE_SIMULATED_DISPATCH_SCHEMA_VERSION
    dispatch_id: str
    session_id: str
    request_id: str
    capability_code: str
    status: SecureRuntimeDispatchStatus
    deterministic_result_code: str
    guard_decision_fingerprint: str
    capability_plan_fingerprint: str
    result_summary_fingerprint: str
    created_at: datetime
    simulation_only: bool = True
    actual_execution_performed: bool = False
    external_call_performed: bool = False
    provider_call_performed: bool = False
    connector_call_performed: bool = False
    tool_execution_performed: bool = False
    production_write_performed: bool = False
    production_memory_written: bool = False
    production_policy_mutated: bool = False
    cognitive_memory_written: bool = False
    belief_created: bool = False
    belief_mutated: bool = False
    source_mutated: bool = False
    git_mutated: bool = False
    model_weights_changed: bool = False
    production_effect: bool = False
    runtime_effect: bool = False
    result_fingerprint: str | None = None

    @field_validator("dispatch_id", "session_id", "request_id")
    @classmethod
    def dispatch_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "guard_decision_fingerprint",
        "capability_plan_fingerprint",
        "result_summary_fingerprint",
    )
    @classmethod
    def dispatch_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def dispatch_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def dispatch_must_remain_simulation_only(self) -> Self:
        prohibited = (
            self.actual_execution_performed,
            self.external_call_performed,
            self.provider_call_performed,
            self.connector_call_performed,
            self.tool_execution_performed,
            self.production_write_performed,
            self.production_memory_written,
            self.production_policy_mutated,
            self.cognitive_memory_written,
            self.belief_created,
            self.belief_mutated,
            self.source_mutated,
            self.git_mutated,
            self.model_weights_changed,
            self.production_effect,
            self.runtime_effect,
        )
        if not self.simulation_only or any(prohibited):
            raise ValueError("dispatch result must remain simulation-only")
        return self


class SecureRuntimeAuditRecord(SecureRuntimeFingerprintedModel):
    """Append-only in-memory audit hash-chain record."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "audit_hash"

    schema_version: str = SECURE_RUNTIME_AUDIT_SCHEMA_VERSION
    audit_record_id: str
    session_id: str
    request_id: str | None = None
    trace_id: str | None = None
    event_type: str
    subject_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    decision_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    prior_audit_hash: str
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    audit_hash: str | None = None
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("audit_record_id", "session_id", "request_id", "trace_id")
    @classmethod
    def audit_identifiers_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_safe_identifier(value)

    @field_validator("subject_fingerprints", "decision_fingerprints")
    @classmethod
    def audit_fingerprint_sets_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in value)

    @field_validator("prior_audit_hash")
    @classmethod
    def prior_audit_hash_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("metadata")
    @classmethod
    def audit_metadata_must_be_redacted(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secure_runtime_protected_material(value)
        return dict(sorted(value.items()))

    @field_validator("created_at")
    @classmethod
    def audit_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeObservabilitySnapshot(SecureRuntimeFingerprintedModel):
    """Redacted local observability snapshot with no external exporter."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "snapshot_fingerprint"

    schema_version: str = SECURE_RUNTIME_OBSERVABILITY_SCHEMA_VERSION
    snapshot_id: str
    session_id: str
    session_state: SecureRuntimeSessionState
    request_counts: dict[str, int]
    active_request_count: int = Field(ge=0)
    completed_request_count: int = Field(ge=0)
    blocked_request_count: int = Field(ge=0)
    replay_rejection_count: int = Field(ge=0)
    stage_receipt_count: int = Field(ge=0)
    audit_record_count: int = Field(ge=0)
    policy_decision_count: int = Field(ge=0)
    risk_decision_count: int = Field(ge=0)
    guardrail_decision_count: int = Field(ge=0)
    approval_validation_count: int = Field(ge=0)
    kill_switch_check_count: int = Field(ge=0)
    simulated_dispatch_count: int = Field(ge=0)
    budget_usage: SecureSideEffectUsage
    integrity_status: SecureRuntimeIntegrityStatus
    created_at: datetime
    snapshot_fingerprint: str | None = None
    external_telemetry_exporter: bool = False
    network_export: bool = False
    log_shipping: bool = False
    production_health_endpoint: bool = False
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("snapshot_id", "session_id")
    @classmethod
    def observability_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("created_at")
    @classmethod
    def observability_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeHealthSnapshot(SecureRuntimeFingerprintedModel):
    """Local readiness and health state."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "health_fingerprint"

    schema_version: str = SECURE_RUNTIME_HEALTH_SCHEMA_VERSION
    health_id: str
    session_id: str
    state: Literal[
        "ready_local_simulation",
        "session_active",
        "blocked",
        "killed",
        "expired",
        "closed",
        "integrity_failed",
    ]
    authorization_exact: bool = True
    identity_pipeline_available: bool = True
    public_key_registry_available: bool = True
    replay_repository_schema_available: bool = True
    kill_switch_clear: bool = True
    resource_budgets_valid: bool = True
    production_runtime: bool = False
    providers: bool = False
    connectors: bool = False
    tools: bool = False
    modules: bool = False
    created_at: datetime
    health_fingerprint: str | None = None
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("health_id", "session_id")
    @classmethod
    def health_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("created_at")
    @classmethod
    def health_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def readiness_must_be_local_only(self) -> Self:
        if (
            not self.authorization_exact
            or not self.identity_pipeline_available
            or not self.public_key_registry_available
            or not self.replay_repository_schema_available
            or not self.resource_budgets_valid
            or self.production_runtime
            or self.providers
            or self.connectors
            or self.tools
            or self.modules
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("health readiness must remain local and non-production")
        return self


class SecureRuntimeSessionCheckpoint(SecureRuntimeFingerprintedModel):
    """Explicit temporary in-memory session checkpoint."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "checkpoint_fingerprint"

    schema_version: str = SECURE_RUNTIME_CHECKPOINT_SCHEMA_VERSION
    checkpoint_id: str
    session_id: str
    current_state: SecureRuntimeSessionState
    latest_stage_receipt_fingerprint: str
    stage_receipt_chain_head: str
    audit_chain_head: str
    session_plan_fingerprint: str
    actor_context_binding_fingerprint: str
    active_request_ids: tuple[str, ...]
    completed_request_ids: tuple[str, ...]
    kill_switch_fingerprint: str
    budget_usage_fingerprint: str
    created_at: datetime
    expires_at: datetime
    checkpoint_fingerprint: str | None = None
    temporary: bool = True
    persistent_session: bool = False
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("checkpoint_id", "session_id")
    @classmethod
    def checkpoint_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "latest_stage_receipt_fingerprint",
        "stage_receipt_chain_head",
        "audit_chain_head",
        "session_plan_fingerprint",
        "actor_context_binding_fingerprint",
        "kill_switch_fingerprint",
        "budget_usage_fingerprint",
    )
    @classmethod
    def checkpoint_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("active_request_ids", "completed_request_ids")
    @classmethod
    def checkpoint_request_ids_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(ensure_safe_identifier(item) for item in value))

    @field_validator("created_at", "expires_at")
    @classmethod
    def checkpoint_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeIntegrityFinding(SecureRuntimeFingerprintedModel):
    """One redacted integrity finding."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "finding_fingerprint"

    schema_version: str = SECURE_RUNTIME_INTEGRITY_SCHEMA_VERSION
    finding_id: str
    category: str
    status: SecureRuntimeIntegrityStatus
    reason_code: str
    evidence_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime
    finding_fingerprint: str | None = None
    redacted: bool = True

    @field_validator("finding_id", "category", "reason_code")
    @classmethod
    def finding_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("evidence_fingerprints")
    @classmethod
    def finding_fingerprints_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in value)

    @field_validator("created_at")
    @classmethod
    def finding_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeIntegrityReport(SecureRuntimeFingerprintedModel):
    """Integrity report over receipts, audit, checkpoints, and no-effect boundaries."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "report_fingerprint"

    schema_version: str = SECURE_RUNTIME_INTEGRITY_SCHEMA_VERSION
    report_id: str
    session_id: str
    status: SecureRuntimeIntegrityStatus
    findings: tuple[SecureRuntimeIntegrityFinding, ...]
    checked_categories: tuple[str, ...]
    created_at: datetime
    report_fingerprint: str | None = None
    no_credentials: bool = True
    no_tokens: bool = True
    no_network: bool = True
    no_providers: bool = True
    no_connectors: bool = True
    no_tools: bool = True
    no_modules: bool = True
    no_production_writes: bool = True
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("report_id", "session_id")
    @classmethod
    def integrity_report_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("checked_categories", mode="before")
    @classmethod
    def integrity_categories_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("checked categories must be a collection")
        return ensure_sorted_unique(value or (), field_name="checked categories")

    @field_validator("created_at")
    @classmethod
    def integrity_report_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def integrity_report_must_preserve_boundaries(self) -> Self:
        if (
            not self.no_credentials
            or not self.no_tokens
            or not self.no_network
            or not self.no_providers
            or not self.no_connectors
            or not self.no_tools
            or not self.no_modules
            or not self.no_production_writes
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("integrity report cannot record enabled runtime effects")
        return self


class SecureRuntimeEvidenceBundle(SecureRuntimeFingerprintedModel):
    """Redacted delivery evidence bundle."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "bundle_fingerprint"

    schema_version: str = SECURE_RUNTIME_EVIDENCE_SCHEMA_VERSION
    bundle_id: str
    session_id: str
    evidence_fingerprints: tuple[str, ...]
    integrity_report_fingerprint: str
    created_at: datetime
    bundle_fingerprint: str | None = None
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("bundle_id", "session_id")
    @classmethod
    def evidence_bundle_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("evidence_fingerprints")
    @classmethod
    def evidence_fingerprints_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in value)

    @field_validator("integrity_report_fingerprint")
    @classmethod
    def integrity_report_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def evidence_bundle_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeDiagnostics(SecureRuntimeFingerprintedModel):
    """Redacted local diagnostics record."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "diagnostic_fingerprint"

    schema_version: str = SECURE_RUNTIME_EVIDENCE_SCHEMA_VERSION
    diagnostic_id: str
    session_id: str
    status: str
    safe_counts: dict[str, int]
    created_at: datetime
    diagnostic_fingerprint: str | None = None
    redacted: bool = True

    @field_validator("diagnostic_id", "session_id", "status")
    @classmethod
    def diagnostics_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("safe_counts")
    @classmethod
    def diagnostics_counts_must_be_safe(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 for count in value.values()):
            raise ValueError("diagnostic counts cannot be negative")
        return dict(sorted(value.items()))

    @field_validator("created_at")
    @classmethod
    def diagnostics_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeIncident(SecureRuntimeFingerprintedModel):
    """Redacted local incident record."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "incident_fingerprint"

    schema_version: str = SECURE_RUNTIME_EVIDENCE_SCHEMA_VERSION
    incident_id: str
    session_id: str
    reason_code: str
    severity: SecureRuntimeCapabilityRisk
    created_at: datetime
    incident_fingerprint: str | None = None
    redacted: bool = True

    @field_validator("incident_id", "session_id", "reason_code")
    @classmethod
    def incident_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("created_at")
    @classmethod
    def incident_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class SecureRuntimeOperatorReviewItem(SecureRuntimeFingerprintedModel):
    """Explicit operator review marker for AION-231 local runtime."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "review_item_fingerprint"

    schema_version: str = SECURE_RUNTIME_EVIDENCE_SCHEMA_VERSION
    review_item_id: str
    session_id: str
    operator_review_required: bool = True
    local_operator_authentication_is_not_production_authentication: bool = True
    offline_assertion_is_not_a_session_token: bool = True
    approval_is_not_execution: bool = True
    simulated_dispatch_is_not_actual_execution: bool = True
    local_runtime_is_not_production_runtime: bool = True
    provider_calls_authorized: bool = False
    connector_calls_authorized: bool = False
    tool_execution_authorized: bool = False
    module_activation_authorized: bool = False
    production_writes_authorized: bool = False
    production_memory_authorized: bool = False
    production_policy_mutation_authorized: bool = False
    cognitive_memory_write_authorized: bool = False
    belief_mutation_authorized: bool = False
    glm_live_execution_authorized: bool = False
    source_rewrite_authorized: bool = False
    model_training_authorized: bool = False
    deployment_authorized: bool = False
    created_at: datetime
    review_item_fingerprint: str | None = None
    redacted: bool = True

    @field_validator("review_item_id", "session_id")
    @classmethod
    def review_item_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("created_at")
    @classmethod
    def review_item_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def review_item_must_require_operator_review(self) -> Self:
        required_true = (
            self.operator_review_required,
            self.local_operator_authentication_is_not_production_authentication,
            self.offline_assertion_is_not_a_session_token,
            self.approval_is_not_execution,
            self.simulated_dispatch_is_not_actual_execution,
            self.local_runtime_is_not_production_runtime,
            self.redacted,
        )
        required_false = (
            self.provider_calls_authorized,
            self.connector_calls_authorized,
            self.tool_execution_authorized,
            self.module_activation_authorized,
            self.production_writes_authorized,
            self.production_memory_authorized,
            self.production_policy_mutation_authorized,
            self.cognitive_memory_write_authorized,
            self.belief_mutation_authorized,
            self.glm_live_execution_authorized,
            self.source_rewrite_authorized,
            self.model_training_authorized,
            self.deployment_authorized,
        )
        if not all(required_true) or any(required_false):
            raise ValueError("operator review item must preserve no-runtime boundaries")
        return self


class SecureRuntimeSessionResult(SecureRuntimeFingerprintedModel):
    """Redacted final result for one closed local operator session."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "result_fingerprint"

    schema_version: str = SECURE_RUNTIME_EVIDENCE_SCHEMA_VERSION
    result_id: str
    session_id: str
    final_state: SecureRuntimeSessionState
    session_plan_fingerprint: str
    response_fingerprint: str
    stage_receipt_chain_head: str
    audit_chain_head: str
    checkpoint_fingerprint: str
    active_request_count: int = Field(ge=0)
    completed_request_count: int = Field(ge=0)
    simulated_dispatch_count: int = Field(ge=0)
    closed_at: datetime
    result_fingerprint: str | None = None
    redacted: bool = True
    actual_execution_performed: bool = False
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("result_id", "session_id")
    @classmethod
    def session_result_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "session_plan_fingerprint",
        "response_fingerprint",
        "stage_receipt_chain_head",
        "audit_chain_head",
        "checkpoint_fingerprint",
    )
    @classmethod
    def session_result_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("closed_at")
    @classmethod
    def session_result_closed_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def session_result_must_be_closed_and_non_effect(self) -> Self:
        if self.final_state != SecureRuntimeSessionState.session_closed:
            raise ValueError("session result requires a closed session")
        if (
            self.active_request_count != 0
            or not self.redacted
            or self.actual_execution_performed
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("session result must remain redacted and side-effect-free")
        return self


def build_component_invocation_binding(
    *,
    component_name: str,
    component_implementation_task: str,
    component_contract_authorization_id: str,
    session_id: str,
    request_id: str | None,
    input_fingerprints: Iterable[str],
    output_fingerprints: Iterable[str],
    invoked_at: datetime,
) -> SecureRuntimeComponentInvocationBinding:
    return SecureRuntimeComponentInvocationBinding(
        binding_id=f"component-{component_name}-{session_id}",
        component_name=component_name,
        component_implementation_task=component_implementation_task,
        component_contract_authorization_id=component_contract_authorization_id,
        session_id=session_id,
        request_id=request_id,
        input_fingerprints=tuple(input_fingerprints),
        output_fingerprints=tuple(output_fingerprints),
        invoked_at=invoked_at,
    )


def bind_verified_local_operator_identity(
    *,
    authorization_envelope: SecureRuntimeAuthorizationEnvelope,
    assertion_envelope: IdentityAssertionEnvelope,
    verification_pipeline: Any,
) -> SecureOperatorIdentityBinding:
    """Verify exactly once and bind one offline assertion to a local operator session."""

    expected_assertion = assertion_fingerprint(assertion_envelope.payload)
    if expected_assertion != authorization_envelope.assertion_fingerprint:
        raise ValueError("assertion fingerprint mismatch")
    verify_once = getattr(verification_pipeline, "verify_once", None)
    if not callable(verify_once):
        raise ValueError("identity verification pipeline unavailable")
    pipeline_bundle = verify_once(assertion_envelope)
    result = pipeline_bundle.result
    if result.outcome != "verified_once":
        raise ValueError("identity assertion was not verified once")
    if not result.cryptographic_verified or not result.verification_and_replay_checks_passed:
        raise ValueError("identity verification and replay checks failed")
    payload = assertion_envelope.payload
    if payload.issuer != authorization_envelope.expected_issuer:
        raise ValueError("issuer mismatch")
    if payload.audience != authorization_envelope.expected_audience:
        raise ValueError("audience mismatch")
    if payload.workspace_id != authorization_envelope.allowed_workspace_id:
        raise ValueError("workspace mismatch")
    operator_identity_fingerprint = text_fingerprint("operator_identity", payload.subject)
    if operator_identity_fingerprint != authorization_envelope.operator_identity_fingerprint:
        raise ValueError("operator identity mismatch")
    if set(payload.roles) - set(authorization_envelope.allowed_roles):
        raise ValueError("role escalation")
    if set(payload.permissions) - set(authorization_envelope.allowed_permissions):
        raise ValueError("permission escalation")
    if set(payload.security_scope) - set(authorization_envelope.allowed_security_scopes):
        raise ValueError("security scope escalation")

    replay_bundle_fingerprint = result.replay_bundle_fingerprint or (
        pipeline_bundle.replay_bundle.fingerprint if pipeline_bundle.replay_bundle else None
    )
    if replay_bundle_fingerprint is None:
        raise ValueError("replay bundle unavailable")
    replay_key = getattr(pipeline_bundle.replay_bundle.result, "replay_key", None)
    if replay_key is None:
        raise ValueError("replay key unavailable")
    created_at = ensure_utc(result.created_at)
    component_bindings = (
        build_component_invocation_binding(
            component_name="offline_ed25519_identity_assertion_verifier",
            component_implementation_task="AION-162",
            component_contract_authorization_id=IDENTITY_COMPONENT_AUTHORIZATION_ID,
            session_id=authorization_envelope.session_id,
            request_id=None,
            input_fingerprints=(authorization_envelope.assertion_fingerprint,),
            output_fingerprints=(result.verification_bundle_fingerprint,),
            invoked_at=created_at,
        ),
        build_component_invocation_binding(
            component_name="identity_assertion_replay_protection",
            component_implementation_task="AION-164",
            component_contract_authorization_id=REPLAY_COMPONENT_AUTHORIZATION_ID,
            session_id=authorization_envelope.session_id,
            request_id=None,
            input_fingerprints=(result.verification_bundle_fingerprint,),
            output_fingerprints=(replay_bundle_fingerprint,),
            invoked_at=created_at,
        ),
    )
    return SecureOperatorIdentityBinding(
        binding_id=f"operator-identity-{authorization_envelope.session_id}",
        session_id=authorization_envelope.session_id,
        assertion_id=payload.assertion_id,
        assertion_fingerprint=authorization_envelope.assertion_fingerprint,
        verification_bundle_fingerprint=result.verification_bundle_fingerprint,
        replay_bundle_fingerprint=replay_bundle_fingerprint,
        replay_key_fingerprint=text_fingerprint("replay_key", replay_key),
        issuer_fingerprint=text_fingerprint("issuer", payload.issuer),
        subject_fingerprint=text_fingerprint("subject", payload.subject),
        operator_identity_fingerprint=operator_identity_fingerprint,
        workspace_fingerprint=text_fingerprint("workspace", payload.workspace_id),
        role_fingerprints=tuple(text_fingerprint("role", role) for role in payload.roles),
        permission_fingerprints=tuple(
            text_fingerprint("permission", permission) for permission in payload.permissions
        ),
        security_scope_fingerprints=tuple(
            text_fingerprint("security_scope", scope) for scope in payload.security_scope
        ),
        component_invocation_bindings=component_bindings,
        created_at=created_at,
        expires_at=authorization_envelope.expires_at,
    )


def bind_secure_request_identity(
    *,
    authorization_envelope: SecureRuntimeAuthorizationEnvelope,
    operator_identity_binding: SecureOperatorIdentityBinding,
    assertion_envelope: IdentityAssertionEnvelope,
    request_id: str,
    trace_id: str,
    correlation_id: str,
    created_at: datetime | None = None,
) -> SecureRequestIdentityBinding:
    """Bind request identity only from the signed assertion payload."""

    payload = assertion_envelope.payload
    if set(payload.roles) - set(authorization_envelope.allowed_roles):
        raise ValueError("role escalation")
    if set(payload.permissions) - set(authorization_envelope.allowed_permissions):
        raise ValueError("permission escalation")
    if set(payload.security_scope) - set(authorization_envelope.allowed_security_scopes):
        raise ValueError("security scope escalation")
    now = created_at or utc_now()
    return SecureRequestIdentityBinding(
        binding_id=f"request-identity-{request_id}",
        session_id=authorization_envelope.session_id,
        request_id=request_id,
        trace_id=trace_id,
        correlation_id=correlation_id,
        operator_identity_fingerprint=operator_identity_binding.operator_identity_fingerprint,
        actor_id=payload.actor_id,
        subject_fingerprint=operator_identity_binding.subject_fingerprint,
        workspace_id=payload.workspace_id or "",
        roles=payload.roles,
        permissions=payload.permissions,
        security_scopes=payload.security_scope,
        assertion_fingerprint=operator_identity_binding.assertion_fingerprint,
        verification_bundle_fingerprint=operator_identity_binding.verification_bundle_fingerprint,
        replay_bundle_fingerprint=operator_identity_binding.replay_bundle_fingerprint,
        created_at=now,
        expires_at=authorization_envelope.expires_at,
    )


def bind_secure_actor_context(
    *,
    request_identity_binding: SecureRequestIdentityBinding,
    allowed_roles: Iterable[str],
    allowed_permissions: Iterable[str],
    allowed_security_scopes: Iterable[str],
    created_at: datetime | None = None,
) -> SecureActorContextBinding:
    """Build a verified local operator ActorContext without using production headers."""

    if set(request_identity_binding.roles) - set(allowed_roles):
        raise ValueError("unknown role")
    if set(request_identity_binding.permissions) - set(allowed_permissions):
        raise ValueError("unknown permission")
    if set(request_identity_binding.security_scopes) - set(allowed_security_scopes):
        raise ValueError("unknown scope")
    actor_context = ActorContext(
        actor_id=request_identity_binding.actor_id,
        actor_type="local_operator",
        workspace_id=request_identity_binding.workspace_id,
        roles=list(request_identity_binding.roles),
        permissions=list(request_identity_binding.permissions),
        security_scope=list(request_identity_binding.security_scopes),
        correlation_id=request_identity_binding.correlation_id,
        trace_id=request_identity_binding.trace_id,
        dev_mode=False,
    )
    return SecureActorContextBinding(
        binding_id=f"actor-context-{request_identity_binding.request_id}",
        session_id=request_identity_binding.session_id,
        request_id=request_identity_binding.request_id,
        request_identity_binding_fingerprint=request_identity_binding.binding_fingerprint or "",
        actor_context=actor_context,
        actor_context_fingerprint=secure_runtime_fingerprint(actor_context.model_dump(mode="json")),
        permission_count=len(actor_context.permissions),
        role_count=len(actor_context.roles),
        security_scope_count=len(actor_context.security_scope),
        created_at=created_at or utc_now(),
    )


def evaluate_side_effect_budget(
    *,
    budget: SecureSideEffectBudget,
    usage: SecureSideEffectUsage,
    created_at: datetime | None = None,
) -> SecureSideEffectBudgetDecision:
    """Fail closed on any budget overflow or prohibited-effect counter."""

    reasons: list[str] = []
    comparisons = {
        "local_operator_sessions": budget.maximum_local_operator_sessions,
        "session_seconds": budget.maximum_session_seconds,
        "requests": budget.maximum_requests_per_session,
        "concurrent_requests": budget.maximum_concurrent_requests,
        "capability_plans_per_request": budget.maximum_capability_plans_per_request,
        "capability_invocations_per_session": (budget.maximum_capability_invocations_per_session),
        "policy_decisions_per_request": budget.maximum_policy_decisions_per_request,
        "risk_assessments_per_request": budget.maximum_risk_assessments_per_request,
        "guardrail_decisions_per_request": budget.maximum_guardrail_decisions_per_request,
        "approval_evidence_records_per_request": (
            budget.maximum_approval_evidence_records_per_request
        ),
        "stage_receipts_per_session": budget.maximum_stage_receipts_per_session,
        "audit_records_per_session": budget.maximum_audit_records_per_session,
        "telemetry_events_per_session": budget.maximum_telemetry_events_per_session,
        "operator_review_items_per_session": (budget.maximum_operator_review_items_per_session),
        "trace_bytes_per_session": budget.maximum_trace_bytes_per_session,
        "response_bytes_per_request": budget.maximum_response_bytes_per_request,
        "fixture_records": budget.maximum_fixture_records,
        "fixture_bytes": budget.maximum_fixture_bytes,
        "session_checkpoints": budget.maximum_session_checkpoints,
        "replay_validations_per_request": budget.maximum_replay_validations_per_request,
        "kill_switch_checks_per_request": budget.maximum_kill_switch_checks_per_request,
    }
    for usage_field, maximum in comparisons.items():
        if getattr(usage, usage_field) > maximum:
            reasons.append(f"budget_overflow:{usage_field}")
    for field_name in PROHIBITED_EFFECT_COUNTER_FIELDS:
        if getattr(usage, field_name) != 0:
            reasons.append(f"prohibited_effect:{field_name}")
    allowed = not reasons
    return SecureSideEffectBudgetDecision(
        budget_fingerprint=budget.budget_fingerprint or "",
        usage_fingerprint=usage.usage_fingerprint or "",
        allowed=allowed,
        reason_codes=tuple(reasons or ["budget_passed"]),
        created_at=created_at or utc_now(),
    )


def create_capability_plan(
    *,
    request: SecureRuntimeRequestEnvelope,
    side_effect_budget: SecureSideEffectBudget,
    created_at: datetime | None = None,
) -> SecureCapabilityInvocationPlan:
    """Create a deterministic capability plan from the closed registry."""

    manifest = capability_manifest_for(request.capability_code)
    now = created_at or utc_now()
    return SecureCapabilityInvocationPlan(
        plan_id=f"capability-plan-{request.request_id}",
        session_id=request.session_id,
        request_id=request.request_id,
        trace_id=request.trace_id,
        request_fingerprint=request.request_fingerprint or "",
        capability_code=manifest.capability_code,
        action_type=manifest.action_type,
        resource_type=manifest.resource_type,
        resource_id=request.resource_id,
        required_permissions=manifest.required_permissions,
        required_security_scopes=manifest.required_security_scopes,
        risk_class=manifest.risk,
        approval_required=manifest.approval_required,
        expected_policy_binding=ZERO_FINGERPRINT,
        expected_risk_binding=ZERO_FINGERPRINT,
        expected_guardrail_binding=ZERO_FINGERPRINT,
        expected_approval_binding=ZERO_FINGERPRINT,
        side_effect_budget_fingerprint=side_effect_budget.budget_fingerprint or "",
        created_at=now,
        expires_at=request.expires_at,
    )


def bind_policy_decision(
    *,
    plan: SecureCapabilityInvocationPlan,
    decision: PolicyDecision,
    created_at: datetime | None = None,
) -> SecurePolicyBinding:
    if decision.trace_id != plan.trace_id:
        raise ValueError("policy trace mismatch")
    if not decision.allow:
        outcome = "deny"
    elif decision.approval_required:
        outcome = "allow_require_approval"
    else:
        outcome = "allow"
    return SecurePolicyBinding(
        binding_id=f"policy-binding-{plan.request_id}",
        session_id=plan.session_id,
        request_id=plan.request_id,
        capability_plan_fingerprint=plan.plan_fingerprint or "",
        source_decision_fingerprint=secure_runtime_fingerprint(decision.model_dump(mode="json")),
        action_type=plan.action_type,
        resource_type=plan.resource_type,
        resource_id=plan.resource_id,
        trace_id=plan.trace_id,
        decision_outcome=outcome,
        approval_required=decision.approval_required,
        constraints=tuple(decision.constraints),
        created_at=created_at or utc_now(),
    )


def bind_risk_assessment(
    *,
    plan: SecureCapabilityInvocationPlan,
    assessment: RiskAssessment,
    created_at: datetime | None = None,
) -> SecureRiskBinding:
    if assessment.action_type != plan.action_type or assessment.resource_type != plan.resource_type:
        raise ValueError("risk target mismatch")
    approval_required = assessment.decision == "require_approval"
    return SecureRiskBinding(
        binding_id=f"risk-binding-{plan.request_id}",
        session_id=plan.session_id,
        request_id=plan.request_id,
        capability_plan_fingerprint=plan.plan_fingerprint or "",
        source_decision_fingerprint=secure_runtime_fingerprint(assessment.model_dump(mode="json")),
        action_type=plan.action_type,
        resource_type=plan.resource_type,
        resource_id=plan.resource_id,
        trace_id=plan.trace_id,
        decision_outcome=assessment.decision,
        approval_required=approval_required,
        constraints=tuple(assessment.constraints),
        requested_risk=plan.risk_class,
        computed_risk=SecureRuntimeCapabilityRisk(assessment.computed_risk_level),
        created_at=created_at or utc_now(),
    )


def bind_guardrail_decision(
    *,
    plan: SecureCapabilityInvocationPlan,
    decision: GuardrailDecision,
    created_at: datetime | None = None,
) -> SecureGuardrailBinding:
    if decision.action_type != plan.action_type or decision.resource_type != plan.resource_type:
        raise ValueError("guardrail target mismatch")
    if decision.blocked:
        outcome = "block"
    elif decision.approval_required:
        outcome = "require_approval"
    else:
        outcome = "allow"
    return SecureGuardrailBinding(
        binding_id=f"guardrail-binding-{plan.request_id}",
        session_id=plan.session_id,
        request_id=plan.request_id,
        capability_plan_fingerprint=plan.plan_fingerprint or "",
        source_decision_fingerprint=secure_runtime_fingerprint(decision.model_dump(mode="json")),
        action_type=plan.action_type,
        resource_type=plan.resource_type,
        resource_id=plan.resource_id or "",
        trace_id=plan.trace_id,
        decision_outcome=outcome,
        approval_required=decision.approval_required,
        constraints=tuple(decision.constraints),
        blocked=decision.blocked,
        severity=SecureRuntimeCapabilityRisk(decision.severity),
        created_at=created_at or utc_now(),
    )


def project_existing_secure_runtime_approval(
    approval_request: ApprovalRequest,
    approval_decision: ApprovalDecision,
    *,
    session_id: str,
    request_id: str,
    capability_code: str,
    capability_plan_fingerprint: str,
    actor_context_fingerprint: str,
    policy_binding_fingerprint: str,
    risk_binding_fingerprint: str,
    guardrail_binding_fingerprint: str,
    side_effect_budget_fingerprint: str,
    now: datetime | None = None,
) -> SecureApprovalEvidence:
    """Project existing approval records without creating or deciding approvals."""

    created_at = now or utc_now()
    if approval_request.status != "approved":
        raise ValueError("approval request is not approved")
    if approval_decision.decision != "approve":
        raise ValueError("approval decision is not approve")
    if approval_decision.approval_request_id != approval_request.approval_request_id:
        raise ValueError("approval request/decision mismatch")
    if (
        approval_request.expires_at is not None
        and ensure_utc(approval_request.expires_at) <= created_at
    ):
        raise ValueError("approval expired")
    if approval_request.requested_by and approval_decision.decided_by:
        if approval_request.requested_by == approval_decision.decided_by:
            raise ValueError("approval requester and approver must differ")
    if approval_request.action_type != "secure_runtime.dispatch.simulate":
        raise ValueError("approval action mismatch")
    if approval_request.resource_type != "secure_runtime_capability_plan":
        raise ValueError("approval resource mismatch")
    if approval_request.resource_id != capability_plan_fingerprint:
        raise ValueError("approval plan mismatch")
    if approval_request.approval_scope != ["secure-runtime:simulate-capability"]:
        raise ValueError("approval scope mismatch")
    return SecureApprovalEvidence(
        evidence_id=f"approval-evidence-{request_id}",
        session_id=session_id,
        request_id=request_id,
        capability_code=capability_code,
        approval_request_fingerprint=secure_runtime_fingerprint(
            approval_request.model_dump(mode="json", exclude={"description", "payload"})
        ),
        approval_decision_fingerprint=secure_runtime_fingerprint(
            approval_decision.model_dump(mode="json", exclude={"reason", "decision_payload"})
        ),
        approval_request_id=approval_request.approval_request_id,
        approval_decision_id=approval_decision.approval_decision_id,
        capability_plan_fingerprint=capability_plan_fingerprint,
        actor_context_fingerprint=actor_context_fingerprint,
        policy_binding_fingerprint=policy_binding_fingerprint,
        risk_binding_fingerprint=risk_binding_fingerprint,
        guardrail_binding_fingerprint=guardrail_binding_fingerprint,
        side_effect_budget_fingerprint=side_effect_budget_fingerprint,
        expires_at=approval_request.expires_at or created_at + timedelta(minutes=5),
        created_at=created_at,
    )


class SecureRuntimeGuardEvaluator:
    """Fail-closed runtime guard for simulation-only dispatch."""

    def evaluate(
        self,
        *,
        authorization_envelope: SecureRuntimeAuthorizationEnvelope,
        operator_identity_binding: SecureOperatorIdentityBinding,
        request_identity_binding: SecureRequestIdentityBinding,
        actor_context_binding: SecureActorContextBinding,
        session: SecureRuntimeSession,
        request: SecureRuntimeRequestEnvelope,
        capability_plan: SecureCapabilityInvocationPlan,
        policy_binding: SecurePolicyBinding,
        risk_binding: SecureRiskBinding,
        guardrail_binding: SecureGuardrailBinding,
        approval_bundle: SecureApprovalEvidenceBundle,
        side_effect_budget_decision: SecureSideEffectBudgetDecision,
        kill_switch_state: SecureRuntimeKillSwitchState,
        created_at: datetime | None = None,
    ) -> SecureRuntimeGuardDecision:
        reasons: list[str] = []
        outcome = SecureRuntimeGuardOutcome.allow_simulation
        required_approval = (
            capability_plan.risk_class == SecureRuntimeCapabilityRisk.medium
            or capability_plan.approval_required
            or policy_binding.approval_required
            or risk_binding.approval_required
            or guardrail_binding.approval_required
        )
        if kill_switch_state.status == SecureRuntimeKillSwitchStatus.active:
            outcome = SecureRuntimeGuardOutcome.kill
            reasons.append("kill_switch_active")
        if authorization_envelope.session_id != session.session_id:
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("authorization_session_mismatch")
        if operator_identity_binding.session_id != session.session_id:
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("operator_identity_session_mismatch")
        if request_identity_binding.binding_fingerprint != (
            actor_context_binding.request_identity_binding_fingerprint
        ):
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("request_identity_actor_context_mismatch")
        if (
            request.session_id != session.session_id
            or request.request_id != capability_plan.request_id
        ):
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("request_session_mismatch")
        if session.expires_at <= (created_at or utc_now()):
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("session_expired")
        if policy_binding.decision_outcome == "deny":
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("policy_denied")
        if risk_binding.decision_outcome == "block":
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("risk_block")
        if guardrail_binding.blocked or guardrail_binding.decision_outcome == "block":
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("guardrail_block")
        if not side_effect_budget_decision.allowed:
            outcome = SecureRuntimeGuardOutcome.block
            reasons.append("budget_failed")
        if (
            required_approval
            and not approval_bundle.evidence
            and outcome == SecureRuntimeGuardOutcome.allow_simulation
        ):
            outcome = SecureRuntimeGuardOutcome.require_approval
            reasons.append("approval_required")
        if (
            required_approval
            and approval_bundle.evidence
            and outcome == SecureRuntimeGuardOutcome.allow_simulation
        ):
            reasons.append("approval_validated")
        if outcome == SecureRuntimeGuardOutcome.allow_simulation:
            reasons.append("allow_simulation")
        return SecureRuntimeGuardDecision(
            decision_id=f"runtime-guard-{capability_plan.request_id}",
            session_id=session.session_id,
            request_id=request.request_id,
            outcome=outcome,
            reason_codes=tuple(reasons),
            required_approval=required_approval,
            approval_present=bool(approval_bundle.evidence),
            kill_switch_status=kill_switch_state.status,
            side_effect_budget_decision_fingerprint=(
                side_effect_budget_decision.decision_fingerprint or ""
            ),
            capability_plan_fingerprint=capability_plan.plan_fingerprint or "",
            policy_binding_fingerprint=policy_binding.binding_fingerprint or "",
            risk_binding_fingerprint=risk_binding.binding_fingerprint or "",
            guardrail_binding_fingerprint=guardrail_binding.binding_fingerprint or "",
            approval_bundle_fingerprint=approval_bundle.bundle_fingerprint or "",
            created_at=created_at or utc_now(),
        )


class DeterministicSecureCapabilityDispatcher:
    """Closed deterministic dispatcher that never calls external components."""

    def simulate(
        self,
        *,
        guard_decision: SecureRuntimeGuardDecision,
        capability_plan: SecureCapabilityInvocationPlan,
        created_at: datetime | None = None,
    ) -> SecureSimulatedDispatchResult:
        if guard_decision.outcome == SecureRuntimeGuardOutcome.kill:
            status = SecureRuntimeDispatchStatus.killed
            code = "dispatch_killed"
        elif guard_decision.outcome == SecureRuntimeGuardOutcome.block:
            status = SecureRuntimeDispatchStatus.blocked
            code = "dispatch_blocked"
        elif guard_decision.outcome == SecureRuntimeGuardOutcome.abstain:
            status = SecureRuntimeDispatchStatus.abstained
            code = "dispatch_abstained"
        elif guard_decision.outcome != SecureRuntimeGuardOutcome.allow_simulation:
            status = SecureRuntimeDispatchStatus.blocked
            code = "dispatch_requires_approval"
        else:
            status = SecureRuntimeDispatchStatus.simulated
            code = f"simulated:{capability_plan.capability_code}"
        return SecureSimulatedDispatchResult(
            dispatch_id=f"simulated-dispatch-{capability_plan.request_id}",
            session_id=capability_plan.session_id,
            request_id=capability_plan.request_id,
            capability_code=capability_plan.capability_code,
            status=status,
            deterministic_result_code=code,
            guard_decision_fingerprint=guard_decision.guard_decision_fingerprint or "",
            capability_plan_fingerprint=capability_plan.plan_fingerprint or "",
            result_summary_fingerprint=secure_runtime_fingerprint(
                {
                    "capability_code": capability_plan.capability_code,
                    "status": status.value,
                    "code": code,
                }
            ),
            created_at=created_at or utc_now(),
        )


class InMemorySecureRuntimeAuditLedger:
    """Append-only session-scoped in-memory audit ledger."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, list[SecureRuntimeAuditRecord]] = {}

    def append(
        self,
        *,
        session_id: str,
        event_type: str,
        request_id: str | None = None,
        trace_id: str | None = None,
        subject_fingerprints: Iterable[str] = (),
        decision_fingerprints: Iterable[str] = (),
        reason_codes: Iterable[str] = (),
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> SecureRuntimeAuditRecord:
        with self._lock:
            prior = self.chain_head(session_id)
            record = SecureRuntimeAuditRecord(
                audit_record_id=f"audit-{session_id}-{len(self._records.get(session_id, [])) + 1}",
                session_id=session_id,
                request_id=request_id,
                trace_id=trace_id,
                event_type=event_type,
                subject_fingerprints=tuple(subject_fingerprints),
                decision_fingerprints=tuple(decision_fingerprints),
                prior_audit_hash=prior,
                reason_codes=tuple(reason_codes),
                metadata=dict(metadata or {}),
                created_at=created_at or utc_now(),
            )
            self._records.setdefault(session_id, []).append(record)
            return record

    def records_by_session(self, session_id: str) -> tuple[SecureRuntimeAuditRecord, ...]:
        with self._lock:
            return tuple(self._records.get(session_id, ()))

    def chain_head(self, session_id: str) -> str:
        with self._lock:
            records = self._records.get(session_id) or []
            if not records:
                return ZERO_FINGERPRINT
            return records[-1].audit_hash or ZERO_FINGERPRINT

    def verify_chain(self, session_id: str) -> bool:
        prior = ZERO_FINGERPRINT
        for record in self.records_by_session(session_id):
            if record.prior_audit_hash != prior:
                return False
            expected = secure_runtime_fingerprint(
                record.model_dump(mode="json", exclude={"audit_hash"})
            )
            if record.audit_hash != expected:
                return False
            prior = record.audit_hash or ZERO_FINGERPRINT
        return True


class InMemorySecureRuntimeSessionRepository:
    """Copy-on-write in-memory repository for local secure-runtime snapshots."""

    def __init__(
        self,
        *,
        sessions: Mapping[str, SecureRuntimeSession] | None = None,
        receipts: Mapping[str, tuple[SecureRuntimeStageReceipt, ...]] | None = None,
        requests: Mapping[str, SecureRuntimeRequestEnvelope] | None = None,
        plans: Mapping[str, SecureCapabilityInvocationPlan] | None = None,
        decisions: Mapping[str, tuple[_DecisionBindingBase, ...]] | None = None,
        audit_records: Mapping[str, tuple[SecureRuntimeAuditRecord, ...]] | None = None,
        checkpoints: Mapping[str, tuple[SecureRuntimeSessionCheckpoint, ...]] | None = None,
    ) -> None:
        self._lock = RLock()
        self._sessions = dict(sessions or {})
        self._receipts = dict(receipts or {})
        self._requests = dict(requests or {})
        self._plans = dict(plans or {})
        self._decisions = dict(decisions or {})
        self._audit_records = dict(audit_records or {})
        self._checkpoints = dict(checkpoints or {})

    def _copy(
        self,
        **updates: Any,
    ) -> InMemorySecureRuntimeSessionRepository:
        return InMemorySecureRuntimeSessionRepository(
            sessions=updates.get("sessions", deepcopy(self._sessions)),
            receipts=updates.get("receipts", deepcopy(self._receipts)),
            requests=updates.get("requests", deepcopy(self._requests)),
            plans=updates.get("plans", deepcopy(self._plans)),
            decisions=updates.get("decisions", deepcopy(self._decisions)),
            audit_records=updates.get("audit_records", deepcopy(self._audit_records)),
            checkpoints=updates.get("checkpoints", deepcopy(self._checkpoints)),
        )

    def with_session(
        self,
        session: SecureRuntimeSession,
    ) -> InMemorySecureRuntimeSessionRepository:
        with self._lock:
            active = [
                item
                for item in self._sessions.values()
                if item.current_state not in TERMINAL_STATES
                and item.session_id != session.session_id
            ]
            if active:
                raise ValueError("only one active secure-runtime session is allowed")
            sessions = dict(self._sessions)
            sessions[session.session_id] = session
            return self._copy(sessions=sessions)

    def with_stage_receipt(
        self,
        receipt: SecureRuntimeStageReceipt,
    ) -> InMemorySecureRuntimeSessionRepository:
        with self._lock:
            existing = list(self._receipts.get(receipt.session_id, ()))
            expected_sequence = len(existing) + 1
            if receipt.sequence_number != expected_sequence:
                raise ValueError("receipt sequence is not contiguous")
            expected_prior = existing[-1].receipt_fingerprint if existing else ZERO_FINGERPRINT
            if receipt.prior_receipt_fingerprint != expected_prior:
                raise ValueError("receipt prior fingerprint mismatch")
            session = self._sessions.get(receipt.session_id)
            if session is not None:
                _validate_transition(session.current_state, receipt.state_after)
                session = session.model_copy(
                    update={
                        "current_state": receipt.state_after,
                        "latest_receipt_fingerprint": receipt.receipt_fingerprint,
                        "receipt_sequence": receipt.sequence_number,
                    }
                )
            existing.append(receipt)
            receipts = dict(self._receipts)
            receipts[receipt.session_id] = tuple(existing)
            sessions = dict(self._sessions)
            if session is not None:
                sessions[session.session_id] = session
            return self._copy(receipts=receipts, sessions=sessions)

    def with_request(
        self,
        request: SecureRuntimeRequestEnvelope,
    ) -> InMemorySecureRuntimeSessionRepository:
        with self._lock:
            requests = dict(self._requests)
            requests[request.request_id] = request
            session = self._sessions.get(request.session_id)
            sessions = dict(self._sessions)
            if session is not None:
                active = tuple(sorted((*session.active_request_ids, request.request_id)))
                if len(active) > session.session_plan.maximum_concurrent_requests:
                    raise ValueError("concurrent request limit exceeded")
                sessions[session.session_id] = session.model_copy(
                    update={"active_request_ids": active}
                )
            return self._copy(requests=requests, sessions=sessions)

    def with_capability_plan(
        self,
        plan: SecureCapabilityInvocationPlan,
    ) -> InMemorySecureRuntimeSessionRepository:
        plans = dict(self._plans)
        plans[plan.plan_id] = plan
        return self._copy(plans=plans)

    def with_decision_binding(
        self,
        decision: _DecisionBindingBase,
    ) -> InMemorySecureRuntimeSessionRepository:
        decisions = dict(self._decisions)
        current = list(decisions.get(decision.request_id, ()))
        current.append(decision)
        decisions[decision.request_id] = tuple(current)
        return self._copy(decisions=decisions)

    def with_audit_record(
        self,
        record: SecureRuntimeAuditRecord,
    ) -> InMemorySecureRuntimeSessionRepository:
        audit_records = dict(self._audit_records)
        current = list(audit_records.get(record.session_id, ()))
        current.append(record)
        audit_records[record.session_id] = tuple(current)
        return self._copy(audit_records=audit_records)

    def with_checkpoint(
        self,
        checkpoint: SecureRuntimeSessionCheckpoint,
    ) -> InMemorySecureRuntimeSessionRepository:
        checkpoints = dict(self._checkpoints)
        current = list(checkpoints.get(checkpoint.session_id, ()))
        if len(current) >= 20:
            raise ValueError("checkpoint limit exceeded")
        current.append(checkpoint)
        checkpoints[checkpoint.session_id] = tuple(current)
        return self._copy(checkpoints=checkpoints)

    def session_by_id(self, session_id: str) -> SecureRuntimeSession | None:
        return self._sessions.get(session_id)

    def request_by_id(self, request_id: str) -> SecureRuntimeRequestEnvelope | None:
        if request_id not in self._requests:
            return None
        return self._requests[request_id]

    def receipts_by_session(self, session_id: str) -> tuple[SecureRuntimeStageReceipt, ...]:
        return tuple(self._receipts.get(session_id, ()))

    def audit_records_by_session(self, session_id: str) -> tuple[SecureRuntimeAuditRecord, ...]:
        return tuple(self._audit_records.get(session_id, ()))

    def active_session_count(self) -> int:
        return sum(
            1 for item in self._sessions.values() if item.current_state not in TERMINAL_STATES
        )

    def active_request_count(self, session_id: str | None = None) -> int:
        if session_id is not None:
            session = self._sessions.get(session_id)
            return 0 if session is None else len(session.active_request_ids)
        return sum(len(session.active_request_ids) for session in self._sessions.values())

    def close_session(
        self,
        *,
        session_id: str,
        closed_at: datetime | None = None,
    ) -> InMemorySecureRuntimeSessionRepository:
        session = self._sessions[session_id]
        if session.active_request_ids:
            raise ValueError("session close requires zero active requests")
        sessions = dict(self._sessions)
        sessions[session_id] = session.model_copy(
            update={
                "current_state": SecureRuntimeSessionState.session_closed,
                "closed_at": closed_at or utc_now(),
            }
        )
        return self._copy(sessions=sessions)

    def complete_request(
        self,
        *,
        session_id: str,
        request_id: str,
    ) -> InMemorySecureRuntimeSessionRepository:
        session = self._sessions[session_id]
        active = tuple(item for item in session.active_request_ids if item != request_id)
        completed = tuple(sorted((*session.completed_request_ids, request_id)))
        sessions = dict(self._sessions)
        sessions[session_id] = session.model_copy(
            update={"active_request_ids": active, "completed_request_ids": completed}
        )
        return self._copy(sessions=sessions)

    def audit(self) -> dict[str, int]:
        return {
            "sessions": len(self._sessions),
            "requests": len(self._requests),
            "receipts": sum(len(items) for items in self._receipts.values()),
            "audit_records": sum(len(items) for items in self._audit_records.values()),
            "checkpoints": sum(len(items) for items in self._checkpoints.values()),
        }


def _validate_transition(
    state_before: SecureRuntimeSessionState,
    state_after: SecureRuntimeSessionState,
) -> None:
    if state_before in TERMINAL_STATES:
        raise ValueError("cannot transition from terminal state")
    if state_after in {
        SecureRuntimeSessionState.abstained,
        SecureRuntimeSessionState.blocked,
        SecureRuntimeSessionState.killed,
        SecureRuntimeSessionState.expired,
        SecureRuntimeSessionState.failed,
    }:
        return
    allowed = ALLOWED_STATE_TRANSITIONS.get(state_before, ())
    if state_after not in allowed:
        raise ValueError("invalid secure-runtime state transition")


class ControlledLocalSecureRuntimeService:
    """Orchestrates the local operator secure-runtime foundation."""

    def __init__(
        self,
        *,
        repository: InMemorySecureRuntimeSessionRepository | None = None,
        audit_ledger: InMemorySecureRuntimeAuditLedger | None = None,
        guard_evaluator: SecureRuntimeGuardEvaluator | None = None,
        dispatcher: DeterministicSecureCapabilityDispatcher | None = None,
    ) -> None:
        self.repository = repository or InMemorySecureRuntimeSessionRepository()
        self.audit_ledger = audit_ledger or InMemorySecureRuntimeAuditLedger()
        self.guard_evaluator = guard_evaluator or SecureRuntimeGuardEvaluator()
        self.dispatcher = dispatcher or DeterministicSecureCapabilityDispatcher()

    def validate_authorization(
        self,
        envelope: SecureRuntimeAuthorizationEnvelope,
    ) -> SecureRuntimeAuthorizationEnvelope:
        return envelope

    def verify_operator_identity(
        self,
        *,
        authorization_envelope: SecureRuntimeAuthorizationEnvelope,
        assertion_envelope: IdentityAssertionEnvelope,
        verification_pipeline: Any,
    ) -> SecureOperatorIdentityBinding:
        binding = bind_verified_local_operator_identity(
            authorization_envelope=authorization_envelope,
            assertion_envelope=assertion_envelope,
            verification_pipeline=verification_pipeline,
        )
        self.audit_ledger.append(
            session_id=authorization_envelope.session_id,
            event_type="identity_verification_passed",
            subject_fingerprints=(binding.operator_identity_fingerprint,),
            decision_fingerprints=(
                binding.verification_bundle_fingerprint,
                binding.replay_bundle_fingerprint,
            ),
            reason_codes=("identity_assertion_verified", "replay_validation_passed"),
        )
        return binding

    def bind_request_identity(
        self,
        **kwargs: Any,
    ) -> SecureRequestIdentityBinding:
        return bind_secure_request_identity(**kwargs)

    def bind_actor_context(self, **kwargs: Any) -> SecureActorContextBinding:
        return bind_secure_actor_context(**kwargs)

    def validate_replay(self, identity_binding: SecureOperatorIdentityBinding) -> bool:
        return identity_binding.replay_validation_passed

    def create_session_plan(self, **kwargs: Any) -> SecureRuntimeSessionPlan:
        return SecureRuntimeSessionPlan(**kwargs)

    def start_session(self, session_plan: SecureRuntimeSessionPlan) -> SecureRuntimeSession:
        session = SecureRuntimeSession(
            session_id=session_plan.authorization_envelope.session_id,
            session_plan=session_plan,
            created_at=utc_now(),
            expires_at=session_plan.expires_at,
        )
        self.repository = self.repository.with_session(session)
        self.audit_ledger.append(
            session_id=session.session_id,
            event_type="session_started",
            subject_fingerprints=(session_plan.plan_fingerprint or "",),
            reason_codes=("session_started",),
        )
        return session

    def validate_stage_command(
        self,
        *,
        session: SecureRuntimeSession,
        command: SecureRuntimeStageCommand,
        kill_switch_state: SecureRuntimeKillSwitchState,
        now: datetime | None = None,
    ) -> None:
        validation_time = now or utc_now()
        if kill_switch_state.status == SecureRuntimeKillSwitchStatus.active:
            raise ValueError("kill switch active")
        if command.session_id != session.session_id:
            raise ValueError("command session mismatch")
        if command.expected_current_state != session.current_state:
            raise ValueError("command state mismatch")
        if command.expires_at <= validation_time:
            raise ValueError("command expired")
        _validate_transition(session.current_state, command.requested_next_state)

    def advance_stage(
        self,
        *,
        session: SecureRuntimeSession,
        command: SecureRuntimeStageCommand,
        output_fingerprints: Iterable[str] = (),
        decision_fingerprints: Iterable[str] = (),
        reason_codes: Iterable[str] = ("stage_transitioned",),
    ) -> SecureRuntimeStageReceipt:
        receipt = SecureRuntimeStageReceipt(
            receipt_id=f"receipt-{session.session_id}-{session.receipt_sequence + 1}",
            session_id=session.session_id,
            request_id=command.request_id,
            sequence_number=session.receipt_sequence + 1,
            prior_receipt_fingerprint=session.latest_receipt_fingerprint,
            state_before=session.current_state,
            state_after=command.requested_next_state,
            disposition=SecureRuntimeStageDisposition.executed,
            command_fingerprint=command.command_fingerprint or "",
            input_fingerprints=command.input_fingerprints,
            output_fingerprints=tuple(output_fingerprints),
            decision_fingerprints=tuple(decision_fingerprints),
            bounded_counts={"active_requests": len(session.active_request_ids)},
            reason_codes=tuple(reason_codes),
            created_at=utc_now(),
        )
        self.repository = self.repository.with_stage_receipt(receipt)
        return receipt

    def validate_request(
        self,
        request: SecureRuntimeRequestEnvelope,
    ) -> SecureRuntimeRequestEnvelope:
        self.repository = self.repository.with_request(request)
        return request

    def create_capability_plan(
        self,
        *,
        request: SecureRuntimeRequestEnvelope,
        side_effect_budget: SecureSideEffectBudget,
    ) -> SecureCapabilityInvocationPlan:
        plan = create_capability_plan(request=request, side_effect_budget=side_effect_budget)
        self.repository = self.repository.with_capability_plan(plan)
        return plan

    def bind_policy_decision(self, **kwargs: Any) -> SecurePolicyBinding:
        binding = bind_policy_decision(**kwargs)
        self.repository = self.repository.with_decision_binding(binding)
        return binding

    def bind_risk_assessment(self, **kwargs: Any) -> SecureRiskBinding:
        binding = bind_risk_assessment(**kwargs)
        self.repository = self.repository.with_decision_binding(binding)
        return binding

    def bind_guardrail_decision(self, **kwargs: Any) -> SecureGuardrailBinding:
        binding = bind_guardrail_decision(**kwargs)
        self.repository = self.repository.with_decision_binding(binding)
        return binding

    def validate_approval_evidence(self, **kwargs: Any) -> SecureApprovalEvidence:
        return project_existing_secure_runtime_approval(**kwargs)

    def evaluate_side_effect_budget(self, **kwargs: Any) -> SecureSideEffectBudgetDecision:
        return evaluate_side_effect_budget(**kwargs)

    def evaluate_runtime_guard(self, **kwargs: Any) -> SecureRuntimeGuardDecision:
        return self.guard_evaluator.evaluate(**kwargs)

    def check_kill_switch(
        self,
        kill_switch: SecureRuntimeKillSwitch,
    ) -> SecureRuntimeKillSwitchState:
        return kill_switch.check()

    def simulate_dispatch(self, **kwargs: Any) -> SecureSimulatedDispatchResult:
        return self.dispatcher.simulate(**kwargs)

    def record_response(
        self,
        *,
        session_id: str,
        request_id: str,
        response_fingerprint: str,
    ) -> SecureRuntimeAuditRecord:
        self.repository = self.repository.complete_request(
            session_id=session_id,
            request_id=request_id,
        )
        return self.audit_ledger.append(
            session_id=session_id,
            request_id=request_id,
            event_type="response_recorded",
            subject_fingerprints=(response_fingerprint,),
            reason_codes=("response_recorded",),
        )

    def create_checkpoint(
        self,
        *,
        session: SecureRuntimeSession,
        actor_context_binding_fingerprint: str,
        kill_switch_fingerprint: str,
        budget_usage_fingerprint: str,
    ) -> SecureRuntimeSessionCheckpoint:
        checkpoint = SecureRuntimeSessionCheckpoint(
            checkpoint_id=f"checkpoint-{session.session_id}-{session.receipt_sequence}",
            session_id=session.session_id,
            current_state=session.current_state,
            latest_stage_receipt_fingerprint=session.latest_receipt_fingerprint,
            stage_receipt_chain_head=session.latest_receipt_fingerprint,
            audit_chain_head=self.audit_ledger.chain_head(session.session_id),
            session_plan_fingerprint=session.session_plan.plan_fingerprint or "",
            actor_context_binding_fingerprint=actor_context_binding_fingerprint,
            active_request_ids=session.active_request_ids,
            completed_request_ids=session.completed_request_ids,
            kill_switch_fingerprint=kill_switch_fingerprint,
            budget_usage_fingerprint=budget_usage_fingerprint,
            created_at=utc_now(),
            expires_at=session.expires_at,
        )
        self.repository = self.repository.with_checkpoint(checkpoint)
        return checkpoint

    def audit_session(self, session_id: str) -> bool:
        return self.audit_ledger.verify_chain(session_id)

    def observability_snapshot(
        self,
        *,
        session: SecureRuntimeSession,
        usage: SecureSideEffectUsage,
        integrity_status: SecureRuntimeIntegrityStatus,
    ) -> SecureRuntimeObservabilitySnapshot:
        audit_count = len(self.audit_ledger.records_by_session(session.session_id))
        receipt_count = len(self.repository.receipts_by_session(session.session_id))
        return SecureRuntimeObservabilitySnapshot(
            snapshot_id=f"observability-{session.session_id}",
            session_id=session.session_id,
            session_state=session.current_state,
            request_counts={
                "active": len(session.active_request_ids),
                "completed": len(session.completed_request_ids),
            },
            active_request_count=len(session.active_request_ids),
            completed_request_count=len(session.completed_request_ids),
            blocked_request_count=0,
            replay_rejection_count=0,
            stage_receipt_count=receipt_count,
            audit_record_count=audit_count,
            policy_decision_count=1,
            risk_decision_count=1,
            guardrail_decision_count=1,
            approval_validation_count=1,
            kill_switch_check_count=usage.kill_switch_checks_per_request,
            simulated_dispatch_count=1,
            budget_usage=usage,
            integrity_status=integrity_status,
            created_at=utc_now(),
        )

    def health_snapshot(
        self,
        *,
        session_id: str,
        state: str = "ready_local_simulation",
        kill_switch_clear: bool = True,
    ) -> SecureRuntimeHealthSnapshot:
        return SecureRuntimeHealthSnapshot(
            health_id=f"health-{session_id}",
            session_id=session_id,
            state=state,  # type: ignore[arg-type]
            kill_switch_clear=kill_switch_clear,
            created_at=utc_now(),
        )

    def close_session(self, session_id: str) -> InMemorySecureRuntimeSessionRepository:
        self.repository = self.repository.close_session(session_id=session_id)
        self.audit_ledger.append(
            session_id=session_id,
            event_type="session_closed",
            reason_codes=("session_closed",),
        )
        return self.repository

    def kill_session(
        self,
        *,
        session_id: str,
        operator_identity_fingerprint: str,
        kill_switch: SecureRuntimeKillSwitch,
    ) -> SecureRuntimeKillSwitchState:
        state = kill_switch.activate(
            reason_code="operator_kill_switch_active",
            operator_identity_fingerprint=operator_identity_fingerprint,
        )
        session = self.repository.session_by_id(session_id)
        if session is not None:
            sessions = dict(self.repository._sessions)
            sessions[session_id] = session.model_copy(
                update={
                    "current_state": SecureRuntimeSessionState.killed,
                    "active_request_ids": tuple(),
                    "killed_at": utc_now(),
                }
            )
            self.repository = self.repository._copy(sessions=sessions)
        self.audit_ledger.append(
            session_id=session_id,
            event_type="session_killed",
            reason_codes=("kill_switch_active",),
        )
        return state

    def replay_fixture(self, fixture_fingerprint: str) -> dict[str, str]:
        return {
            "fixture_fingerprint": ensure_sha256(fixture_fingerprint),
            "result": "fixture_replayed_deterministically",
        }

    def reject_actual_execution(self) -> None:
        raise ValueError("actual capability execution is not authorized")

    def reject_external_effect(self) -> None:
        raise ValueError("external effects are not authorized")


__all__ = [
    "ALLOWED_STATE_TRANSITIONS",
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CLOSED_CAPABILITY_CODES",
    "CLOSED_CAPABILITY_REGISTRY",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "LOCAL_OPERATOR_CONFIRMATION_TEXT",
    "PROGRAM_ID",
    "SECURE_ACTOR_CONTEXT_BINDING_SCHEMA_VERSION",
    "SECURE_APPROVAL_EVIDENCE_SCHEMA_VERSION",
    "SECURE_CAPABILITY_PLAN_SCHEMA_VERSION",
    "SECURE_DECISION_BINDING_SCHEMA_VERSION",
    "SECURE_OPERATOR_IDENTITY_BINDING_SCHEMA_VERSION",
    "SECURE_REQUEST_IDENTITY_BINDING_SCHEMA_VERSION",
    "SECURE_RUNTIME_AUDIT_SCHEMA_VERSION",
    "SECURE_RUNTIME_AUTHORIZATION_SCHEMA_VERSION",
    "SECURE_RUNTIME_CHECKPOINT_SCHEMA_VERSION",
    "SECURE_RUNTIME_CONTRACT_SCHEMA_VERSION",
    "SECURE_RUNTIME_EVIDENCE_SCHEMA_VERSION",
    "SECURE_RUNTIME_GUARD_SCHEMA_VERSION",
    "SECURE_RUNTIME_HEALTH_SCHEMA_VERSION",
    "SECURE_RUNTIME_INTEGRITY_SCHEMA_VERSION",
    "SECURE_RUNTIME_KILL_SWITCH_SCHEMA_VERSION",
    "SECURE_RUNTIME_OBSERVABILITY_SCHEMA_VERSION",
    "SECURE_RUNTIME_REASON_REGISTRY_VERSION",
    "SECURE_RUNTIME_REQUEST_SCHEMA_VERSION",
    "SECURE_RUNTIME_SESSION_SCHEMA_VERSION",
    "SECURE_RUNTIME_STAGE_COMMAND_SCHEMA_VERSION",
    "SECURE_RUNTIME_STAGE_RECEIPT_SCHEMA_VERSION",
    "SECURE_SIDE_EFFECT_BUDGET_SCHEMA_VERSION",
    "SECURE_SIMULATED_DISPATCH_SCHEMA_VERSION",
    "TERMINAL_STATES",
    "ZERO_FINGERPRINT",
    "ControlledLocalSecureRuntimeService",
    "DeterministicSecureCapabilityDispatcher",
    "InMemorySecureRuntimeAuditLedger",
    "InMemorySecureRuntimeSessionRepository",
    "SecureActorContextBinding",
    "SecureApprovalEvidence",
    "SecureApprovalEvidenceBundle",
    "SecureCapabilityInvocationPlan",
    "SecureCapabilityManifest",
    "SecureOperatorIdentityBinding",
    "SecurePolicyBinding",
    "SecureRequestIdentityBinding",
    "SecureRiskBinding",
    "SecureRuntimeAuditRecord",
    "SecureRuntimeAuthorizationEnvelope",
    "SecureRuntimeCapabilityRisk",
    "SecureRuntimeComponentInvocationBinding",
    "SecureRuntimeDiagnostics",
    "SecureRuntimeDispatchStatus",
    "SecureRuntimeEvidenceBundle",
    "SecureRuntimeGuardDecision",
    "SecureRuntimeGuardEvaluator",
    "SecureRuntimeGuardOutcome",
    "SecureRuntimeHealthSnapshot",
    "SecureRuntimeIncident",
    "SecureRuntimeIntegrityFinding",
    "SecureRuntimeIntegrityReport",
    "SecureRuntimeIntegrityStatus",
    "SecureRuntimeKillSwitch",
    "SecureRuntimeKillSwitchState",
    "SecureRuntimeKillSwitchStatus",
    "SecureRuntimeMode",
    "SecureRuntimeObservabilitySnapshot",
    "SecureRuntimeOperatorReviewItem",
    "SecureRuntimeRequestEnvelope",
    "SecureRuntimeSession",
    "SecureRuntimeSessionCheckpoint",
    "SecureRuntimeSessionPlan",
    "SecureRuntimeSessionResult",
    "SecureRuntimeSessionState",
    "SecureRuntimeStageCommand",
    "SecureRuntimeStageDisposition",
    "SecureRuntimeStageReceipt",
    "SecureSideEffectBudget",
    "SecureSideEffectBudgetDecision",
    "SecureSideEffectUsage",
    "SecureSimulatedDispatchResult",
    "bind_guardrail_decision",
    "bind_policy_decision",
    "bind_risk_assessment",
    "bind_secure_actor_context",
    "bind_secure_request_identity",
    "bind_verified_local_operator_identity",
    "capability_manifest_for",
    "create_capability_plan",
    "evaluate_side_effect_budget",
    "local_operator_confirmation_fingerprint",
    "project_existing_secure_runtime_approval",
    "secure_runtime_fingerprint",
    "text_fingerprint",
    "utc_now",
]
