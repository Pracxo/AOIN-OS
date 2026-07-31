"""Provider-neutral model gateway contracts owned by AION Brain."""

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import UTC, datetime
from enum import StrEnum
from math import ceil, isfinite
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.reasoning import (
    ModelCallRecord,
    ModelRouteDecision,
    PromptPacket,
    ReasoningMode,
    ReasoningRiskLevel,
)
from aion_brain.production_auth.canonical import sha256_fingerprint


class ModelProviderType(StrEnum):
    """Provider categories known to the gateway contract.

    Legacy values remain to preserve the pre-AION-233 internal deterministic
    gateway tests. The AION-233 controlled gateway admits only
    ``reference_simulation`` manifests.
    """

    deterministic = "deterministic"
    litellm_http = "litellm_http"
    openai_compatible_http = "openai_compatible_http"
    local_http = "local_http"
    placeholder = "placeholder"
    reference_simulation = "reference_simulation"


ModelProviderStatus = Literal["active", "disabled"]
ModelProviderHealthStatus = Literal["unknown", "healthy", "degraded", "unhealthy"]
ModelPrivacyLevel = Literal["local", "private_gateway", "external"]
ModelLatencyClass = Literal["low", "medium", "high"]
ModelGatewayStatus = Literal[
    "completed",
    "blocked_by_policy",
    "blocked_by_budget",
    "blocked_by_redaction",
    "provider_unavailable",
    "failed",
    "fallback_used",
]
ModelBudgetType = Literal["daily", "weekly", "monthly", "project", "session"]
ModelBudgetStatus = Literal["active", "disabled", "exceeded"]
ModelUsageStatus = Literal["estimated", "recorded", "failed", "blocked"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
    "authorization",
}
_SECRET_VALUE_MARKERS = ("sk-", "bearer ", "authorization=", "api_key=", "token=")


class ModelProvider(BaseModel):
    """Registered provider boundary for model inference."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    provider_type: ModelProviderType
    display_name: str = Field(min_length=1)
    status: ModelProviderStatus
    endpoint_ref: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    health_status: ModelProviderHealthStatus = "unknown"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_health_check_at: datetime | None = None

    @field_validator("endpoint_ref")
    @classmethod
    def endpoint_ref_must_not_contain_secrets(cls, value: str | None) -> str | None:
        """Reject endpoint references that inline credentials."""
        if value is not None and _contains_secret_like_value(value):
            raise ValueError("endpoint_ref must not contain secrets")
        return value

    @field_validator("config")
    @classmethod
    def config_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject provider config that stores credentials directly."""
        _reject_secret_like_keys(value, "config must not contain secret-like keys")
        return value


class ModelProfile(BaseModel):
    """A provider model profile available to the gateway router."""

    model_config = ConfigDict(extra="forbid")

    model_profile_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    mode: ReasoningMode
    status: ModelProviderStatus
    privacy_level: ModelPrivacyLevel
    risk_level: ReasoningRiskLevel
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    cost_per_1k_input_tokens: float | None = Field(default=None, ge=0.0)
    cost_per_1k_output_tokens: float | None = Field(default=None, ge=0.0)
    latency_class: ModelLatencyClass
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject profile metadata that stores credentials directly."""
        _reject_secret_like_keys(value, "metadata must not contain secret-like keys")
        return value


class ModelGatewayRequest(BaseModel):
    """Provider-neutral request to complete a prompt packet."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    reasoning_id: str | None = None
    prompt: PromptPacket
    mode: ReasoningMode
    risk_level: ReasoningRiskLevel
    actor_id: str | None = None
    workspace_id: str | None = None
    scope: list[str] = Field(min_length=1)
    preferred_profile_id: str | None = None
    allow_external: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptRedactionRecord(BaseModel):
    """Prompt inspection and redaction ledger record."""

    model_config = ConfigDict(extra="forbid")

    redaction_id: str = Field(min_length=1)
    trace_id: str | None = None
    reasoning_id: str | None = None
    prompt_id: str | None = None
    redaction_count: int = Field(ge=0)
    redaction_types: list[str]
    blocked: bool
    reason: str | None = None
    created_at: datetime | None = None


class ModelBudgetRecord(BaseModel):
    """Local model budget record used by the gateway guard."""

    model_config = ConfigDict(extra="forbid")

    budget_id: str = Field(min_length=1)
    workspace_id: str | None = None
    actor_id: str | None = None
    scope: list[str] = Field(min_length=1)
    budget_type: ModelBudgetType
    limit_amount: float = Field(ge=0.0)
    used_amount: float = Field(ge=0.0)
    currency: str = Field(min_length=1)
    status: ModelBudgetStatus
    resets_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject budget metadata that stores credentials directly."""
        _reject_secret_like_keys(value, "metadata must not contain secret-like keys")
        return value


class ModelUsageRecord(BaseModel):
    """Model usage and cost estimate ledger record."""

    model_config = ConfigDict(extra="forbid")

    usage_id: str = Field(min_length=1)
    trace_id: str | None = None
    reasoning_id: str | None = None
    model_call_id: str | None = None
    provider_id: str = Field(min_length=1)
    model_profile_id: str | None = None
    model_name: str = Field(min_length=1)
    mode: ReasoningMode
    input_token_estimate: int = Field(ge=0)
    output_token_estimate: int = Field(ge=0)
    cost_estimate: float = Field(ge=0.0)
    latency_ms: int | None = Field(default=None, ge=0)
    status: ModelUsageStatus
    actor_id: str | None = None
    workspace_id: str | None = None
    created_at: datetime | None = None


class ModelProviderHealth(BaseModel):
    """Provider health check result."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    status: ModelProviderHealthStatus
    latency_ms: int | None = Field(default=None, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime


class ModelGatewayResponse(BaseModel):
    """Provider-neutral model gateway completion response."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    model_call: ModelCallRecord
    usage: ModelUsageRecord
    redaction: PromptRedactionRecord | None = None
    route_decision: ModelRouteDecision
    output: dict[str, Any]
    status: ModelGatewayStatus
    reason: str | None = None
    created_at: datetime


def _reject_secret_like_keys(value: object, message: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(secret in normalized for secret in _SECRET_KEY_PARTS):
                raise ValueError(message)
            _reject_secret_like_keys(nested, message)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_like_keys(item, message)


def _contains_secret_like_value(value: str) -> bool:
    normalized = value.lower()
    return any(marker in normalized for marker in _SECRET_VALUE_MARKERS)


MODEL_GATEWAY_CONTRACT_SCHEMA_VERSION = "aion-model-gateway/v1"
MODEL_GATEWAY_AUTHORIZATION_SCHEMA_VERSION = "aion-model-gateway-authorization/v1"
MODEL_GATEWAY_COMPONENT_BINDING_SCHEMA_VERSION = "aion-model-gateway-component-binding/v1"
MODEL_PROVIDER_MANIFEST_SCHEMA_VERSION = "aion-model-gateway-provider-manifest/v1"
MODEL_MANIFEST_SCHEMA_VERSION = "aion-model-gateway-model-manifest/v1"
MODEL_CAPABILITY_PROFILE_SCHEMA_VERSION = "aion-model-gateway-capability-profile/v1"
MODEL_GATEWAY_SESSION_SCHEMA_VERSION = "aion-model-gateway-session/v1"
MODEL_GATEWAY_REQUEST_SCHEMA_VERSION = "aion-model-gateway-request/v1"
MODEL_GATEWAY_MESSAGE_SCHEMA_VERSION = "aion-model-gateway-message/v1"
MODEL_GATEWAY_CONTEXT_ITEM_SCHEMA_VERSION = "aion-model-gateway-context-item/v1"
MODEL_GATEWAY_CONTEXT_BUDGET_SCHEMA_VERSION = "aion-model-gateway-context-budget/v1"
MODEL_GATEWAY_TOKEN_BUDGET_SCHEMA_VERSION = "aion-model-gateway-token-budget/v1"
MODEL_GATEWAY_ROUTING_SCHEMA_VERSION = "aion-model-gateway-routing/v1"
MODEL_GATEWAY_FALLBACK_SCHEMA_VERSION = "aion-model-gateway-fallback/v1"
MODEL_GATEWAY_RETRY_SCHEMA_VERSION = "aion-model-gateway-retry/v1"
MODEL_GATEWAY_CIRCUIT_BREAKER_SCHEMA_VERSION = "aion-model-gateway-circuit-breaker/v1"
MODEL_GATEWAY_GUARD_SCHEMA_VERSION = "aion-model-gateway-guard/v1"
MODEL_GATEWAY_REFERENCE_REQUEST_SCHEMA_VERSION = "aion-model-gateway-reference-request/v1"
MODEL_GATEWAY_REFERENCE_RESPONSE_SCHEMA_VERSION = "aion-model-gateway-reference-response/v1"
MODEL_GATEWAY_STRUCTURED_SCHEMA_VERSION = "aion-model-gateway-structured-output-schema/v1"
MODEL_GATEWAY_RESPONSE_VALIDATION_SCHEMA_VERSION = "aion-model-gateway-response-validation/v1"
MODEL_OUTPUT_PROVENANCE_SCHEMA_VERSION = "aion-model-gateway-output-provenance/v1"
MODEL_GATEWAY_AUDIT_SCHEMA_VERSION = "aion-model-gateway-audit/v1"
MODEL_GATEWAY_OBSERVABILITY_SCHEMA_VERSION = "aion-model-gateway-observability/v1"
MODEL_GATEWAY_HEALTH_SCHEMA_VERSION = "aion-model-gateway-health/v1"
MODEL_GATEWAY_INTEGRITY_SCHEMA_VERSION = "aion-model-gateway-integrity/v1"
MODEL_GATEWAY_EVIDENCE_SCHEMA_VERSION = "aion-model-gateway-evidence/v1"
MODEL_GATEWAY_REASON_REGISTRY_VERSION = "aion-model-gateway-reasons/v1"

PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
AUTHORIZATION_TRANSACTION_ID = "AION-232-SRI-0002"
APPROVAL_RECORD_ID = "AION-232-SRI-0002"
IMPLEMENTATION_TASK = "AION-233"
FORMAL_CLOSEOUT_TASK = "AION-234"
AUTHORIZATION_SCOPE = (
    "authenticated-local-model-request-envelope-provider-model-manifest-closed-allowlist-"
    "context-token-budget-redaction-routing-fallback-retry-circuit-breaker-cost-latency-"
    "estimation-structured-output-validation-untrusted-output-provenance-deterministic-"
    "reference-provider-no-egress-core"
)
PARENT_CAPABILITY_CODE = "brain.think.simulate"
HISTORICAL_COMPONENT_AUTHORIZATION_ID = "AION-230-SRI-0001"
DETERMINISTIC_PROVIDER_ID = "deterministic-reference-provider"
REFERENCE_TEXT_MODEL_ID = "reference-text-sim-v1"
REFERENCE_JSON_MODEL_ID = "reference-json-sim-v1"
LOCAL_MODEL_GATEWAY_CONFIRMATION_TEXT = "RUN_CONTROLLED_MODEL_GATEWAY_SIMULATION"
ZERO_FINGERPRINT = "0000000000000000000000000000000000000000000000000000000000000000"
TOKEN_ESTIMATOR_VERSION = "utf8-ceil-div-3/v1"
SAFE_IDENTIFIER_RE = r"^[A-Za-z0-9._:-]{1,128}$"
LOWER_SHA256_RE = r"^[0-9a-f]{64}$"

MAXIMUM_MODEL_GATEWAY_SESSIONS = 1
MAXIMUM_REQUESTS_PER_SESSION = 100
MAXIMUM_CONCURRENT_REQUESTS = 4
MAXIMUM_PROVIDER_MANIFESTS = 10
MAXIMUM_MODEL_MANIFESTS = 50
MAXIMUM_MODELS_PER_PROVIDER = 25
MAXIMUM_ALLOWED_MODEL_IDS_PER_REQUEST = 10
MAXIMUM_ROUTING_CANDIDATES_PER_REQUEST = 10
MAXIMUM_FALLBACK_CANDIDATES_PER_REQUEST = 3
MAXIMUM_MESSAGES_PER_REQUEST = 128
MAXIMUM_CONTEXT_ITEMS_PER_REQUEST = 256
MAXIMUM_CONTEXT_BYTES_PER_REQUEST = 4_194_304
MAXIMUM_PROMPT_BYTES_PER_REQUEST = 1_048_576
MAXIMUM_INPUT_TOKENS_PER_REQUEST = 131_072
MAXIMUM_OUTPUT_TOKENS_PER_REQUEST = 16_384
MAXIMUM_TOTAL_TOKENS_PER_SESSION = 1_000_000
MAXIMUM_RESPONSE_BYTES_PER_REQUEST = 1_048_576
MAXIMUM_STRUCTURED_OUTPUT_SCHEMA_BYTES = 65_536
MAXIMUM_STRUCTURED_OUTPUT_DEPTH = 16
MAXIMUM_RETRY_ATTEMPTS_PLANNED_PER_REQUEST = 2
MAXIMUM_RESPONSE_VALIDATION_ATTEMPTS_PER_REQUEST = 3
MAXIMUM_CIRCUIT_BREAKER_RECORDS = 100
MAXIMUM_LATENCY_BUDGET_MILLISECONDS = 120_000
MAXIMUM_ESTIMATED_COST_MICROUNITS_PER_REQUEST = 10_000_000
MAXIMUM_ESTIMATED_COST_MICROUNITS_PER_SESSION = 100_000_000
MAXIMUM_AUDIT_RECORDS_PER_SESSION = 10_000
MAXIMUM_TELEMETRY_EVENTS_PER_SESSION = 10_000
MAXIMUM_OPERATOR_REVIEW_ITEMS_PER_SESSION = 500
MAXIMUM_TRACE_BYTES_PER_SESSION = 4_194_304
MAXIMUM_FIXTURE_RECORDS = 5_000
MAXIMUM_FIXTURE_BYTES = 4_194_304
MAXIMUM_SESSION_CHECKPOINTS = 20

ALLOWED_SYSTEM_POLICY_CODES = (
    "aion-safe-structured-simulation-v1",
    "aion-safe-text-simulation-v1",
)
STRUCTURED_SCHEMA_ALLOWED_KEYWORDS = {
    "additionalProperties",
    "const",
    "enum",
    "items",
    "maxItems",
    "maxLength",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "properties",
    "required",
    "type",
}
STRUCTURED_SCHEMA_TYPES = {
    "array",
    "boolean",
    "integer",
    "null",
    "number",
    "object",
    "string",
}
STRUCTURED_SCHEMA_PROHIBITED_KEYWORDS = {
    "$dynamicRef",
    "$id",
    "$ref",
    "contentEncoding",
    "contentMediaType",
    "format",
    "pattern",
    "patternProperties",
    "unevaluatedProperties",
}
PROTECTED_KEY_PARTS = (
    "api_key",
    "authorization_header",
    "bearer",
    "chain_of_thought",
    "client_secret",
    "cookie",
    "credential",
    "endpoint",
    "hidden_reasoning",
    "password",
    "private_key",
    "provider_raw_payload",
    "raw_prompt",
    "raw_response",
    "secret",
    "token",
)
PROTECTED_VALUE_MARKERS = (
    "api_key=",
    "authorization:",
    "bearer ",
    "chain of thought",
    "client_secret",
    "cookie:",
    "hidden reasoning",
    "password=",
    "private key",
    "raw prompt",
    "raw response",
    "sk-",
)
EXECUTABLE_MARKERS = (
    "#!/bin/",
    "<script",
    "eval(",
    "exec(",
    "import os",
    "os.system",
    "subprocess",
)
TOOL_SMUGGLING_MARKERS = (
    "function_call",
    "invoke_tool",
    "tool_call",
    "tool_calls",
)
PRODUCTION_ACTION_MARKERS = (
    "deploy",
    "merge this",
    "production write",
    "write memory",
)


class ModelGatewayMode(StrEnum):
    """Allowed gateway invocation modes."""

    deterministic_simulation = "deterministic_simulation"
    operator_invoked_local = "operator_invoked_local"


class ModelGatewayOperation(StrEnum):
    """Closed gateway operation registry."""

    health_read = "health_read"
    observability_read = "observability_read"
    route_plan = "route_plan"
    text_generate_simulate = "text_generate_simulate"
    structured_generate_simulate = "structured_generate_simulate"


class ModelGatewayMessageRole(StrEnum):
    """Retained role labels for normalized messages."""

    system = "system"
    user = "user"
    assistant = "assistant"


class ModelGatewayOutputMode(StrEnum):
    """Allowed output modes."""

    text = "text"
    structured_json = "structured_json"


class ModelGatewayRouteDisposition(StrEnum):
    """Planning-only route dispositions."""

    selected = "selected"
    blocked = "blocked"
    abstained = "abstained"


class ModelGatewayCircuitBreakerStatus(StrEnum):
    """Local deterministic circuit-breaker states."""

    closed = "closed"
    open = "open"
    half_open = "half_open"


class ModelGatewayGuardOutcome(StrEnum):
    """Model-gateway guard outcomes; none authorizes live effects."""

    allow_reference_simulation = "allow_reference_simulation"
    abstain = "abstain"
    block = "block"


class ModelGatewayResponseValidationStatus(StrEnum):
    """Response validation outcomes."""

    passed = "passed"
    blocked = "blocked"
    failed = "failed"


class ModelOutputTrustClass(StrEnum):
    """All model outputs remain untrusted evidence."""

    untrusted_validated_text = "untrusted_validated_text"
    untrusted_validated_structured = "untrusted_validated_structured"
    untrusted_blocked = "untrusted_blocked"
    untrusted_invalid = "untrusted_invalid"


class ModelGatewaySessionStatus(StrEnum):
    """Gateway session state labels."""

    drafted = "drafted"
    authorized = "authorized"
    active = "active"
    closed = "closed"
    blocked = "blocked"
    expired = "expired"
    failed = "failed"


class ModelGatewayRequestStatus(StrEnum):
    """Gateway request state labels."""

    drafted = "drafted"
    validated = "validated"
    routed = "routed"
    reference_simulated = "reference_simulated"
    response_validated = "response_validated"
    closed = "closed"
    blocked = "blocked"
    failed = "failed"


class ModelGatewayIntegrityStatus(StrEnum):
    """Integrity report outcome."""

    passed = "passed"
    failed = "failed"


class ModelGatewayBaseModel(BaseModel):
    """Strict base model for AION-233 contracts."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def gateway_common_values_must_be_safe(self) -> Self:
        _reject_non_finite_numbers(self.model_dump(mode="python"))
        return self


class ModelGatewayFingerprintedModel(ModelGatewayBaseModel):
    """Model that self-populates and verifies one canonical fingerprint."""

    _fingerprint_field: ClassVar[str | None] = None

    @model_validator(mode="after")
    def gateway_fingerprint_must_match(self) -> Self:
        field_name = self._fingerprint_field
        if field_name is None:
            return self
        expected = model_gateway_fingerprint(
            self.model_dump(mode="json", exclude={field_name})
        )
        current = getattr(self, field_name)
        if current is None:
            object.__setattr__(self, field_name, expected)
        elif current != expected:
            raise ValueError("fingerprint must match canonical model gateway payload")
        return self


def model_gateway_fingerprint(payload: Any) -> str:
    """Return the repository-standard deterministic SHA-256 fingerprint."""

    return sha256_fingerprint(_gateway_json_safe(payload))


def local_model_gateway_confirmation_fingerprint() -> str:
    """Fingerprint the exact local gateway confirmation phrase."""

    return model_gateway_fingerprint(
        {"confirmation": LOCAL_MODEL_GATEWAY_CONFIRMATION_TEXT, "program_id": PROGRAM_ID}
    )


def content_fingerprint(kind: str, value: str | bytes | None) -> str:
    """Fingerprint transient content without retaining the content."""

    if isinstance(value, bytes):
        byte_count = len(value)
        payload_value = value.decode("utf-8", errors="replace")
    else:
        payload_value = value or ""
        byte_count = len(payload_value.encode("utf-8"))
    return model_gateway_fingerprint(
        {"byte_count": byte_count, "kind": kind, "value": payload_value}
    )


def estimate_tokens_from_bytes(byte_count: int) -> int:
    """Return the deterministic UTF-8 byte-count token estimate."""

    if byte_count < 0:
        raise ValueError("byte count must be non-negative")
    return int(ceil(byte_count / 3))


def ensure_gateway_identifier(value: str, *, field_name: str = "identifier") -> str:
    """Validate a bounded ASCII identifier."""

    import re

    if not isinstance(value, str) or re.fullmatch(SAFE_IDENTIFIER_RE, value) is None:
        raise ValueError(f"{field_name} must be a safe bounded ASCII identifier")
    return value


def ensure_gateway_sha256(value: str, *, field_name: str = "fingerprint") -> str:
    """Validate a lowercase SHA-256 fingerprint."""

    import re

    if not isinstance(value, str) or re.fullmatch(LOWER_SHA256_RE, value) is None:
        raise ValueError(f"{field_name} must be a 64-character lowercase SHA-256 value")
    return value


def ensure_gateway_utc(value: datetime) -> datetime:
    """Normalize and require timezone-aware UTC timestamps."""

    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def ensure_gateway_sorted_unique(
    values: object,
    *,
    field_name: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    """Return a sorted unique tuple and reject wildcards or blanks."""

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
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} must be unique")
    for item in result:
        if not item.strip() or item != item.strip() or item == "*":
            raise ValueError(f"{field_name} contains an unsafe value")
    return result


def ensure_gateway_operations(values: object) -> tuple[ModelGatewayOperation, ...]:
    """Normalize gateway operations into deterministic enum order."""

    raw = ensure_gateway_sorted_unique(values, field_name="gateway operations")
    return tuple(ModelGatewayOperation(item) for item in raw)


def reject_gateway_protected_material(value: Any) -> None:
    """Reject protected material recursively without echoing rejected content."""

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


def contains_executable_content(value: Any) -> bool:
    """Detect executable-content markers in a transient value."""

    return any(marker in _text_projection(value).lower() for marker in EXECUTABLE_MARKERS)


def contains_tool_or_function_smuggling(value: Any) -> bool:
    """Detect tool-call or function-call smuggling markers."""

    return any(marker in _text_projection(value).lower() for marker in TOOL_SMUGGLING_MARKERS)


def contains_production_action_marker(value: Any) -> bool:
    """Detect production-action markers in model output."""

    return any(marker in _text_projection(value).lower() for marker in PRODUCTION_ACTION_MARKERS)


def _text_projection(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Mapping):
        return " ".join([str(key) for key in value] + [_text_projection(v) for v in value.values()])
    if isinstance(value, (list, tuple, set)):
        return " ".join(_text_projection(item) for item in value)
    return str(value)


def _reject_non_finite_numbers(value: Any) -> None:
    if isinstance(value, Mapping):
        for nested in value.values():
            _reject_non_finite_numbers(nested)
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            _reject_non_finite_numbers(nested)
    elif isinstance(value, float) and not isfinite(value):
        raise ValueError("non-finite numeric values are not supported")


def _gateway_json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return ensure_gateway_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _gateway_json_safe(nested) for key, nested in value.items()}
    if isinstance(value, (tuple, list)):
        return [_gateway_json_safe(nested) for nested in value]
    if isinstance(value, set):
        return sorted(_gateway_json_safe(nested) for nested in value)
    return value


class ModelGatewayComponentInvocationBinding(ModelGatewayFingerprintedModel):
    """Current AION-232 authority binding to the historical AION-231 component."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    binding_id: str
    current_program_id: str = PROGRAM_ID
    current_authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    component_name: str = "secure-runtime-foundation"
    component_implementation_task: str = "AION-231"
    component_contract_authorization_id: str = HISTORICAL_COMPONENT_AUTHORIZATION_ID
    component_contract_authorization_closed: bool = True
    component_contract_authorization_reactivated: bool = False
    component_invocation_authorized_by_current_parent: bool = True
    secure_runtime_session_id: str
    secure_runtime_request_id: str
    actor_context_binding_fingerprint: str
    parent_capability_plan_fingerprint: str
    parent_runtime_guard_fingerprint: str
    parent_simulated_dispatch_fingerprint: str
    input_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    output_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    invoked_at: datetime
    binding_fingerprint: str | None = None
    read_only: bool = True
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("binding_id", "secure_runtime_session_id", "secure_runtime_request_id")
    @classmethod
    def component_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator(
        "actor_context_binding_fingerprint",
        "parent_capability_plan_fingerprint",
        "parent_runtime_guard_fingerprint",
        "parent_simulated_dispatch_fingerprint",
    )
    @classmethod
    def component_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("input_fingerprints", "output_fingerprints", mode="before")
    @classmethod
    def component_fingerprint_sets_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return tuple(
            ensure_gateway_sha256(item)
            for item in ensure_gateway_sorted_unique(
                value or (), field_name="component fingerprints", allow_empty=True
            )
        )

    @field_validator("invoked_at")
    @classmethod
    def component_invoked_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def component_binding_must_preserve_authority(self) -> Self:
        if (
            self.current_program_id != PROGRAM_ID
            or self.current_authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or self.component_name != "secure-runtime-foundation"
            or self.component_implementation_task != "AION-231"
            or self.component_contract_authorization_id != HISTORICAL_COMPONENT_AUTHORIZATION_ID
            or not self.component_contract_authorization_closed
            or self.component_contract_authorization_reactivated
            or not self.component_invocation_authorized_by_current_parent
            or not self.read_only
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("secure-runtime component binding violates authority boundary")
        return self


class ModelGatewayContextBudget(ModelGatewayFingerprintedModel):
    """Context and byte-count budget for one gateway session/request family."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    schema_version: str = MODEL_GATEWAY_CONTEXT_BUDGET_SCHEMA_VERSION
    maximum_messages_per_request: int = Field(default=MAXIMUM_MESSAGES_PER_REQUEST, ge=1)
    maximum_context_items_per_request: int = Field(
        default=MAXIMUM_CONTEXT_ITEMS_PER_REQUEST, ge=0
    )
    maximum_context_bytes_per_request: int = Field(
        default=MAXIMUM_CONTEXT_BYTES_PER_REQUEST, ge=0
    )
    maximum_prompt_bytes_per_request: int = Field(
        default=MAXIMUM_PROMPT_BYTES_PER_REQUEST, ge=1
    )
    maximum_response_bytes_per_request: int = Field(
        default=MAXIMUM_RESPONSE_BYTES_PER_REQUEST, ge=1
    )
    maximum_structured_output_schema_bytes: int = Field(
        default=MAXIMUM_STRUCTURED_OUTPUT_SCHEMA_BYTES, ge=0
    )
    maximum_structured_output_depth: int = Field(
        default=MAXIMUM_STRUCTURED_OUTPUT_DEPTH, ge=1
    )
    token_estimator_version: str = TOKEN_ESTIMATOR_VERSION
    budget_fingerprint: str | None = None

    @model_validator(mode="after")
    def context_budget_must_not_exceed_authorization(self) -> Self:
        if (
            self.maximum_messages_per_request > MAXIMUM_MESSAGES_PER_REQUEST
            or self.maximum_context_items_per_request > MAXIMUM_CONTEXT_ITEMS_PER_REQUEST
            or self.maximum_context_bytes_per_request > MAXIMUM_CONTEXT_BYTES_PER_REQUEST
            or self.maximum_prompt_bytes_per_request > MAXIMUM_PROMPT_BYTES_PER_REQUEST
            or self.maximum_response_bytes_per_request > MAXIMUM_RESPONSE_BYTES_PER_REQUEST
            or self.maximum_structured_output_schema_bytes
            > MAXIMUM_STRUCTURED_OUTPUT_SCHEMA_BYTES
            or self.maximum_structured_output_depth > MAXIMUM_STRUCTURED_OUTPUT_DEPTH
        ):
            raise ValueError("context budget exceeds AION-232-SRI-0002 resource limits")
        return self


class ModelGatewayTokenBudget(ModelGatewayFingerprintedModel):
    """Token-estimate budget using a deterministic byte-count estimator."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    schema_version: str = MODEL_GATEWAY_TOKEN_BUDGET_SCHEMA_VERSION
    maximum_input_tokens_per_request: int = Field(
        default=MAXIMUM_INPUT_TOKENS_PER_REQUEST, ge=1
    )
    maximum_output_tokens_per_request: int = Field(
        default=MAXIMUM_OUTPUT_TOKENS_PER_REQUEST, ge=1
    )
    maximum_total_tokens_per_session: int = Field(
        default=MAXIMUM_TOTAL_TOKENS_PER_SESSION, ge=1
    )
    token_estimator_version: str = TOKEN_ESTIMATOR_VERSION
    provider_native_tokenizer_used: bool = False
    budget_fingerprint: str | None = None

    @model_validator(mode="after")
    def token_budget_must_not_exceed_authorization(self) -> Self:
        if (
            self.maximum_input_tokens_per_request > MAXIMUM_INPUT_TOKENS_PER_REQUEST
            or self.maximum_output_tokens_per_request > MAXIMUM_OUTPUT_TOKENS_PER_REQUEST
            or self.maximum_total_tokens_per_session > MAXIMUM_TOTAL_TOKENS_PER_SESSION
            or self.provider_native_tokenizer_used
        ):
            raise ValueError("token budget exceeds AION-232-SRI-0002 resource limits")
        return self


class ModelProviderManifest(ModelGatewayFingerprintedModel):
    """Immutable manifest for the only AION-233 provider."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "manifest_fingerprint"

    schema_version: str = MODEL_PROVIDER_MANIFEST_SCHEMA_VERSION
    provider_id: str = DETERMINISTIC_PROVIDER_ID
    provider_type: ModelProviderType = ModelProviderType.reference_simulation
    display_name: str = "AION deterministic reference provider"
    allowed_model_ids: tuple[str, ...] = (REFERENCE_JSON_MODEL_ID, REFERENCE_TEXT_MODEL_ID)
    credential_free: bool = True
    endpoint_present: bool = False
    provider_sdk_enabled: bool = False
    network_egress_enabled: bool = False
    streaming_enabled: bool = False
    actual_provider_call_available: bool = False
    simulation_only: bool = True
    manifest_fingerprint: str | None = None

    @field_validator("provider_id")
    @classmethod
    def provider_identifier_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value, field_name="provider_id")

    @field_validator("allowed_model_ids", mode="before")
    @classmethod
    def allowed_models_must_be_closed(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="allowed model ids")

    @model_validator(mode="after")
    def provider_manifest_must_be_reference_only(self) -> Self:
        if (
            self.provider_id != DETERMINISTIC_PROVIDER_ID
            or self.provider_type != ModelProviderType.reference_simulation
            or self.allowed_model_ids != (REFERENCE_JSON_MODEL_ID, REFERENCE_TEXT_MODEL_ID)
            or not self.credential_free
            or self.endpoint_present
            or self.provider_sdk_enabled
            or self.network_egress_enabled
            or self.streaming_enabled
            or self.actual_provider_call_available
            or not self.simulation_only
        ):
            raise ValueError("provider manifest must remain the deterministic reference provider")
        return self


class ModelManifest(ModelGatewayFingerprintedModel):
    """Immutable model manifest for the deterministic reference provider."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "manifest_fingerprint"

    schema_version: str = MODEL_MANIFEST_SCHEMA_VERSION
    model_id: str
    provider_id: str = DETERMINISTIC_PROVIDER_ID
    supported_operations: tuple[ModelGatewayOperation, ...]
    output_modes: tuple[ModelGatewayOutputMode, ...]
    maximum_input_tokens: int = Field(default=MAXIMUM_INPUT_TOKENS_PER_REQUEST, ge=1)
    maximum_output_tokens: int = Field(default=MAXIMUM_OUTPUT_TOKENS_PER_REQUEST, ge=1)
    maximum_response_bytes: int = Field(default=MAXIMUM_RESPONSE_BYTES_PER_REQUEST, ge=1)
    simulation_only: bool = True
    actual_provider_call: bool = False
    tool_calling: bool = False
    function_calling: bool = False
    network_effect: bool = False
    credential_effect: bool = False
    production_effect: bool = False
    manifest_fingerprint: str | None = None

    @field_validator("model_id", "provider_id")
    @classmethod
    def model_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("supported_operations", mode="before")
    @classmethod
    def model_operations_must_be_sorted(cls, value: object) -> tuple[ModelGatewayOperation, ...]:
        return ensure_gateway_operations(value)

    @field_validator("output_modes", mode="before")
    @classmethod
    def output_modes_must_be_sorted(cls, value: object) -> tuple[ModelGatewayOutputMode, ...]:
        raw = ensure_gateway_sorted_unique(value, field_name="output modes")
        return tuple(ModelGatewayOutputMode(item) for item in raw)

    @model_validator(mode="after")
    def model_manifest_must_be_closed_and_simulated(self) -> Self:
        if self.provider_id != DETERMINISTIC_PROVIDER_ID:
            raise ValueError("model provider reference mismatch")
        if self.model_id == REFERENCE_TEXT_MODEL_ID:
            if self.supported_operations != (ModelGatewayOperation.text_generate_simulate,):
                raise ValueError("text reference model capability mismatch")
            if self.output_modes != (ModelGatewayOutputMode.text,):
                raise ValueError("text reference model output mismatch")
        elif self.model_id == REFERENCE_JSON_MODEL_ID:
            if self.supported_operations != (
                ModelGatewayOperation.structured_generate_simulate,
                ModelGatewayOperation.text_generate_simulate,
            ):
                raise ValueError("JSON reference model capability mismatch")
            if self.output_modes != (
                ModelGatewayOutputMode.structured_json,
                ModelGatewayOutputMode.text,
            ):
                raise ValueError("JSON reference model output mismatch")
        else:
            raise ValueError("unknown model manifest")
        if (
            not self.simulation_only
            or self.actual_provider_call
            or self.tool_calling
            or self.function_calling
            or self.network_effect
            or self.credential_effect
            or self.production_effect
        ):
            raise ValueError("model manifest cannot allow external or production effects")
        return self


class ModelCapabilityProfile(ModelGatewayFingerprintedModel):
    """Capability profile binding provider, model, operation, and limits."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "profile_fingerprint"

    schema_version: str = MODEL_CAPABILITY_PROFILE_SCHEMA_VERSION
    profile_id: str
    provider_id: str
    model_id: str
    supported_operations: tuple[ModelGatewayOperation, ...]
    output_modes: tuple[ModelGatewayOutputMode, ...]
    maximum_input_tokens: int
    maximum_output_tokens: int
    maximum_response_bytes: int
    simulation_only: bool = True
    profile_fingerprint: str | None = None

    @field_validator("profile_id", "provider_id", "model_id")
    @classmethod
    def profile_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("supported_operations", mode="before")
    @classmethod
    def profile_operations_must_be_sorted(cls, value: object) -> tuple[ModelGatewayOperation, ...]:
        return ensure_gateway_operations(value)

    @field_validator("output_modes", mode="before")
    @classmethod
    def profile_output_modes_must_be_sorted(
        cls, value: object
    ) -> tuple[ModelGatewayOutputMode, ...]:
        raw = ensure_gateway_sorted_unique(value, field_name="output modes")
        return tuple(ModelGatewayOutputMode(item) for item in raw)

    @model_validator(mode="after")
    def profile_must_match_closed_model(self) -> Self:
        if self.provider_id != DETERMINISTIC_PROVIDER_ID or self.model_id not in {
            REFERENCE_TEXT_MODEL_ID,
            REFERENCE_JSON_MODEL_ID,
        }:
            raise ValueError("capability profile outside closed model allowlist")
        if not self.simulation_only:
            raise ValueError("capability profile must remain simulation-only")
        return self


class ModelGatewayAuthorizationEnvelope(ModelGatewayFingerprintedModel):
    """Current AION-232 authorization envelope for one model-gateway session."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "envelope_fingerprint"

    schema_version: str = MODEL_GATEWAY_AUTHORIZATION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    model_gateway_session_id: str
    secure_runtime_component_binding: ModelGatewayComponentInvocationBinding
    operator_identity_fingerprint: str
    actor_context_binding_fingerprint: str
    allowed_provider_ids: tuple[str, ...] = (DETERMINISTIC_PROVIDER_ID,)
    allowed_model_ids: tuple[str, ...] = (REFERENCE_JSON_MODEL_ID, REFERENCE_TEXT_MODEL_ID)
    allowed_operations: tuple[ModelGatewayOperation, ...] = (
        ModelGatewayOperation.health_read,
        ModelGatewayOperation.observability_read,
        ModelGatewayOperation.route_plan,
        ModelGatewayOperation.structured_generate_simulate,
        ModelGatewayOperation.text_generate_simulate,
    )
    context_budget: ModelGatewayContextBudget = Field(default_factory=ModelGatewayContextBudget)
    token_budget: ModelGatewayTokenBudget = Field(default_factory=ModelGatewayTokenBudget)
    maximum_requests: int = Field(default=MAXIMUM_REQUESTS_PER_SESSION, ge=1)
    maximum_concurrent_requests: int = Field(default=MAXIMUM_CONCURRENT_REQUESTS, ge=1)
    created_at: datetime
    expires_at: datetime
    confirmation_fingerprint: str
    operator_invoked: bool = True
    local_session: bool = True
    simulation_only: bool = True
    actual_provider_call: bool = False
    network_access: bool = False
    credential_access: bool = False
    production_runtime: bool = False
    production_effect: bool = False
    envelope_fingerprint: str | None = None

    @field_validator("model_gateway_session_id")
    @classmethod
    def authorization_session_id_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("operator_identity_fingerprint", "actor_context_binding_fingerprint")
    @classmethod
    def authorization_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("allowed_provider_ids", "allowed_model_ids", mode="before")
    @classmethod
    def authorization_allowlists_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="authorization allowlist")

    @field_validator("allowed_operations", mode="before")
    @classmethod
    def authorization_operations_must_be_sorted(
        cls, value: object
    ) -> tuple[ModelGatewayOperation, ...]:
        return ensure_gateway_operations(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def authorization_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @field_validator("confirmation_fingerprint")
    @classmethod
    def confirmation_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @model_validator(mode="after")
    def authorization_envelope_must_match_aion232(self) -> Self:
        if (
            self.program_id != PROGRAM_ID
            or self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or self.approval_record_id != APPROVAL_RECORD_ID
            or self.allowed_provider_ids != (DETERMINISTIC_PROVIDER_ID,)
            or self.allowed_model_ids != (REFERENCE_JSON_MODEL_ID, REFERENCE_TEXT_MODEL_ID)
            or self.maximum_requests > MAXIMUM_REQUESTS_PER_SESSION
            or self.maximum_concurrent_requests > MAXIMUM_CONCURRENT_REQUESTS
            or self.confirmation_fingerprint != local_model_gateway_confirmation_fingerprint()
            or self.expires_at <= self.created_at
            or not self.operator_invoked
            or not self.local_session
            or not self.simulation_only
            or self.actual_provider_call
            or self.network_access
            or self.credential_access
            or self.production_runtime
            or self.production_effect
        ):
            raise ValueError("AION-232-SRI-0002 model-gateway authorization mismatch")
        return self


class ModelGatewaySessionPlan(ModelGatewayFingerprintedModel):
    """Bounded local model-gateway session plan."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: str = MODEL_GATEWAY_SESSION_SCHEMA_VERSION
    session_plan_id: str
    authorization_envelope: ModelGatewayAuthorizationEnvelope
    secure_runtime_session_fingerprint: str
    parent_capability_plan_fingerprint: str
    parent_runtime_guard_fingerprint: str
    parent_simulated_dispatch_fingerprint: str
    provider_manifest_fingerprints: tuple[str, ...]
    model_manifest_fingerprints: tuple[str, ...]
    allowed_operations: tuple[ModelGatewayOperation, ...]
    maximum_requests: int = Field(default=MAXIMUM_REQUESTS_PER_SESSION, ge=1)
    maximum_concurrent_requests: int = Field(default=MAXIMUM_CONCURRENT_REQUESTS, ge=1)
    created_at: datetime
    expires_at: datetime
    operator_invoked: bool = True
    simulation_only: bool = True
    background_execution: bool = False
    scheduled_execution: bool = False
    automatic_continuation: bool = False
    production_runtime: bool = False
    plan_fingerprint: str | None = None

    @field_validator("session_plan_id")
    @classmethod
    def session_plan_identifier_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator(
        "secure_runtime_session_fingerprint",
        "parent_capability_plan_fingerprint",
        "parent_runtime_guard_fingerprint",
        "parent_simulated_dispatch_fingerprint",
    )
    @classmethod
    def session_plan_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("provider_manifest_fingerprints", "model_manifest_fingerprints", mode="before")
    @classmethod
    def session_plan_fingerprint_sets_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return tuple(
            ensure_gateway_sha256(item)
            for item in ensure_gateway_sorted_unique(
                value, field_name="session manifest fingerprints"
            )
        )

    @field_validator("allowed_operations", mode="before")
    @classmethod
    def session_plan_operations_must_be_sorted(
        cls, value: object
    ) -> tuple[ModelGatewayOperation, ...]:
        return ensure_gateway_operations(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def session_plan_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def session_plan_must_match_authorization(self) -> Self:
        if self.expires_at > self.authorization_envelope.expires_at:
            raise ValueError("gateway session cannot outlive authorization")
        if self.maximum_requests > self.authorization_envelope.maximum_requests:
            raise ValueError("gateway session request limit exceeds authorization")
        if (
            self.maximum_concurrent_requests
            > self.authorization_envelope.maximum_concurrent_requests
        ):
            raise ValueError("gateway session concurrency exceeds authorization")
        if set(self.allowed_operations) - set(self.authorization_envelope.allowed_operations):
            raise ValueError("gateway session operation allowlist exceeds authorization")
        if (
            not self.operator_invoked
            or not self.simulation_only
            or self.background_execution
            or self.scheduled_execution
            or self.automatic_continuation
            or self.production_runtime
        ):
            raise ValueError("gateway session cannot authorize automated or production runtime")
        return self


class ModelGatewaySession(ModelGatewayFingerprintedModel):
    """Immutable copy-on-write gateway session snapshot."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "session_fingerprint"

    schema_version: str = MODEL_GATEWAY_SESSION_SCHEMA_VERSION
    session_id: str
    session_plan: ModelGatewaySessionPlan
    status: ModelGatewaySessionStatus = ModelGatewaySessionStatus.drafted
    active_request_ids: tuple[str, ...] = Field(default_factory=tuple)
    completed_request_ids: tuple[str, ...] = Field(default_factory=tuple)
    total_estimated_tokens_used: int = Field(default=0, ge=0)
    audit_chain_head: str = ZERO_FINGERPRINT
    created_at: datetime
    expires_at: datetime
    closed_at: datetime | None = None
    production_effect: bool = False
    runtime_effect: bool = False
    session_fingerprint: str | None = None

    @field_validator("session_id")
    @classmethod
    def session_identifier_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("active_request_ids", "completed_request_ids", mode="before")
    @classmethod
    def request_ids_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value or (), field_name="request ids", allow_empty=True)

    @field_validator("audit_chain_head")
    @classmethod
    def audit_chain_head_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at", "expires_at", "closed_at")
    @classmethod
    def session_timestamps_must_be_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_gateway_utc(value)

    @model_validator(mode="after")
    def session_must_remain_local(self) -> Self:
        if self.expires_at > self.session_plan.expires_at:
            raise ValueError("gateway session cannot outlive session plan")
        if (
            len(self.active_request_ids) > self.session_plan.maximum_concurrent_requests
            or self.total_estimated_tokens_used
            > self.session_plan.authorization_envelope.token_budget.maximum_total_tokens_per_session
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("gateway session exceeds local no-effect boundary")
        return self


class ModelGatewayMessage(ModelGatewayFingerprintedModel):
    """Retained message record without raw body content."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "message_fingerprint"

    schema_version: str = MODEL_GATEWAY_MESSAGE_SCHEMA_VERSION
    message_id: str
    role: ModelGatewayMessageRole
    content_fingerprint: str
    utf8_byte_count: int = Field(ge=0)
    deterministic_token_estimate: int = Field(ge=0)
    token_estimator_version: str = TOKEN_ESTIMATOR_VERSION
    redacted: bool = True
    protected_material_detected: bool = False
    created_at: datetime
    message_fingerprint: str | None = None

    @field_validator("message_id")
    @classmethod
    def message_identifier_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("content_fingerprint")
    @classmethod
    def message_content_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def message_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def message_must_be_redacted(self) -> Self:
        if not self.redacted or self.protected_material_detected:
            raise ValueError("retained message must be redacted and protected-material-free")
        return self


class ModelGatewayContextItem(ModelGatewayFingerprintedModel):
    """Retained context record without raw context content."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "item_fingerprint"

    schema_version: str = MODEL_GATEWAY_CONTEXT_ITEM_SCHEMA_VERSION
    context_item_id: str
    context_kind: str
    source_fingerprint: str
    content_fingerprint: str
    utf8_byte_count: int = Field(ge=0)
    deterministic_token_estimate: int = Field(ge=0)
    trust_classification: str = "operator_supplied_untrusted_context"
    redacted: bool = True
    protected_material_detected: bool = False
    item_fingerprint: str | None = None

    @field_validator("context_item_id", "context_kind")
    @classmethod
    def context_identifiers_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("source_fingerprint", "content_fingerprint")
    @classmethod
    def context_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @model_validator(mode="after")
    def context_item_must_be_redacted(self) -> Self:
        if not self.redacted or self.protected_material_detected:
            raise ValueError("retained context must be redacted and protected-material-free")
        return self


class ModelGatewaySystemInstructionPolicyBinding(ModelGatewayFingerprintedModel):
    """Closed system-instruction policy binding by fingerprint only."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = MODEL_GATEWAY_MESSAGE_SCHEMA_VERSION
    policy_code: str
    policy_body_fingerprint: str
    precedes_user_messages: bool = True
    user_override_allowed: bool = False
    raw_policy_retained: bool = False
    created_at: datetime
    binding_fingerprint: str | None = None

    @field_validator("policy_code")
    @classmethod
    def policy_code_must_be_closed(cls, value: str) -> str:
        ensure_gateway_identifier(value)
        if value not in ALLOWED_SYSTEM_POLICY_CODES:
            raise ValueError("unknown model-gateway system policy")
        return value

    @field_validator("policy_body_fingerprint")
    @classmethod
    def policy_body_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def policy_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def policy_binding_must_precede_and_not_retain(self) -> Self:
        if (
            not self.precedes_user_messages
            or self.user_override_allowed
            or self.raw_policy_retained
        ):
            raise ValueError("system policy must precede user input and remain fingerprint-only")
        return self


class ModelGatewayContextUsage(ModelGatewayFingerprintedModel):
    """Observed request context usage using deterministic byte counts."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "usage_fingerprint"

    schema_version: str = MODEL_GATEWAY_CONTEXT_BUDGET_SCHEMA_VERSION
    message_count: int = Field(ge=0)
    context_item_count: int = Field(ge=0)
    prompt_utf8_bytes: int = Field(ge=0)
    context_utf8_bytes: int = Field(ge=0)
    response_byte_limit: int = Field(ge=0)
    structured_schema_bytes: int = Field(ge=0)
    structured_schema_depth: int = Field(ge=0)
    usage_fingerprint: str | None = None


class ModelGatewayContextBudgetDecision(ModelGatewayFingerprintedModel):
    """Fail-closed context budget decision."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "decision_fingerprint"

    schema_version: str = MODEL_GATEWAY_CONTEXT_BUDGET_SCHEMA_VERSION
    decision_id: str
    budget: ModelGatewayContextBudget
    usage: ModelGatewayContextUsage
    allowed: bool
    reason_codes: tuple[str, ...]
    created_at: datetime
    decision_fingerprint: str | None = None
    override_allowed: bool = False

    @field_validator("decision_id")
    @classmethod
    def context_decision_id_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def reason_codes_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="reason codes")

    @field_validator("created_at")
    @classmethod
    def context_decision_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def context_budget_decision_must_match_usage(self) -> Self:
        violations = _context_budget_violations(self.budget, self.usage)
        if self.allowed == bool(violations) or self.override_allowed:
            raise ValueError("context budget decision must fail closed without override")
        if violations and not set(violations).issubset(set(self.reason_codes)):
            raise ValueError("context budget decision reason mismatch")
        return self


class ModelGatewayTokenUsage(ModelGatewayFingerprintedModel):
    """Observed deterministic token-estimate usage."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "usage_fingerprint"

    schema_version: str = MODEL_GATEWAY_TOKEN_BUDGET_SCHEMA_VERSION
    estimated_input_tokens: int = Field(ge=0)
    requested_output_tokens: int = Field(ge=0)
    estimated_session_tokens_after_request: int = Field(ge=0)
    provider_native_tokenizer_used: bool = False
    usage_fingerprint: str | None = None

    @model_validator(mode="after")
    def token_usage_must_be_estimated(self) -> Self:
        if self.provider_native_tokenizer_used:
            raise ValueError("gateway cannot use provider-native tokenizers")
        return self


class ModelGatewayTokenBudgetDecision(ModelGatewayFingerprintedModel):
    """Fail-closed token budget decision."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "decision_fingerprint"

    schema_version: str = MODEL_GATEWAY_TOKEN_BUDGET_SCHEMA_VERSION
    decision_id: str
    budget: ModelGatewayTokenBudget
    usage: ModelGatewayTokenUsage
    allowed: bool
    reason_codes: tuple[str, ...]
    created_at: datetime
    decision_fingerprint: str | None = None
    override_allowed: bool = False

    @field_validator("decision_id")
    @classmethod
    def token_decision_id_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def token_reason_codes_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="reason codes")

    @field_validator("created_at")
    @classmethod
    def token_decision_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def token_budget_decision_must_match_usage(self) -> Self:
        violations = _token_budget_violations(self.budget, self.usage)
        if self.allowed == bool(violations) or self.override_allowed:
            raise ValueError("token budget decision must fail closed without override")
        if violations and not set(violations).issubset(set(self.reason_codes)):
            raise ValueError("token budget decision reason mismatch")
        return self


class ModelStructuredOutputSchema(ModelGatewayFingerprintedModel):
    """Restricted standard-library structured output schema."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "schema_fingerprint"

    schema_version: str = MODEL_GATEWAY_STRUCTURED_SCHEMA_VERSION
    schema_id: str
    schema_definition: Mapping[str, Any]
    schema_byte_count: int = Field(ge=0)
    schema_depth: int = Field(ge=0)
    additional_properties_allowed: bool = False
    tool_calling_enabled: bool = False
    function_calling_enabled: bool = False
    schema_fingerprint: str | None = None

    @field_validator("schema_id")
    @classmethod
    def schema_identifier_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @model_validator(mode="after")
    def structured_schema_must_be_closed_subset(self) -> Self:
        validate_structured_schema_definition(self.schema_definition)
        computed_bytes = len(
            sha256_fingerprint(self.schema_definition).encode("utf-8")
        )
        if self.schema_byte_count > MAXIMUM_STRUCTURED_OUTPUT_SCHEMA_BYTES:
            raise ValueError("structured output schema byte limit exceeded")
        if self.schema_depth > MAXIMUM_STRUCTURED_OUTPUT_DEPTH:
            raise ValueError("structured output schema depth exceeded")
        if (
            self.additional_properties_allowed
            or self.tool_calling_enabled
            or self.function_calling_enabled
            or computed_bytes <= 0
        ):
            raise ValueError("structured schema cannot authorize tools or extra effects")
        return self


class ModelGatewayRequestIdentity(ModelGatewayFingerprintedModel):
    """Session-scoped model request identity."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "identity_fingerprint"

    schema_version: str = MODEL_GATEWAY_REQUEST_SCHEMA_VERSION
    request_id: str
    model_gateway_session_id: str
    secure_runtime_request_id: str
    created_at: datetime
    identity_fingerprint: str | None = None

    @field_validator("request_id", "model_gateway_session_id", "secure_runtime_request_id")
    @classmethod
    def request_identity_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("created_at")
    @classmethod
    def request_identity_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)


class ModelGatewayRequestEnvelope(ModelGatewayFingerprintedModel):
    """Bounded provider-neutral request envelope with no raw prompt body."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "request_fingerprint"

    schema_version: str = MODEL_GATEWAY_REQUEST_SCHEMA_VERSION
    request_envelope_id: str
    model_gateway_session_id: str
    secure_runtime_session_id: str
    secure_runtime_request_id: str
    parent_capability_plan_fingerprint: str
    actor_context_binding_fingerprint: str
    operation: ModelGatewayOperation
    provider_allowlist: tuple[str, ...]
    model_allowlist: tuple[str, ...]
    system_instruction_policy_fingerprint: str
    message_fingerprints: tuple[str, ...]
    context_item_fingerprints: tuple[str, ...]
    context_budget_fingerprint: str
    token_budget_fingerprint: str
    structured_output_schema_fingerprint: str
    requested_output_mode: ModelGatewayOutputMode
    requested_output_tokens: int = Field(ge=0)
    safe_metadata_fingerprint: str
    created_at: datetime
    expires_at: datetime
    prompt_body_retained: bool = False
    provider_credential_reference_present: bool = False
    network_target_present: bool = False
    connector_target_present: bool = False
    tool_target_present: bool = False
    executable_present: bool = False
    production_target_present: bool = False
    simulation_only: bool = True
    actual_provider_call: bool = False
    status: ModelGatewayRequestStatus = ModelGatewayRequestStatus.validated
    request_fingerprint: str | None = None

    @field_validator(
        "request_envelope_id",
        "model_gateway_session_id",
        "secure_runtime_session_id",
        "secure_runtime_request_id",
    )
    @classmethod
    def request_envelope_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator(
        "parent_capability_plan_fingerprint",
        "actor_context_binding_fingerprint",
        "system_instruction_policy_fingerprint",
        "context_budget_fingerprint",
        "token_budget_fingerprint",
        "structured_output_schema_fingerprint",
        "safe_metadata_fingerprint",
    )
    @classmethod
    def request_envelope_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("provider_allowlist", "model_allowlist", mode="before")
    @classmethod
    def request_allowlists_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="request allowlist")

    @field_validator("message_fingerprints", "context_item_fingerprints", mode="before")
    @classmethod
    def request_fingerprint_sets_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return tuple(
            ensure_gateway_sha256(item)
            for item in ensure_gateway_sorted_unique(
                value or (), field_name="request fingerprints", allow_empty=True
            )
        )

    @field_validator("created_at", "expires_at")
    @classmethod
    def request_envelope_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def request_envelope_must_be_bounded(self) -> Self:
        if (
            set(self.provider_allowlist) - {DETERMINISTIC_PROVIDER_ID}
            or set(self.model_allowlist) - {REFERENCE_TEXT_MODEL_ID, REFERENCE_JSON_MODEL_ID}
            or self.expires_at <= self.created_at
            or self.prompt_body_retained
            or self.provider_credential_reference_present
            or self.network_target_present
            or self.connector_target_present
            or self.tool_target_present
            or self.executable_present
            or self.production_target_present
            or not self.simulation_only
            or self.actual_provider_call
        ):
            raise ValueError("model gateway request violates closed simulation boundary")
        return self


class ModelGatewayRequestReplayRecord(ModelGatewayFingerprintedModel):
    """Idempotency ledger record by request ID and request fingerprint."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "replay_fingerprint"

    schema_version: str = MODEL_GATEWAY_REQUEST_SCHEMA_VERSION
    request_id: str
    model_gateway_session_id: str
    request_fingerprint: str
    safe_result_fingerprint: str
    exact_replay_returned: bool = False
    changed_replay_rejected: bool = False
    created_at: datetime
    replay_fingerprint: str | None = None

    @field_validator("request_id", "model_gateway_session_id")
    @classmethod
    def replay_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("request_fingerprint", "safe_result_fingerprint")
    @classmethod
    def replay_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def replay_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)


class ModelGatewayCostEstimate(ModelGatewayFingerprintedModel):
    """Deterministic estimated cost, never a provider charge."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "estimate_fingerprint"

    schema_version: str = MODEL_GATEWAY_ROUTING_SCHEMA_VERSION
    estimated_cost_microunits: int = Field(ge=0)
    live_provider_charge: bool = False
    estimate_fingerprint: str | None = None

    @model_validator(mode="after")
    def cost_estimate_must_be_within_limit(self) -> Self:
        if (
            self.estimated_cost_microunits
            > MAXIMUM_ESTIMATED_COST_MICROUNITS_PER_REQUEST
            or self.live_provider_charge
        ):
            raise ValueError("cost estimate exceeds no-charge budget")
        return self


class ModelGatewayLatencyEstimate(ModelGatewayFingerprintedModel):
    """Deterministic estimated latency, never measured provider telemetry."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "estimate_fingerprint"

    schema_version: str = MODEL_GATEWAY_ROUTING_SCHEMA_VERSION
    estimated_latency_milliseconds: int = Field(ge=0)
    live_latency_measurement: bool = False
    estimate_fingerprint: str | None = None

    @model_validator(mode="after")
    def latency_estimate_must_be_within_limit(self) -> Self:
        if (
            self.estimated_latency_milliseconds > MAXIMUM_LATENCY_BUDGET_MILLISECONDS
            or self.live_latency_measurement
        ):
            raise ValueError("latency estimate exceeds deterministic budget")
        return self


class ModelRoutingCandidate(ModelGatewayFingerprintedModel):
    """Deterministic route candidate evidence."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "candidate_fingerprint"

    schema_version: str = MODEL_GATEWAY_ROUTING_SCHEMA_VERSION
    provider_id: str
    model_id: str
    provider_manifest_fingerprint: str
    model_manifest_fingerprint: str
    capability_profile_fingerprint: str
    operation: ModelGatewayOperation
    context_fit: bool
    token_fit: bool
    output_mode_fit: bool
    structured_schema_fit: bool
    circuit_breaker_status: ModelGatewayCircuitBreakerStatus
    estimated_input_tokens: int = Field(ge=0)
    estimated_output_tokens: int = Field(ge=0)
    estimated_cost_microunits: int = Field(ge=0)
    estimated_latency_milliseconds: int = Field(ge=0)
    candidate_fingerprint: str | None = None

    @field_validator("provider_id", "model_id")
    @classmethod
    def candidate_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator(
        "provider_manifest_fingerprint",
        "model_manifest_fingerprint",
        "capability_profile_fingerprint",
    )
    @classmethod
    def candidate_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)


class ModelRoutingPlan(ModelGatewayFingerprintedModel):
    """Planning-only deterministic routing result."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: str = MODEL_GATEWAY_ROUTING_SCHEMA_VERSION
    routing_plan_id: str
    request_fingerprint: str
    candidates: tuple[ModelRoutingCandidate, ...]
    selected_provider_id: str | None
    selected_model_id: str | None
    disposition: ModelGatewayRouteDisposition
    reason_codes: tuple[str, ...]
    created_at: datetime
    planning_only: bool = True
    automatic_execution: bool = False
    provider_call_performed: bool = False
    network_effect: bool = False
    plan_fingerprint: str | None = None

    @field_validator("routing_plan_id", "selected_provider_id", "selected_model_id")
    @classmethod
    def route_ids_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_gateway_identifier(value)

    @field_validator("request_fingerprint")
    @classmethod
    def route_request_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def route_reason_codes_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="reason codes")

    @field_validator("created_at")
    @classmethod
    def route_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def route_plan_must_remain_planning_only(self) -> Self:
        if (
            len(self.candidates) > MAXIMUM_ROUTING_CANDIDATES_PER_REQUEST
            or not self.planning_only
            or self.automatic_execution
            or self.provider_call_performed
            or self.network_effect
        ):
            raise ValueError("routing plan cannot perform live execution")
        return self


class ModelFallbackPlan(ModelGatewayFingerprintedModel):
    """Planning-only deterministic fallback result."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: str = MODEL_GATEWAY_FALLBACK_SCHEMA_VERSION
    fallback_plan_id: str
    request_fingerprint: str
    primary_model_id: str
    fallback_model_ids: tuple[str, ...]
    created_at: datetime
    planning_only: bool = True
    automatic_fallback_execution: bool = False
    plan_fingerprint: str | None = None

    @field_validator("fallback_plan_id", "primary_model_id")
    @classmethod
    def fallback_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("fallback_model_ids", mode="before")
    @classmethod
    def fallback_models_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(
            value or (), field_name="fallback models", allow_empty=True
        )

    @field_validator("request_fingerprint")
    @classmethod
    def fallback_request_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def fallback_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def fallback_plan_must_not_execute(self) -> Self:
        if (
            len(self.fallback_model_ids) > MAXIMUM_FALLBACK_CANDIDATES_PER_REQUEST
            or not self.planning_only
            or self.automatic_fallback_execution
        ):
            raise ValueError("fallback plan cannot execute automatically")
        return self


class ModelRetryPlan(ModelGatewayFingerprintedModel):
    """Planning-only deterministic retry result."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: str = MODEL_GATEWAY_RETRY_SCHEMA_VERSION
    retry_plan_id: str
    request_fingerprint: str
    planned_attempts: int = Field(ge=0, le=MAXIMUM_RETRY_ATTEMPTS_PLANNED_PER_REQUEST)
    deterministic_delay_milliseconds: tuple[int, ...]
    created_at: datetime
    planning_only: bool = True
    automatic_retry_execution: bool = False
    plan_fingerprint: str | None = None

    @field_validator("retry_plan_id")
    @classmethod
    def retry_id_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("request_fingerprint")
    @classmethod
    def retry_request_fingerprint_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def retry_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def retry_plan_must_not_execute(self) -> Self:
        if (
            len(self.deterministic_delay_milliseconds) != self.planned_attempts
            or not self.planning_only
            or self.automatic_retry_execution
        ):
            raise ValueError("retry plan cannot execute automatically")
        return self


class ModelCircuitBreakerRecord(ModelGatewayFingerprintedModel):
    """Explicit deterministic circuit-breaker transition record."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "record_fingerprint"

    schema_version: str = MODEL_GATEWAY_CIRCUIT_BREAKER_SCHEMA_VERSION
    record_id: str
    provider_id: str
    model_id: str
    previous_status: ModelGatewayCircuitBreakerStatus
    next_status: ModelGatewayCircuitBreakerStatus
    deterministic_fixture_failure: bool
    reason_code: str
    created_at: datetime
    provider_network_failure_ingested: bool = False
    automatic_transition: bool = False
    record_fingerprint: str | None = None

    @field_validator("record_id", "provider_id", "model_id", "reason_code")
    @classmethod
    def circuit_record_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("created_at")
    @classmethod
    def circuit_record_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def circuit_record_must_be_explicit(self) -> Self:
        if self.provider_network_failure_ingested or self.automatic_transition:
            raise ValueError("circuit breaker cannot ingest provider failures automatically")
        return self


class ModelCircuitBreakerState(ModelGatewayFingerprintedModel):
    """Current local circuit-breaker state snapshot."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "state_fingerprint"

    schema_version: str = MODEL_GATEWAY_CIRCUIT_BREAKER_SCHEMA_VERSION
    provider_id: str
    model_id: str
    status: ModelGatewayCircuitBreakerStatus
    record_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    routing_allowed: bool
    deterministic_reference_simulation_only: bool = True
    background_reset: bool = False
    timer_thread: bool = False
    daemon_thread: bool = False
    automatic_half_open_transition: bool = False
    state_fingerprint: str | None = None

    @field_validator("provider_id", "model_id")
    @classmethod
    def circuit_state_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("record_fingerprints", mode="before")
    @classmethod
    def circuit_record_fingerprints_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return tuple(
            ensure_gateway_sha256(item)
            for item in ensure_gateway_sorted_unique(
                value or (), field_name="circuit record fingerprints", allow_empty=True
            )
        )

    @model_validator(mode="after")
    def circuit_state_must_be_local_and_explicit(self) -> Self:
        if (
            not self.deterministic_reference_simulation_only
            or self.background_reset
            or self.timer_thread
            or self.daemon_thread
            or self.automatic_half_open_transition
        ):
            raise ValueError("circuit breaker state cannot schedule or automate transitions")
        if self.status == ModelGatewayCircuitBreakerStatus.open and self.routing_allowed:
            raise ValueError("open circuit must block routing")
        return self


class ModelGatewayGuardDecision(ModelGatewayFingerprintedModel):
    """Guard decision for a bounded reference simulation."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "guard_decision_fingerprint"

    schema_version: str = MODEL_GATEWAY_GUARD_SCHEMA_VERSION
    decision_id: str
    outcome: ModelGatewayGuardOutcome
    reason_codes: tuple[str, ...]
    authorization_envelope_fingerprint: str
    component_binding_fingerprint: str
    secure_runtime_session_fingerprint: str
    parent_capability_plan_fingerprint: str
    parent_runtime_guard_fingerprint: str
    parent_kill_switch_fingerprint: str
    gateway_session_fingerprint: str
    request_fingerprint: str
    provider_manifest_fingerprint: str
    model_manifest_fingerprint: str
    capability_profile_fingerprint: str
    context_budget_decision_fingerprint: str
    token_budget_decision_fingerprint: str
    routing_plan_fingerprint: str
    fallback_plan_fingerprint: str
    retry_plan_fingerprint: str
    circuit_breaker_state_fingerprint: str
    cost_estimate_fingerprint: str
    latency_estimate_fingerprint: str
    created_at: datetime
    guard_decision_fingerprint: str | None = None
    allow_provider_call: bool = False
    allow_network_egress: bool = False
    allow_tool_call: bool = False
    allow_function_call: bool = False
    allow_production_execution: bool = False

    @field_validator("decision_id")
    @classmethod
    def guard_decision_id_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def guard_reason_codes_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="guard reason codes")

    @field_validator(
        "authorization_envelope_fingerprint",
        "component_binding_fingerprint",
        "secure_runtime_session_fingerprint",
        "parent_capability_plan_fingerprint",
        "parent_runtime_guard_fingerprint",
        "parent_kill_switch_fingerprint",
        "gateway_session_fingerprint",
        "request_fingerprint",
        "provider_manifest_fingerprint",
        "model_manifest_fingerprint",
        "capability_profile_fingerprint",
        "context_budget_decision_fingerprint",
        "token_budget_decision_fingerprint",
        "routing_plan_fingerprint",
        "fallback_plan_fingerprint",
        "retry_plan_fingerprint",
        "circuit_breaker_state_fingerprint",
        "cost_estimate_fingerprint",
        "latency_estimate_fingerprint",
    )
    @classmethod
    def guard_decision_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def guard_decision_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def guard_decision_must_never_allow_live_effects(self) -> Self:
        if (
            self.allow_provider_call
            or self.allow_network_egress
            or self.allow_tool_call
            or self.allow_function_call
            or self.allow_production_execution
        ):
            raise ValueError("model-gateway guard cannot allow live effects")
        return self


class ModelGatewayReferenceProviderRequest(ModelGatewayFingerprintedModel):
    """Request to the deterministic reference provider, by fingerprint only."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "reference_request_fingerprint"

    schema_version: str = MODEL_GATEWAY_REFERENCE_REQUEST_SCHEMA_VERSION
    reference_request_id: str
    provider_id: str
    model_id: str
    request_fingerprint: str
    operation: ModelGatewayOperation
    output_mode: ModelGatewayOutputMode
    requested_output_tokens: int = Field(ge=0)
    structured_schema_fingerprint: str
    created_at: datetime
    simulation_only: bool = True
    actual_provider_call: bool = False
    network_effect: bool = False
    credential_effect: bool = False
    reference_request_fingerprint: str | None = None

    @field_validator("reference_request_id", "provider_id", "model_id")
    @classmethod
    def reference_request_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("request_fingerprint", "structured_schema_fingerprint")
    @classmethod
    def reference_request_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def reference_request_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def reference_request_must_be_simulation_only(self) -> Self:
        if (
            self.provider_id != DETERMINISTIC_PROVIDER_ID
            or self.model_id not in {REFERENCE_TEXT_MODEL_ID, REFERENCE_JSON_MODEL_ID}
            or not self.simulation_only
            or self.actual_provider_call
            or self.network_effect
            or self.credential_effect
        ):
            raise ValueError("reference provider request violates simulation-only boundary")
        return self


class ModelGatewayReferenceProviderResponse(ModelGatewayFingerprintedModel):
    """Retained reference-provider response metadata with transient output excluded."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "response_fingerprint"

    schema_version: str = MODEL_GATEWAY_REFERENCE_RESPONSE_SCHEMA_VERSION
    response_id: str
    provider_id: str
    model_id: str
    request_fingerprint: str
    output_fingerprint: str
    output_mode: ModelGatewayOutputMode
    output_byte_count: int = Field(ge=0)
    estimated_output_tokens: int = Field(ge=0)
    finish_code: str = "synthetic_complete"
    created_at: datetime
    transient_output: Any | None = Field(default=None, exclude=True, repr=False)
    synthetic: bool = True
    simulation_only: bool = True
    actual_provider_call: bool = False
    network_effect: bool = False
    credential_effect: bool = False
    tool_effect: bool = False
    connector_effect: bool = False
    production_effect: bool = False
    runtime_effect: bool = False
    response_fingerprint: str | None = None

    @field_validator("response_id", "provider_id", "model_id", "finish_code")
    @classmethod
    def reference_response_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("request_fingerprint", "output_fingerprint")
    @classmethod
    def reference_response_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def reference_response_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def reference_response_must_have_no_effects(self) -> Self:
        if (
            self.provider_id != DETERMINISTIC_PROVIDER_ID
            or self.model_id not in {REFERENCE_TEXT_MODEL_ID, REFERENCE_JSON_MODEL_ID}
            or not self.synthetic
            or not self.simulation_only
            or self.actual_provider_call
            or self.network_effect
            or self.credential_effect
            or self.tool_effect
            or self.connector_effect
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("reference response violates no-effect boundary")
        return self


class ModelOutputValidationResult(ModelGatewayFingerprintedModel):
    """Validation result for untrusted model output."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "validation_fingerprint"

    schema_version: str = MODEL_GATEWAY_RESPONSE_VALIDATION_SCHEMA_VERSION
    validation_id: str
    request_fingerprint: str
    provider_manifest_fingerprint: str
    model_manifest_fingerprint: str
    route_plan_fingerprint: str
    response_fingerprint: str
    output_mode: ModelGatewayOutputMode
    status: ModelGatewayResponseValidationStatus
    reason_codes: tuple[str, ...]
    created_at: datetime
    validation_fingerprint: str | None = None
    trusted: bool = False
    approval_effect: bool = False
    memory_effect: bool = False
    belief_effect: bool = False
    policy_effect: bool = False
    connector_effect: bool = False
    tool_effect: bool = False
    production_effect: bool = False

    @field_validator("validation_id")
    @classmethod
    def validation_id_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator(
        "request_fingerprint",
        "provider_manifest_fingerprint",
        "model_manifest_fingerprint",
        "route_plan_fingerprint",
        "response_fingerprint",
    )
    @classmethod
    def validation_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def validation_reason_codes_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="validation reason codes")

    @field_validator("created_at")
    @classmethod
    def validation_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def validation_must_remain_untrusted(self) -> Self:
        if (
            self.trusted
            or self.approval_effect
            or self.memory_effect
            or self.belief_effect
            or self.policy_effect
            or self.connector_effect
            or self.tool_effect
            or self.production_effect
        ):
            raise ValueError("model output validation cannot create trusted effects")
        return self


class ModelGatewayResponseClassification(ModelGatewayFingerprintedModel):
    """Classification for a validated but untrusted output."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "classification_fingerprint"

    schema_version: str = MODEL_GATEWAY_RESPONSE_VALIDATION_SCHEMA_VERSION
    classification_id: str
    output_trust_class: ModelOutputTrustClass
    response_fingerprint: str
    validation_fingerprint: str
    factual_status: str = "unverified"
    created_at: datetime
    classification_fingerprint: str | None = None
    trusted: bool = False
    synthetic: bool = True
    untrusted: bool = True

    @field_validator("classification_id", "factual_status")
    @classmethod
    def classification_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("response_fingerprint", "validation_fingerprint")
    @classmethod
    def classification_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def classification_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def classification_must_be_untrusted(self) -> Self:
        if self.trusted or not self.synthetic or not self.untrusted:
            raise ValueError("model output classification cannot mark output trusted")
        return self


class ModelOutputProvenance(ModelGatewayFingerprintedModel):
    """Redacted provenance chain for a model output."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "provenance_fingerprint"

    schema_version: str = MODEL_OUTPUT_PROVENANCE_SCHEMA_VERSION
    provenance_id: str
    provider_id: str
    provider_manifest_fingerprint: str
    model_id: str
    model_manifest_fingerprint: str
    request_fingerprint: str
    routing_plan_fingerprint: str
    response_fingerprint: str
    validation_result_fingerprint: str
    output_classification: ModelOutputTrustClass
    redacted: bool
    audit_chain_head: str
    created_at: datetime
    provenance_fingerprint: str | None = None
    raw_prompt_retained: bool = False
    raw_response_retained: bool = False

    @field_validator("provenance_id", "provider_id", "model_id")
    @classmethod
    def provenance_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator(
        "provider_manifest_fingerprint",
        "model_manifest_fingerprint",
        "request_fingerprint",
        "routing_plan_fingerprint",
        "response_fingerprint",
        "validation_result_fingerprint",
        "audit_chain_head",
    )
    @classmethod
    def provenance_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def provenance_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def provenance_must_be_redacted(self) -> Self:
        if not self.redacted or self.raw_prompt_retained or self.raw_response_retained:
            raise ValueError("output provenance cannot retain raw prompt or response")
        return self


class ModelGatewayAuditRecord(ModelGatewayFingerprintedModel):
    """Append-only redacted gateway audit event."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "record_fingerprint"

    schema_version: str = MODEL_GATEWAY_AUDIT_SCHEMA_VERSION
    audit_record_id: str
    session_id: str
    request_id: str | None = None
    event_type: str
    outcome: str
    payload_fingerprint: str
    previous_record_fingerprint: str
    sequence: int = Field(ge=1)
    created_at: datetime
    record_fingerprint: str | None = None
    redacted: bool = True
    raw_prompt_retained: bool = False
    raw_response_retained: bool = False
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("audit_record_id", "session_id", "request_id", "event_type", "outcome")
    @classmethod
    def audit_ids_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_gateway_identifier(value)

    @field_validator("payload_fingerprint", "previous_record_fingerprint")
    @classmethod
    def audit_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def audit_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def audit_record_must_be_redacted(self) -> Self:
        if (
            not self.redacted
            or self.raw_prompt_retained
            or self.raw_response_retained
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("audit record cannot retain raw content or effects")
        return self


class ModelGatewayObservabilitySnapshot(ModelGatewayFingerprintedModel):
    """Redacted gateway observability snapshot."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "snapshot_fingerprint"

    schema_version: str = MODEL_GATEWAY_OBSERVABILITY_SCHEMA_VERSION
    snapshot_id: str
    session_id: str
    event_counters: Mapping[str, int]
    health_state: str
    audit_chain_head: str
    created_at: datetime
    snapshot_fingerprint: str | None = None
    redacted: bool = True
    provider_latency_measured: bool = False
    raw_prompt_retained: bool = False
    raw_response_retained: bool = False

    @field_validator("snapshot_id", "session_id", "health_state")
    @classmethod
    def observability_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("audit_chain_head")
    @classmethod
    def observability_audit_head_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def observability_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def observability_must_be_redacted(self) -> Self:
        if (
            not self.redacted
            or self.provider_latency_measured
            or self.raw_prompt_retained
            or self.raw_response_retained
            or any(value < 0 for value in self.event_counters.values())
        ):
            raise ValueError("observability snapshot cannot contain raw or live telemetry")
        return self


class ModelGatewayHealthSnapshot(ModelGatewayFingerprintedModel):
    """Gateway health/readiness state."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "health_fingerprint"

    schema_version: str = MODEL_GATEWAY_HEALTH_SCHEMA_VERSION
    health_id: str
    health_state: str
    authorization_valid: bool
    secure_runtime_binding_valid: bool
    parent_kill_switch_clear: bool
    provider_registry_exact: bool
    model_registry_exact: bool
    reference_provider_available: bool
    budgets_valid: bool
    actual_provider_calls_disabled: bool = True
    network_egress_disabled: bool = True
    credential_access_disabled: bool = True
    connectors_disabled: bool = True
    tools_disabled: bool = True
    production_runtime_disabled: bool = True
    created_at: datetime
    health_fingerprint: str | None = None

    @field_validator("health_id", "health_state")
    @classmethod
    def health_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("created_at")
    @classmethod
    def health_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def health_readiness_must_preserve_boundary(self) -> Self:
        required = (
            self.authorization_valid,
            self.secure_runtime_binding_valid,
            self.parent_kill_switch_clear,
            self.provider_registry_exact,
            self.model_registry_exact,
            self.reference_provider_available,
            self.budgets_valid,
            self.actual_provider_calls_disabled,
            self.network_egress_disabled,
            self.credential_access_disabled,
            self.connectors_disabled,
            self.tools_disabled,
            self.production_runtime_disabled,
        )
        if self.health_state == "ready_reference_simulation" and not all(required):
            raise ValueError("gateway readiness requires every no-effect control")
        return self


class ModelGatewayIntegrityFinding(ModelGatewayFingerprintedModel):
    """One redacted integrity finding."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "finding_fingerprint"

    schema_version: str = MODEL_GATEWAY_INTEGRITY_SCHEMA_VERSION
    finding_id: str
    severity: str
    category: str
    reason_code: str
    finding_fingerprint: str | None = None

    @field_validator("finding_id", "severity", "category", "reason_code")
    @classmethod
    def integrity_finding_fields_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)


class ModelGatewayIntegrityReport(ModelGatewayFingerprintedModel):
    """Integrity report over gateway evidence and no-effect counters."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "report_fingerprint"

    schema_version: str = MODEL_GATEWAY_INTEGRITY_SCHEMA_VERSION
    report_id: str
    session_id: str
    status: ModelGatewayIntegrityStatus
    findings: tuple[ModelGatewayIntegrityFinding, ...]
    checked_categories: tuple[str, ...]
    audit_chain_head: str
    created_at: datetime
    report_fingerprint: str | None = None
    no_credentials: bool = True
    no_tokens: bool = True
    no_network: bool = True
    no_provider_calls: bool = True
    no_connectors: bool = True
    no_tools: bool = True
    no_modules: bool = True
    no_production_writes: bool = True
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("report_id", "session_id")
    @classmethod
    def integrity_report_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("checked_categories", mode="before")
    @classmethod
    def integrity_categories_must_be_sorted(cls, value: object) -> tuple[str, ...]:
        return ensure_gateway_sorted_unique(value, field_name="checked categories")

    @field_validator("audit_chain_head")
    @classmethod
    def integrity_audit_head_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def integrity_report_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def integrity_report_must_pass_or_explain(self) -> Self:
        if (
            not self.no_credentials
            or not self.no_tokens
            or not self.no_network
            or not self.no_provider_calls
            or not self.no_connectors
            or not self.no_tools
            or not self.no_modules
            or not self.no_production_writes
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("model gateway integrity report cannot record enabled effects")
        if self.status == ModelGatewayIntegrityStatus.passed and self.findings:
            raise ValueError("passed integrity report cannot include findings")
        return self


class ModelGatewayDiagnostics(ModelGatewayFingerprintedModel):
    """Redacted diagnostics counters for operator review."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "diagnostics_fingerprint"

    schema_version: str = MODEL_GATEWAY_EVIDENCE_SCHEMA_VERSION
    diagnostics_id: str
    counters: Mapping[str, int]
    prohibited_effect_counters_zero: bool
    created_at: datetime
    diagnostics_fingerprint: str | None = None
    redacted: bool = True

    @field_validator("diagnostics_id")
    @classmethod
    def diagnostics_id_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("created_at")
    @classmethod
    def diagnostics_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def diagnostics_must_be_redacted(self) -> Self:
        if (
            not self.redacted
            or not self.prohibited_effect_counters_zero
            or any(value < 0 for value in self.counters.values())
        ):
            raise ValueError("diagnostics must be redacted and non-negative")
        return self


class ModelGatewayIncident(ModelGatewayFingerprintedModel):
    """Redacted incident record for blocked or failed gateway events."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "incident_fingerprint"

    schema_version: str = MODEL_GATEWAY_EVIDENCE_SCHEMA_VERSION
    incident_id: str
    session_id: str
    request_id: str | None
    category: str
    reason_code: str
    created_at: datetime
    incident_fingerprint: str | None = None
    redacted: bool = True
    production_effect: bool = False

    @field_validator("incident_id", "session_id", "request_id", "category", "reason_code")
    @classmethod
    def incident_ids_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_gateway_identifier(value)

    @field_validator("created_at")
    @classmethod
    def incident_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)


class ModelGatewayOperatorReviewItem(ModelGatewayFingerprintedModel):
    """Operator-review evidence item for untrusted simulated output."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "review_fingerprint"

    schema_version: str = MODEL_GATEWAY_EVIDENCE_SCHEMA_VERSION
    review_item_id: str
    session_id: str
    request_fingerprint: str | None = None
    operator_review_required: bool = True
    model_gateway_is_simulation_only: bool = True
    reference_provider_is_not_a_live_model: bool = True
    validated_model_output_remains_untrusted: bool = True
    model_output_is_not_factual_truth: bool = True
    model_output_is_not_approval: bool = True
    model_output_is_not_memory: bool = True
    model_output_is_not_belief: bool = True
    model_output_is_not_policy: bool = True
    model_output_is_not_execution: bool = True
    provider_call_authorized: bool = False
    provider_network_egress_authorized: bool = False
    provider_credentials_authorized: bool = False
    connector_execution_authorized: bool = False
    tool_execution_authorized: bool = False
    function_calling_authorized: bool = False
    memory_write_authorized: bool = False
    belief_mutation_authorized: bool = False
    deployment_authorized: bool = False
    model_training_authorized: bool = False
    created_at: datetime
    review_fingerprint: str | None = None
    redacted: bool = True

    @field_validator("review_item_id", "session_id")
    @classmethod
    def review_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("request_fingerprint")
    @classmethod
    def review_request_fingerprint_must_be_safe(cls, value: str | None) -> str | None:
        return None if value is None else ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def review_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def review_item_must_deny_effects(self) -> Self:
        if (
            not self.operator_review_required
            or not self.model_gateway_is_simulation_only
            or not self.reference_provider_is_not_a_live_model
            or not self.validated_model_output_remains_untrusted
            or not self.model_output_is_not_factual_truth
            or not self.model_output_is_not_approval
            or not self.model_output_is_not_memory
            or not self.model_output_is_not_belief
            or not self.model_output_is_not_policy
            or not self.model_output_is_not_execution
            or self.provider_call_authorized
            or self.provider_network_egress_authorized
            or self.provider_credentials_authorized
            or self.connector_execution_authorized
            or self.tool_execution_authorized
            or self.function_calling_authorized
            or self.memory_write_authorized
            or self.belief_mutation_authorized
            or self.deployment_authorized
            or self.model_training_authorized
            or not self.redacted
        ):
            raise ValueError("operator review item cannot authorize effects")
        return self


class ModelGatewayEvidenceBundle(ModelGatewayFingerprintedModel):
    """Redacted operator-review evidence bundle."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "bundle_fingerprint"

    schema_version: str = MODEL_GATEWAY_EVIDENCE_SCHEMA_VERSION
    bundle_id: str
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    diagnostics: ModelGatewayDiagnostics
    incidents: tuple[ModelGatewayIncident, ...] = Field(default_factory=tuple)
    operator_review_items: tuple[ModelGatewayOperatorReviewItem, ...]
    integrity_report_fingerprint: str
    audit_chain_head: str
    created_at: datetime
    bundle_fingerprint: str | None = None
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("bundle_id", "authorization_id")
    @classmethod
    def evidence_ids_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_identifier(value)

    @field_validator("integrity_report_fingerprint", "audit_chain_head")
    @classmethod
    def evidence_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_gateway_sha256(value)

    @field_validator("created_at")
    @classmethod
    def evidence_created_at_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_gateway_utc(value)

    @model_validator(mode="after")
    def evidence_bundle_must_be_redacted(self) -> Self:
        if (
            self.authorization_id != AUTHORIZATION_TRANSACTION_ID
            or not self.operator_review_items
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("evidence bundle must remain redacted and no-effect")
        return self


def _context_budget_violations(
    budget: ModelGatewayContextBudget, usage: ModelGatewayContextUsage
) -> tuple[str, ...]:
    violations: list[str] = []
    if usage.message_count > budget.maximum_messages_per_request:
        violations.append("message_count_exceeded")
    if usage.context_item_count > budget.maximum_context_items_per_request:
        violations.append("context_item_count_exceeded")
    if usage.prompt_utf8_bytes > budget.maximum_prompt_bytes_per_request:
        violations.append("prompt_bytes_exceeded")
    if usage.context_utf8_bytes > budget.maximum_context_bytes_per_request:
        violations.append("context_bytes_exceeded")
    if usage.response_byte_limit > budget.maximum_response_bytes_per_request:
        violations.append("response_bytes_exceeded")
    if usage.structured_schema_bytes > budget.maximum_structured_output_schema_bytes:
        violations.append("structured_schema_bytes_exceeded")
    if usage.structured_schema_depth > budget.maximum_structured_output_depth:
        violations.append("structured_schema_depth_exceeded")
    return tuple(sorted(violations))


def _token_budget_violations(
    budget: ModelGatewayTokenBudget, usage: ModelGatewayTokenUsage
) -> tuple[str, ...]:
    violations: list[str] = []
    if usage.estimated_input_tokens > budget.maximum_input_tokens_per_request:
        violations.append("input_tokens_exceeded")
    if usage.requested_output_tokens > budget.maximum_output_tokens_per_request:
        violations.append("output_tokens_exceeded")
    if usage.estimated_session_tokens_after_request > budget.maximum_total_tokens_per_session:
        violations.append("session_tokens_exceeded")
    if usage.provider_native_tokenizer_used:
        violations.append("provider_native_tokenizer_used")
    return tuple(sorted(violations))


def validate_structured_schema_definition(
    schema_definition: Mapping[str, Any],
    *,
    depth: int = 1,
) -> None:
    """Validate the restricted JSON-schema subset without external resolvers."""

    if depth > MAXIMUM_STRUCTURED_OUTPUT_DEPTH:
        raise ValueError("structured output schema depth exceeded")
    for key, value in schema_definition.items():
        if (
            key in STRUCTURED_SCHEMA_PROHIBITED_KEYWORDS
            or key not in STRUCTURED_SCHEMA_ALLOWED_KEYWORDS
        ):
            raise ValueError("structured output schema keyword is not allowed")
        if key == "type":
            allowed = {value} if isinstance(value, str) else set(value)
            if not allowed or allowed - STRUCTURED_SCHEMA_TYPES:
                raise ValueError("structured output schema type is not allowed")
        if key == "properties":
            if not isinstance(value, Mapping):
                raise ValueError("structured output schema properties must be an object")
            for prop_name, nested in value.items():
                ensure_gateway_identifier(str(prop_name), field_name="schema property")
                if not isinstance(nested, Mapping):
                    raise ValueError("structured output schema property must be an object")
                validate_structured_schema_definition(nested, depth=depth + 1)
        if key == "items":
            if not isinstance(value, Mapping):
                raise ValueError("structured output schema items must be an object")
            validate_structured_schema_definition(value, depth=depth + 1)
        if key == "additionalProperties" and value is not False:
            raise ValueError("structured output schema cannot allow additional properties")
    if not schema_definition:
        raise ValueError("structured output schema must not be empty")


def structured_schema_depth(schema_definition: Mapping[str, Any], *, depth: int = 1) -> int:
    """Return deterministic maximum nested schema depth."""

    max_depth = depth
    properties = schema_definition.get("properties")
    if isinstance(properties, Mapping):
        for nested in properties.values():
            if isinstance(nested, Mapping):
                max_depth = max(max_depth, structured_schema_depth(nested, depth=depth + 1))
    items = schema_definition.get("items")
    if isinstance(items, Mapping):
        max_depth = max(max_depth, structured_schema_depth(items, depth=depth + 1))
    return max_depth


def copy_redacted_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return a protected-material-checked copy of safe metadata."""

    reject_gateway_protected_material(value)
    return deepcopy(dict(value))
