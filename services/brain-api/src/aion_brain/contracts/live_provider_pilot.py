"""AION-248 single OpenAI Responses API live-provider pilot contracts."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.production_auth.canonical import sha256_fingerprint

LIVE_PROVIDER_PILOT_SCHEMA_VERSION = "aion-live-provider-pilot/v1"
LIVE_PROVIDER_AUTHORIZATION_SCHEMA_VERSION = "aion-live-provider-authorization/v1"
LIVE_PROVIDER_COMPONENT_BINDING_SCHEMA_VERSION = "aion-live-provider-component-binding/v1"
LIVE_PROVIDER_SELECTION_SCHEMA_VERSION = "aion-live-provider-selection/v1"
LIVE_PROVIDER_OPERATOR_APPROVAL_SCHEMA_VERSION = "aion-live-provider-operator-approval/v1"
LIVE_PROVIDER_CREDENTIAL_SCHEMA_VERSION = "aion-live-provider-credential/v1"
LIVE_PROVIDER_ENDPOINT_SCHEMA_VERSION = "aion-live-provider-endpoint/v1"
LIVE_PROVIDER_REQUEST_SCHEMA_VERSION = "aion-live-provider-request/v1"
LIVE_PROVIDER_RESPONSE_SCHEMA_VERSION = "aion-live-provider-response/v1"
LIVE_PROVIDER_USAGE_SCHEMA_VERSION = "aion-live-provider-usage/v1"
LIVE_PROVIDER_RETENTION_SCHEMA_VERSION = "aion-live-provider-retention/v1"
LIVE_PROVIDER_TRUST_SCHEMA_VERSION = "aion-live-provider-trust/v1"
LIVE_PROVIDER_UNCERTAINTY_SCHEMA_VERSION = "aion-live-provider-uncertainty/v1"
LIVE_PROVIDER_REPLAY_SCHEMA_VERSION = "aion-live-provider-replay/v1"
LIVE_PROVIDER_AUDIT_SCHEMA_VERSION = "aion-live-provider-audit/v1"
LIVE_PROVIDER_OBSERVABILITY_SCHEMA_VERSION = "aion-live-provider-observability/v1"
LIVE_PROVIDER_INTEGRITY_SCHEMA_VERSION = "aion-live-provider-integrity/v1"
LIVE_PROVIDER_EVIDENCE_SCHEMA_VERSION = "aion-live-provider-evidence/v1"

PROGRAM_ID = "AION-ADAPTIVE-INTELLIGENCE-001"
AUTHORIZATION_TRANSACTION_ID = "AION-247-AI-0002"
APPROVAL_RECORD_ID = "AION-247-AI-0002"
PARENT_EVALUATION_ID = "AION-ECGPE-001"
IMPLEMENTATION_TASK = "AION-248"
FORMAL_CLOSEOUT_TASK = "AION-249"
FINAL_PLANNED_TASK = "AION-260"
PILOT_ID = "AION-248-single-openai-responses-api-synthetic-live-provider-pilot"
PROVIDER_ID = "openai"
PROVIDER_API_FAMILY = "responses"
SELECTED_MODEL_ID = "gpt-5.6-terra"
ALLOWED_MODEL_IDS = ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")
MODEL_FAMILY_BOUNDARY = "gpt-5.6"
ENDPOINT_SCHEME = "https"
ENDPOINT_HOST = "api.openai.com"
ENDPOINT_PORT = 443
ENDPOINT_PATH = "/v1/responses"
HTTP_METHOD = "POST"
REASONING_EFFORT: Literal["low"] = "low"
PILOT_CONFIRMATION_TEXT = "RUN_SINGLE_OPENAI_RESPONSES_API_SYNTHETIC_LIVE_PROVIDER_PILOT"
ZERO_FINGERPRINT = "0000000000000000000000000000000000000000000000000000000000000000"
SAFE_IDENTIFIER_RE = r"^[A-Za-z0-9._:-]{1,160}$"
LOWER_SHA256_RE = r"^[0-9a-f]{64}$"

MAXIMUM_LIVE_PROVIDER_SESSIONS = 1
MAXIMUM_LIVE_PROVIDERS = 1
MAXIMUM_LIVE_MODELS = 1
MAXIMUM_LIVE_PROVIDER_CALLS = 6
MAXIMUM_SUCCESSFUL_LIVE_RESPONSES = 6
MAXIMUM_AUTHORIZATION_HEADERS_CREATED = 6
MAXIMUM_TLS_CONNECTIONS = 6
MAXIMUM_HTTP_REQUESTS = 6
MAXIMUM_DNS_RESOLUTIONS = 8
MAXIMUM_REQUEST_PAYLOAD_BYTES = 262_144
MAXIMUM_RESPONSE_PAYLOAD_BYTES = 2_097_152
MAXIMUM_TOTAL_INPUT_TOKENS = 60_000
MAXIMUM_TOTAL_OUTPUT_TOKENS = 12_000
MAXIMUM_REQUEST_TIMEOUT_SECONDS = 120
MAXIMUM_SESSION_SECONDS = 1_200
MAXIMUM_CONCURRENCY = 1
MAXIMUM_MESSAGES_PER_REQUEST = 16
MAXIMUM_EVIDENCE_BYTES = 20_971_520
MAXIMUM_EVIDENCE_RECORDS = 2_000
MAXIMUM_OPERATOR_REVIEW_ITEMS = 12
MAXIMUM_AUDIT_RECORDS = 500
MAXIMUM_OBSERVABILITY_RECORDS = 500

EXPECTED_SOURCE_SCOPE = (
    "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/__init__.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/authorization.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/component_binding.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/provider_selection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/operator_approval.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/credential_boundary.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/endpoint_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/request_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/response_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/usage_budget.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/retention_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/transport.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/openai_responses_adapter.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/trust.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/redaction.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/replay.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/audit.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/observability.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/integrity.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/evidence.py",
    "scripts/live-provider-pilot-local-run.py",
)

PROHIBITED_RUNTIME_SOURCE_NAMES = (
    "provider_tools.py",
    "web_search.py",
    "file_search.py",
    "code_interpreter.py",
    "computer_use.py",
    "mcp_runtime.py",
    "credential_store.py",
    "token_store.py",
    "background_worker.py",
    "scheduler.py",
    "network.py",
    "http_client.py",
)

REQUIRED_COUNTER_TARGETS: dict[str, int] = {
    "live_provider_sessions_started": 1,
    "live_provider_sessions_closed": 1,
    "active_live_provider_sessions_after_close": 0,
    "selected_providers": 1,
    "selected_models": 1,
    "operator_model_selection_records": 1,
    "operator_approval_records": 1,
    "provider_credentials_read": 1,
    "provider_credentials_persisted": 0,
    "credential_fingerprints_created": 0,
    "authorization_headers_created": 6,
    "authorization_headers_persisted": 0,
    "tls_connections": 6,
    "http_requests": 6,
    "live_provider_calls": 6,
    "successful_live_responses": 6,
    "store_false_requests": 6,
    "background_false_requests": 6,
    "stream_false_requests": 6,
    "tool_free_requests": 6,
    "file_free_requests": 6,
    "previous_response_references": 0,
    "live_response_projections": 6,
    "trust_assessments_created": 6,
    "uncertainty_projections_created": 6,
    "operator_review_items_created": 6,
    "usage_records_created": 6,
    "exact_replays_returned": 1,
    "changed_replays_rejected": 1,
    "context_budget_rejections": 1,
    "output_budget_rejections": 1,
    "unauthorized_tool_requests_rejected": 1,
    "store_true_requests_rejected": 1,
    "background_requests_rejected": 1,
    "streaming_requests_rejected": 1,
    "alternate_hosts_rejected": 1,
    "alternate_paths_rejected": 1,
    "redirect_attempts_rejected": 1,
    "proxy_attempts_rejected": 1,
    "credential_file_inputs_rejected": 1,
    "credential_cli_inputs_rejected": 1,
    "previous_response_references_rejected": 1,
    "file_inputs_rejected": 1,
    "image_inputs_rejected": 1,
    "audio_inputs_rejected": 1,
    "unapproved_model_aliases_rejected": 1,
    "model_switches_rejected": 1,
    "memory_write_escalations_rejected": 1,
    "tool_execution_escalations_rejected": 1,
    "temporary_files_retained": 0,
}

ZERO_COUNTER_TARGETS = {
    "provider_credentials_generated",
    "provider_credentials_logged",
    "provider_tokens_persisted",
    "raw_authorization_headers_persisted",
    "store_true_requests_sent",
    "background_requests_sent",
    "streaming_requests_sent",
    "provider_tool_definitions_sent",
    "provider_tool_calls_received",
    "provider_web_search_calls",
    "provider_file_search_calls",
    "provider_code_interpreter_calls",
    "provider_computer_use_calls",
    "provider_mcp_calls",
    "provider_function_calls",
    "file_uploads",
    "image_inputs_sent",
    "audio_inputs_sent",
    "raw_prompts_persisted",
    "raw_responses_persisted",
    "hidden_reasoning_records",
    "memory_writes",
    "verified_knowledge_promotions",
    "belief_mutations",
    "external_tool_executions",
    "external_connector_calls",
    "background_cycles",
    "scheduled_provider_calls",
    "source_mutations",
    "git_operations",
    "production_deployments",
    "model_weight_changes",
}

PROTECTED_KEY_PARTS = (
    "api_key",
    "raw_authorization_header",
    "bearer",
    "hidden_reasoning",
    "password",
    "private_key",
    "prompt_text",
    "provider_error_message",
    "raw_response",
    "raw_prompt",
    "raw_provider_response",
    "response_text",
    "secret",
)
PROTECTED_VALUE_MARKERS = (
    "api_key=",
    "authorization:",
    "bearer ",
    "client_secret",
    "hidden reasoning",
    "password=",
    "private key",
    "raw prompt",
    "raw response",
    "sk-",
)


class LiveProviderScenarioCode(StrEnum):
    """The six authorized synthetic live-provider scenarios."""

    synthetic_general_reasoning = "SYNTHETIC_GENERAL_REASONING"
    synthetic_code_review = "SYNTHETIC_CODE_REVIEW"
    synthetic_classification = "SYNTHETIC_CLASSIFICATION"
    synthetic_restricted_json = "SYNTHETIC_RESTRICTED_JSON"
    synthetic_multilingual = "SYNTHETIC_MULTILINGUAL"
    synthetic_long_context_summarization = "SYNTHETIC_LONG_CONTEXT_SUMMARIZATION"


class LiveProviderTrustClass(StrEnum):
    """Every provider output remains untrusted."""

    untrusted_live_provider_output = "untrusted_live_provider_output"
    schema_validated_untrusted_live_provider_output = (
        "schema_validated_untrusted_live_provider_output"
    )
    untrusted_blocked_live_provider_output = "untrusted_blocked_live_provider_output"


class LiveProviderReplayOutcome(StrEnum):
    """Replay outcomes."""

    recorded = "recorded"
    exact_replay_returned = "exact_replay_returned"
    changed_replay_rejected = "changed_replay_rejected"


class LiveProviderAuditOutcome(StrEnum):
    """Audit event outcomes."""

    accepted = "accepted"
    rejected = "rejected"
    observed = "observed"


class LiveProviderIntegrityStatus(StrEnum):
    """Integrity outcomes."""

    passed = "passed"
    failed = "failed"


class LiveProviderBaseModel(BaseModel):
    """Strict, immutable base for AION-248 records."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def live_provider_common_values_must_be_safe(self) -> Self:
        _reject_non_finite_numbers(self.model_dump(mode="python"))
        return self


class LiveProviderFingerprintedModel(LiveProviderBaseModel):
    """Model that self-populates a canonical fingerprint field."""

    _fingerprint_field: ClassVar[str | None] = None

    @model_validator(mode="after")
    def live_provider_fingerprint_must_match(self) -> Self:
        field_name = self._fingerprint_field
        if field_name is None:
            return self
        expected = live_provider_fingerprint(
            self.model_dump(mode="json", exclude={field_name})
        )
        current = getattr(self, field_name)
        if current is None:
            object.__setattr__(self, field_name, expected)
        elif current != expected:
            raise ValueError("fingerprint must match canonical live-provider payload")
        return self


def live_provider_fingerprint(payload: Any) -> str:
    """Return the repository-standard canonical SHA-256 fingerprint."""

    return sha256_fingerprint(payload)


def content_fingerprint(kind: str, value: str | bytes | None) -> str:
    """Fingerprint transient content without retaining it in contract records."""

    if isinstance(value, bytes):
        byte_count = len(value)
        payload_value = value.decode("utf-8", errors="replace")
    else:
        payload_value = value or ""
        byte_count = len(payload_value.encode("utf-8"))
    return live_provider_fingerprint(
        {"byte_count": byte_count, "kind": kind, "value": payload_value}
    )


def estimate_tokens_from_bytes(byte_count: int) -> int:
    """Return a deterministic rough token estimate."""

    if byte_count < 0:
        raise ValueError("byte count must be non-negative")
    return int(math.ceil(byte_count / 3))


def ensure_utc(value: datetime) -> datetime:
    """Normalize timestamps to timezone-aware UTC."""

    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(UTC)


def ensure_safe_identifier(value: str, *, field_name: str = "identifier") -> str:
    """Validate a bounded ASCII identifier."""

    if re.fullmatch(SAFE_IDENTIFIER_RE, value) is None:
        raise ValueError(f"{field_name} must be a bounded ASCII identifier")
    return value


def ensure_sha256(value: str, *, field_name: str = "fingerprint") -> str:
    """Validate a lowercase SHA-256 fingerprint."""

    if re.fullmatch(LOWER_SHA256_RE, value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 fingerprint")
    return value


def assert_no_protected_material(payload: object) -> None:
    """Reject raw prompts, outputs, credentials, and authorization material."""

    _reject_protected_material(payload)


class LiveProviderResourceLimits(LiveProviderBaseModel):
    """Exact AION-247-AI-0002 resource limits for AION-248."""

    maximum_live_provider_sessions: int = MAXIMUM_LIVE_PROVIDER_SESSIONS
    maximum_live_providers: int = MAXIMUM_LIVE_PROVIDERS
    maximum_live_models: int = MAXIMUM_LIVE_MODELS
    maximum_live_provider_calls: int = MAXIMUM_LIVE_PROVIDER_CALLS
    maximum_successful_live_responses: int = MAXIMUM_SUCCESSFUL_LIVE_RESPONSES
    maximum_authorization_headers_created: int = MAXIMUM_AUTHORIZATION_HEADERS_CREATED
    maximum_tls_connections: int = MAXIMUM_TLS_CONNECTIONS
    maximum_http_requests: int = MAXIMUM_HTTP_REQUESTS
    maximum_dns_resolutions: int = MAXIMUM_DNS_RESOLUTIONS
    maximum_request_payload_bytes: int = MAXIMUM_REQUEST_PAYLOAD_BYTES
    maximum_response_payload_bytes: int = MAXIMUM_RESPONSE_PAYLOAD_BYTES
    maximum_total_input_tokens: int = MAXIMUM_TOTAL_INPUT_TOKENS
    maximum_total_output_tokens: int = MAXIMUM_TOTAL_OUTPUT_TOKENS
    maximum_request_timeout_seconds: int = MAXIMUM_REQUEST_TIMEOUT_SECONDS
    maximum_session_seconds: int = MAXIMUM_SESSION_SECONDS
    maximum_concurrency: int = MAXIMUM_CONCURRENCY
    maximum_messages_per_request: int = MAXIMUM_MESSAGES_PER_REQUEST
    maximum_evidence_bytes: int = MAXIMUM_EVIDENCE_BYTES
    maximum_evidence_records: int = MAXIMUM_EVIDENCE_RECORDS
    maximum_operator_review_items: int = MAXIMUM_OPERATOR_REVIEW_ITEMS
    maximum_audit_records: int = MAXIMUM_AUDIT_RECORDS
    maximum_observability_records: int = MAXIMUM_OBSERVABILITY_RECORDS
    maximum_provider_credentials_read: int = 1
    maximum_provider_credentials_persisted: int = 0
    maximum_provider_credentials_generated: int = 0
    maximum_provider_tokens_persisted: int = 0
    maximum_raw_authorization_headers_persisted: int = 0
    maximum_provider_tool_definitions: int = 0
    maximum_provider_tool_calls: int = 0
    maximum_provider_web_search_calls: int = 0
    maximum_provider_file_search_calls: int = 0
    maximum_provider_code_interpreter_calls: int = 0
    maximum_provider_computer_use_calls: int = 0
    maximum_provider_mcp_calls: int = 0
    maximum_file_uploads: int = 0
    maximum_image_inputs: int = 0
    maximum_audio_inputs: int = 0
    maximum_previous_response_references: int = 0
    maximum_redirects: int = 0
    maximum_automatic_retries: int = 0
    maximum_background_requests: int = 0
    maximum_store_true_requests: int = 0
    maximum_streaming_requests: int = 0
    maximum_raw_prompts_persisted: int = 0
    maximum_raw_responses_persisted: int = 0
    maximum_hidden_reasoning_records: int = 0
    maximum_memory_writes: int = 0
    maximum_verified_knowledge_promotions: int = 0
    maximum_belief_mutations: int = 0
    maximum_external_tool_executions: int = 0
    maximum_external_connector_calls: int = 0
    maximum_background_cycles: int = 0
    maximum_scheduled_provider_calls: int = 0
    maximum_source_mutations: int = 0
    maximum_git_operations: int = 0
    maximum_production_deployments: int = 0
    maximum_model_weight_changes: int = 0


class LiveProviderProhibitedCapabilities(LiveProviderBaseModel):
    """Booleans that must remain false."""

    provider_builtin_tools_enabled: bool = False
    provider_custom_tools_enabled: bool = False
    provider_web_search_enabled: bool = False
    provider_file_search_enabled: bool = False
    provider_code_interpreter_enabled: bool = False
    provider_computer_use_enabled: bool = False
    provider_function_calling_enabled: bool = False
    provider_remote_mcp_enabled: bool = False
    file_upload_enabled: bool = False
    image_input_enabled: bool = False
    audio_input_enabled: bool = False
    previous_response_id_enabled: bool = False
    background_mode_enabled: bool = False
    streaming_enabled: bool = False
    store_true_enabled: bool = False
    proxy_use_enabled: bool = False
    redirect_following_enabled: bool = False
    provider_model_listing_call_enabled: bool = False
    provider_endpoint_discovery_enabled: bool = False
    multiple_live_providers_enabled: bool = False
    multiple_live_models_enabled: bool = False
    credential_file_input_enabled: bool = False
    credential_cli_argument_enabled: bool = False
    credential_fingerprinting_enabled: bool = False
    credential_logging_enabled: bool = False
    credential_persistence_enabled: bool = False
    provider_token_persistence_enabled: bool = False
    raw_authorization_header_persistence_enabled: bool = False
    raw_prompt_persistence_enabled: bool = False
    raw_response_persistence_enabled: bool = False
    hidden_reasoning_capture_enabled: bool = False
    persistent_memory_write_enabled: bool = False
    verified_knowledge_promotion_enabled: bool = False
    actual_belief_mutation_enabled: bool = False
    external_tool_execution_enabled: bool = False
    external_connector_execution_enabled: bool = False
    autonomous_background_loop_enabled: bool = False
    scheduled_provider_calls_enabled: bool = False
    source_rewrite_enabled: bool = False
    runtime_git_mutation_enabled: bool = False
    runtime_pull_request_creation_enabled: bool = False
    automatic_merge_enabled: bool = False
    production_deployment_enabled: bool = False
    production_runtime_authorized: bool = False
    model_weight_training_enabled: bool = False

    @model_validator(mode="after")
    def all_capabilities_must_be_false(self) -> Self:
        if any(bool(value) for value in self.model_dump(mode="python").values()):
            raise ValueError("prohibited live-provider capability enabled")
        return self


class LiveProviderRequestPolicy(LiveProviderBaseModel):
    """Payload policy for all six Responses API requests."""

    store: bool = False
    background: bool = False
    stream: bool = False
    synthetic_text_only: bool = True
    tools: bool = False
    files: bool = False
    previous_response_id: bool = False
    image_input: bool = False
    audio_input: bool = False

    @model_validator(mode="after")
    def request_policy_must_be_exact(self) -> Self:
        if (
            self.store
            or self.background
            or self.stream
            or self.tools
            or self.files
            or self.previous_response_id
            or self.image_input
            or self.audio_input
            or not self.synthetic_text_only
        ):
            raise ValueError("live-provider request policy must remain closed")
        return self


class LiveProviderAuthorizationEnvelope(LiveProviderFingerprintedModel):
    """AION-248 implementation authorization envelope."""

    _fingerprint_field: ClassVar[str | None] = "authorization_fingerprint"

    schema_version: str = LIVE_PROVIDER_AUTHORIZATION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    parent_evaluation_id: str = PARENT_EVALUATION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    formal_closeout_task: str = FORMAL_CLOSEOUT_TASK
    final_planned_task: str = FINAL_PLANNED_TASK
    provider_id: str = PROVIDER_ID
    provider_api_family: str = PROVIDER_API_FAMILY
    allowed_model_ids: tuple[str, ...] = ALLOWED_MODEL_IDS
    selected_model_id: str = SELECTED_MODEL_ID
    model_family_boundary: str = MODEL_FAMILY_BOUNDARY
    endpoint_scheme: str = ENDPOINT_SCHEME
    endpoint_host: str = ENDPOINT_HOST
    endpoint_port: int = ENDPOINT_PORT
    endpoint_path: str = ENDPOINT_PATH
    http_method: str = HTTP_METHOD
    reasoning_effort: Literal["low"] = REASONING_EFFORT
    resource_limits: LiveProviderResourceLimits = Field(
        default_factory=LiveProviderResourceLimits
    )
    request_policy: LiveProviderRequestPolicy = Field(default_factory=LiveProviderRequestPolicy)
    prohibited_capabilities: LiveProviderProhibitedCapabilities = Field(
        default_factory=LiveProviderProhibitedCapabilities
    )
    authorization_active: bool = True
    authorization_consumed: bool = False
    authorization_expired: bool = False
    authorization_reusable: bool = False
    authorization_fingerprint: str | None = None

    @model_validator(mode="after")
    def authorization_must_be_exact(self) -> Self:
        if (
            self.program_id != PROGRAM_ID
            or self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or self.selected_model_id != SELECTED_MODEL_ID
            or self.provider_id != PROVIDER_ID
            or self.provider_api_family != PROVIDER_API_FAMILY
            or self.endpoint_scheme != ENDPOINT_SCHEME
            or self.endpoint_host != ENDPOINT_HOST
            or self.endpoint_port != ENDPOINT_PORT
            or self.endpoint_path != ENDPOINT_PATH
            or self.http_method != HTTP_METHOD
            or self.reasoning_effort != REASONING_EFFORT
            or self.allowed_model_ids != ALLOWED_MODEL_IDS
            or not self.authorization_active
            or self.authorization_consumed
            or self.authorization_expired
            or self.authorization_reusable
        ):
            raise ValueError("AION-247-AI-0002 authorization mismatch")
        return self


class LiveProviderComponentBinding(LiveProviderFingerprintedModel):
    """Fingerprint-only component lineage binding."""

    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = LIVE_PROVIDER_COMPONENT_BINDING_SCHEMA_VERSION
    binding_id: str = Field(min_length=1)
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    external_cognition_component_fingerprint: str
    existing_model_gateway_component_fingerprint: str
    operator_identity_fingerprint: str
    created_at: datetime
    binding_fingerprint: str | None = None

    _safe_binding_id = field_validator("binding_id")(ensure_safe_identifier)
    _sha_external = field_validator("external_cognition_component_fingerprint")(ensure_sha256)
    _sha_gateway = field_validator("existing_model_gateway_component_fingerprint")(ensure_sha256)
    _sha_operator = field_validator("operator_identity_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)


class LiveProviderModelSelection(LiveProviderFingerprintedModel):
    """Operator-bound provider and model selection."""

    _fingerprint_field: ClassVar[str | None] = "selection_fingerprint"

    schema_version: str = LIVE_PROVIDER_SELECTION_SCHEMA_VERSION
    selection_id: str = Field(min_length=1)
    provider_id: str = PROVIDER_ID
    provider_api_family: str = PROVIDER_API_FAMILY
    selected_model_id: str = SELECTED_MODEL_ID
    allowed_model_ids: tuple[str, ...] = ALLOWED_MODEL_IDS
    model_family_boundary: str = MODEL_FAMILY_BOUNDARY
    model_discovery_performed: bool = False
    created_at: datetime
    selection_fingerprint: str | None = None

    _safe_selection_id = field_validator("selection_id")(ensure_safe_identifier)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def selected_model_must_be_exact(self) -> Self:
        validate_selected_model(self.selected_model_id)
        if self.provider_id != PROVIDER_ID or self.provider_api_family != PROVIDER_API_FAMILY:
            raise ValueError("live-provider selection must use exact OpenAI Responses API")
        if self.model_discovery_performed:
            raise ValueError("model discovery is not authorized")
        return self


class LiveProviderOperatorApproval(LiveProviderFingerprintedModel):
    """Operator approval record without credential or prompt content."""

    _fingerprint_field: ClassVar[str | None] = "approval_fingerprint"

    schema_version: str = LIVE_PROVIDER_OPERATOR_APPROVAL_SCHEMA_VERSION
    approval_id: str = Field(min_length=1)
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    confirmation_text_fingerprint: str
    selected_model_fingerprint: str
    approved: bool = True
    created_at: datetime
    approval_fingerprint: str | None = None

    _safe_approval_id = field_validator("approval_id")(ensure_safe_identifier)
    _sha_confirmation = field_validator("confirmation_text_fingerprint")(ensure_sha256)
    _sha_model = field_validator("selected_model_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)


class LiveProviderCredentialBoundary(LiveProviderFingerprintedModel):
    """Credential source attestation retained without any credential value."""

    _fingerprint_field: ClassVar[str | None] = "boundary_fingerprint"

    schema_version: str = LIVE_PROVIDER_CREDENTIAL_SCHEMA_VERSION
    boundary_id: str = Field(min_length=1)
    credential_source: str = "process_environment"
    credential_name: str = "OPENAI_API_KEY"
    credential_present: bool = False
    credential_value_retained: bool = False
    credential_fingerprint_created: bool = False
    provider_credentials_read: int = 0
    provider_credentials_persisted: int = 0
    authorization_headers_persisted: int = 0
    created_at: datetime
    boundary_fingerprint: str | None = None

    _safe_boundary_id = field_validator("boundary_id")(ensure_safe_identifier)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def credential_boundary_must_not_retain_values(self) -> Self:
        if (
            self.credential_source != "process_environment"
            or self.credential_name != "OPENAI_API_KEY"
            or self.credential_value_retained
            or self.credential_fingerprint_created
            or self.provider_credentials_persisted
            or self.authorization_headers_persisted
            or self.provider_credentials_read not in {0, 1}
        ):
            raise ValueError("credential boundary violated")
        return self


class LiveProviderEndpointPolicy(LiveProviderFingerprintedModel):
    """Exact endpoint and transport policy."""

    _fingerprint_field: ClassVar[str | None] = "endpoint_policy_fingerprint"

    schema_version: str = LIVE_PROVIDER_ENDPOINT_SCHEMA_VERSION
    policy_id: str = Field(min_length=1)
    scheme: str = ENDPOINT_SCHEME
    host: str = ENDPOINT_HOST
    port: int = ENDPOINT_PORT
    path: str = ENDPOINT_PATH
    method: str = HTTP_METHOD
    tls_certificate_verification_required: bool = True
    redirects_allowed: bool = False
    proxy_allowed: bool = False
    model_list_calls_allowed: bool = False
    created_at: datetime
    endpoint_policy_fingerprint: str | None = None

    _safe_policy_id = field_validator("policy_id")(ensure_safe_identifier)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def endpoint_policy_must_be_exact(self) -> Self:
        if (
            self.scheme != ENDPOINT_SCHEME
            or self.host != ENDPOINT_HOST
            or self.port != ENDPOINT_PORT
            or self.path != ENDPOINT_PATH
            or self.method != HTTP_METHOD
            or not self.tls_certificate_verification_required
            or self.redirects_allowed
            or self.proxy_allowed
            or self.model_list_calls_allowed
        ):
            raise ValueError("live-provider endpoint policy mismatch")
        return self


class LiveProviderRequestProjection(LiveProviderFingerprintedModel):
    """Retained request projection with no prompt text."""

    _fingerprint_field: ClassVar[str | None] = "projection_fingerprint"

    schema_version: str = LIVE_PROVIDER_REQUEST_SCHEMA_VERSION
    request_id: str = Field(min_length=1)
    scenario_code: LiveProviderScenarioCode
    provider_id: str = PROVIDER_ID
    provider_api_family: str = PROVIDER_API_FAMILY
    selected_model_id: str = SELECTED_MODEL_ID
    endpoint_policy_fingerprint: str
    request_policy_fingerprint: str
    request_fingerprint: str
    request_byte_count: int = Field(ge=0, le=MAXIMUM_REQUEST_PAYLOAD_BYTES)
    estimated_input_tokens: int = Field(ge=0, le=MAXIMUM_TOTAL_INPUT_TOKENS)
    maximum_output_tokens: int = Field(gt=0, le=MAXIMUM_TOTAL_OUTPUT_TOKENS)
    reasoning_effort: Literal["low"] = REASONING_EFFORT
    store: bool = False
    background: bool = False
    stream: bool = False
    tools_present: bool = False
    files_present: bool = False
    previous_response_id_present: bool = False
    image_input_present: bool = False
    audio_input_present: bool = False
    raw_prompt_retained: bool = False
    created_at: datetime
    projection_fingerprint: str | None = None

    _safe_request_id = field_validator("request_id")(ensure_safe_identifier)
    _sha_endpoint = field_validator("endpoint_policy_fingerprint")(ensure_sha256)
    _sha_policy = field_validator("request_policy_fingerprint")(ensure_sha256)
    _sha_request = field_validator("request_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def request_projection_must_be_closed(self) -> Self:
        if (
            self.provider_id != PROVIDER_ID
            or self.provider_api_family != PROVIDER_API_FAMILY
            or self.selected_model_id != SELECTED_MODEL_ID
            or self.reasoning_effort != REASONING_EFFORT
            or self.store
            or self.background
            or self.stream
            or self.tools_present
            or self.files_present
            or self.previous_response_id_present
            or self.image_input_present
            or self.audio_input_present
            or self.raw_prompt_retained
        ):
            raise ValueError("live-provider request projection violates closed policy")
        return self


class LiveProviderTransportResult(LiveProviderFingerprintedModel):
    """Transport result projection supplied by the uninstalled runner or test fake."""

    _fingerprint_field: ClassVar[str | None] = "transport_result_fingerprint"

    schema_version: str = "aion-live-provider-transport-result/v1"
    transport_result_id: str = Field(min_length=1)
    request_projection_fingerprint: str
    http_status: int = Field(ge=100, le=599)
    provider_status: str = Field(min_length=1)
    provider_response_model_id: str = SELECTED_MODEL_ID
    response_byte_count: int = Field(ge=0, le=MAXIMUM_RESPONSE_PAYLOAD_BYTES)
    response_fingerprint: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    cached_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    completed: bool = True
    tool_call_received: bool = False
    file_or_media_received: bool = False
    transport_result_fingerprint: str | None = None

    _safe_transport_id = field_validator("transport_result_id")(ensure_safe_identifier)
    _sha_request_projection = field_validator("request_projection_fingerprint")(ensure_sha256)
    _sha_response = field_validator("response_fingerprint")(ensure_sha256)

    @model_validator(mode="after")
    def transport_result_must_be_authorized(self) -> Self:
        if (
            self.provider_response_model_id != SELECTED_MODEL_ID
            or not self.completed
            or self.tool_call_received
            or self.file_or_media_received
            or self.total_tokens != self.input_tokens + self.output_tokens
        ):
            raise ValueError("live-provider transport result is outside authorization")
        return self


class LiveProviderResponseProjection(LiveProviderFingerprintedModel):
    """Retained response projection with no raw output text."""

    _fingerprint_field: ClassVar[str | None] = "projection_fingerprint"

    schema_version: str = LIVE_PROVIDER_RESPONSE_SCHEMA_VERSION
    response_projection_id: str = Field(min_length=1)
    request_projection_fingerprint: str
    transport_result_fingerprint: str
    provider_response_model_id: str = SELECTED_MODEL_ID
    response_fingerprint: str
    response_byte_count: int = Field(ge=0, le=MAXIMUM_RESPONSE_PAYLOAD_BYTES)
    estimated_output_tokens: int = Field(ge=0, le=MAXIMUM_TOTAL_OUTPUT_TOKENS)
    completed: bool = True
    raw_response_retained: bool = False
    output_text_retained: bool = False
    tool_call_received: bool = False
    file_or_media_received: bool = False
    local_validation_result: str = "validated"
    created_at: datetime
    projection_fingerprint: str | None = None

    _safe_response_projection_id = field_validator("response_projection_id")(
        ensure_safe_identifier
    )
    _sha_request_projection = field_validator("request_projection_fingerprint")(ensure_sha256)
    _sha_transport_result = field_validator("transport_result_fingerprint")(ensure_sha256)
    _sha_response = field_validator("response_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def response_projection_must_remain_untrusted_and_redacted(self) -> Self:
        if (
            self.provider_response_model_id != SELECTED_MODEL_ID
            or not self.completed
            or self.raw_response_retained
            or self.output_text_retained
            or self.tool_call_received
            or self.file_or_media_received
        ):
            raise ValueError("live-provider response projection violates retention policy")
        return self


class LiveProviderUsageRecord(LiveProviderFingerprintedModel):
    """Usage and latency evidence for one response."""

    _fingerprint_field: ClassVar[str | None] = "usage_fingerprint"

    schema_version: str = LIVE_PROVIDER_USAGE_SCHEMA_VERSION
    usage_id: str = Field(min_length=1)
    request_projection_fingerprint: str
    response_projection_fingerprint: str
    selected_model_id: str = SELECTED_MODEL_ID
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    cached_tokens: int = Field(ge=0)
    request_byte_count: int = Field(ge=0)
    response_byte_count: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    http_status: int = Field(ge=100, le=599)
    provider_status: str = Field(min_length=1)
    created_at: datetime
    usage_fingerprint: str | None = None

    _safe_usage_id = field_validator("usage_id")(ensure_safe_identifier)
    _sha_request_projection = field_validator("request_projection_fingerprint")(ensure_sha256)
    _sha_response_projection = field_validator("response_projection_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def usage_totals_must_match(self) -> Self:
        if self.selected_model_id != SELECTED_MODEL_ID:
            raise ValueError("usage record model mismatch")
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("usage total must equal input plus output")
        return self


class LiveProviderRetentionPolicy(LiveProviderFingerprintedModel):
    """Retention statement for AION-248."""

    _fingerprint_field: ClassVar[str | None] = "retention_fingerprint"

    schema_version: str = LIVE_PROVIDER_RETENTION_SCHEMA_VERSION
    retention_id: str = Field(min_length=1)
    provider_application_state_storage_requested: bool = False
    provider_background_state_requested: bool = False
    provider_streaming_requested: bool = False
    provider_zero_data_retention_claimed: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    credential_value_retained: bool = False
    authorization_header_retained: bool = False
    created_at: datetime
    retention_fingerprint: str | None = None

    _safe_retention_id = field_validator("retention_id")(ensure_safe_identifier)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def retention_must_be_non_persistent(self) -> Self:
        retained_fields = self.model_dump(
            mode="python",
            exclude={
                "schema_version",
                "retention_id",
                "created_at",
                "retention_fingerprint",
            },
        )
        if any(
            bool(value)
            for value in retained_fields.values()
        ):
            raise ValueError("live-provider retention boundary violated")
        return self


class LiveProviderTrustAssessment(LiveProviderFingerprintedModel):
    """Trust classification for a live response."""

    _fingerprint_field: ClassVar[str | None] = "trust_fingerprint"

    schema_version: str = LIVE_PROVIDER_TRUST_SCHEMA_VERSION
    trust_id: str = Field(min_length=1)
    response_projection_fingerprint: str
    trust_class: LiveProviderTrustClass = LiveProviderTrustClass.untrusted_live_provider_output
    provider_output_promoted_to_truth: bool = False
    provider_output_promoted_to_memory: bool = False
    provider_output_promoted_to_knowledge: bool = False
    created_at: datetime
    trust_fingerprint: str | None = None

    _safe_trust_id = field_validator("trust_id")(ensure_safe_identifier)
    _sha_response_projection = field_validator("response_projection_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def trust_must_not_promote_output(self) -> Self:
        if (
            self.provider_output_promoted_to_truth
            or self.provider_output_promoted_to_memory
            or self.provider_output_promoted_to_knowledge
        ):
            raise ValueError("live-provider output promotion is not authorized")
        return self


class LiveProviderUncertaintyProjection(LiveProviderFingerprintedModel):
    """Uncertainty projection for operator review."""

    _fingerprint_field: ClassVar[str | None] = "uncertainty_fingerprint"

    schema_version: str = LIVE_PROVIDER_UNCERTAINTY_SCHEMA_VERSION
    uncertainty_id: str = Field(min_length=1)
    response_projection_fingerprint: str
    label: str = "untrusted_candidate_reasoning_requires_operator_review"
    confidence_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    uncertainty_fingerprint: str | None = None

    _safe_uncertainty_id = field_validator("uncertainty_id")(ensure_safe_identifier)
    _sha_response_projection = field_validator("response_projection_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)


class LiveProviderRedactionRecord(LiveProviderFingerprintedModel):
    """Redaction evidence without protected material."""

    _fingerprint_field: ClassVar[str | None] = "redaction_fingerprint"

    schema_version: str = LIVE_PROVIDER_TRUST_SCHEMA_VERSION
    redaction_id: str = Field(min_length=1)
    request_projection_fingerprint: str
    response_projection_fingerprint: str | None = None
    redacted: bool = True
    protected_material_retained: bool = False
    created_at: datetime
    redaction_fingerprint: str | None = None

    _safe_redaction_id = field_validator("redaction_id")(ensure_safe_identifier)
    _sha_request_projection = field_validator("request_projection_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)

    @field_validator("response_projection_fingerprint")
    @classmethod
    def optional_response_fingerprint(cls, value: str | None) -> str | None:
        if value is not None:
            return ensure_sha256(value)
        return value

    @model_validator(mode="after")
    def redaction_must_be_closed(self) -> Self:
        if not self.redacted or self.protected_material_retained:
            raise ValueError("live-provider redaction boundary violated")
        return self


class LiveProviderReplayRecord(LiveProviderFingerprintedModel):
    """Replay evidence with no additional provider call for exact replay."""

    _fingerprint_field: ClassVar[str | None] = "replay_fingerprint"

    schema_version: str = LIVE_PROVIDER_REPLAY_SCHEMA_VERSION
    replay_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    original_request_fingerprint: str
    replay_request_fingerprint: str
    outcome: LiveProviderReplayOutcome
    additional_provider_call_performed: bool = False
    created_at: datetime
    replay_fingerprint: str | None = None

    _safe_replay_id = field_validator("replay_id")(ensure_safe_identifier)
    _safe_request_id = field_validator("request_id")(ensure_safe_identifier)
    _sha_original = field_validator("original_request_fingerprint")(ensure_sha256)
    _sha_replay = field_validator("replay_request_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def replay_must_not_call_provider(self) -> Self:
        if self.additional_provider_call_performed:
            raise ValueError("exact or changed replay cannot call provider")
        if (
            self.outcome == LiveProviderReplayOutcome.exact_replay_returned
            and self.original_request_fingerprint != self.replay_request_fingerprint
        ):
            raise ValueError("exact replay fingerprint mismatch")
        if (
            self.outcome == LiveProviderReplayOutcome.changed_replay_rejected
            and self.original_request_fingerprint == self.replay_request_fingerprint
        ):
            raise ValueError("changed replay must differ from original")
        return self


class LiveProviderAuditRecord(LiveProviderFingerprintedModel):
    """Append-only audit event projection."""

    _fingerprint_field: ClassVar[str | None] = "audit_fingerprint"

    schema_version: str = LIVE_PROVIDER_AUDIT_SCHEMA_VERSION
    audit_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    outcome: LiveProviderAuditOutcome
    subject_fingerprint: str = ZERO_FINGERPRINT
    previous_audit_fingerprint: str = ZERO_FINGERPRINT
    created_at: datetime
    audit_fingerprint: str | None = None

    _safe_audit_id = field_validator("audit_id")(ensure_safe_identifier)
    _safe_event_type = field_validator("event_type")(ensure_safe_identifier)
    _sha_subject = field_validator("subject_fingerprint")(ensure_sha256)
    _sha_previous = field_validator("previous_audit_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)


class LiveProviderObservabilitySnapshot(LiveProviderFingerprintedModel):
    """Counters and latency evidence for the completed pilot."""

    _fingerprint_field: ClassVar[str | None] = "observability_fingerprint"

    schema_version: str = LIVE_PROVIDER_OBSERVABILITY_SCHEMA_VERSION
    snapshot_id: str = Field(min_length=1)
    counters: dict[str, int]
    latency_summary: dict[str, int]
    created_at: datetime
    observability_fingerprint: str | None = None

    _safe_snapshot_id = field_validator("snapshot_id")(ensure_safe_identifier)
    _utc_created = field_validator("created_at")(ensure_utc)

    @field_validator("counters", "latency_summary")
    @classmethod
    def counters_must_be_non_negative(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 for count in value.values()):
            raise ValueError("counters must be non-negative")
        return dict(sorted(value.items()))


class LiveProviderIntegrityReport(LiveProviderFingerprintedModel):
    """Integrity report for the source/evidence boundary."""

    _fingerprint_field: ClassVar[str | None] = "integrity_fingerprint"

    schema_version: str = LIVE_PROVIDER_INTEGRITY_SCHEMA_VERSION
    integrity_id: str = Field(min_length=1)
    status: LiveProviderIntegrityStatus
    authorization_fingerprint: str
    selected_model_fingerprint: str
    endpoint_policy_fingerprint: str
    transport_policy_fingerprint: str
    observability_fingerprint: str
    evidence_contains_raw_content: bool = False
    evidence_contains_credentials: bool = False
    post_pilot_provider_runtime_active: bool = False
    post_pilot_network_runtime_active: bool = False
    created_at: datetime
    integrity_fingerprint: str | None = None

    _safe_integrity_id = field_validator("integrity_id")(ensure_safe_identifier)
    _sha_auth = field_validator("authorization_fingerprint")(ensure_sha256)
    _sha_model = field_validator("selected_model_fingerprint")(ensure_sha256)
    _sha_endpoint = field_validator("endpoint_policy_fingerprint")(ensure_sha256)
    _sha_transport = field_validator("transport_policy_fingerprint")(ensure_sha256)
    _sha_observability = field_validator("observability_fingerprint")(ensure_sha256)
    _utc_created = field_validator("created_at")(ensure_utc)

    @model_validator(mode="after")
    def integrity_must_pass_without_runtime(self) -> Self:
        if (
            self.status != LiveProviderIntegrityStatus.passed
            or self.evidence_contains_raw_content
            or self.evidence_contains_credentials
            or self.post_pilot_provider_runtime_active
            or self.post_pilot_network_runtime_active
        ):
            raise ValueError("live-provider integrity report failed")
        return self


class LiveProviderEvidenceBundle(LiveProviderBaseModel):
    """Committed redacted pilot evidence bundle."""

    schema_version: str = LIVE_PROVIDER_EVIDENCE_SCHEMA_VERSION
    pilot_id: str = PILOT_ID
    program_id: str = PROGRAM_ID
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    mode: str = "operator_invoked_single_openai_responses_api"
    implementation_commit: str
    provider_id: str = PROVIDER_ID
    provider_api_family: str = PROVIDER_API_FAMILY
    selected_model_id: str = SELECTED_MODEL_ID
    selected_model_fingerprint: str
    endpoint_policy_fingerprint: str
    transport_policy_fingerprint: str
    operator_approval_fingerprint: str
    external_cognition_component_binding_fingerprint: str
    existing_model_gateway_component_binding_fingerprint: str
    credential_source: str = "process_environment"
    credential_value_retained: bool = False
    credential_fingerprint_created: bool = False
    provider_application_state_storage_requested: bool = False
    provider_background_state_requested: bool = False
    provider_streaming_requested: bool = False
    provider_zero_data_retention_claimed: bool = False
    request_projection_fingerprints: tuple[str, ...]
    response_projection_fingerprints: tuple[str, ...]
    usage_record_fingerprints: tuple[str, ...]
    trust_assessment_fingerprints: tuple[str, ...]
    uncertainty_projection_fingerprints: tuple[str, ...]
    audit_chain_head: str
    observability_fingerprint: str
    integrity_report_fingerprint: str
    counters: dict[str, int]
    zero_counters: dict[str, int]
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    latency_summary: dict[str, int]
    integrity_passed: bool = True
    temporary_files_retained: int = 0
    credential_references_released: bool = True
    redacted: bool = True
    memory_effect: bool = False
    tool_effect: bool = False
    production_effect: bool = False
    post_pilot_provider_runtime_active: bool = False
    post_pilot_network_runtime_active: bool = False
    report_fingerprint: str | None = None

    _sha_model = field_validator("selected_model_fingerprint")(ensure_sha256)
    _sha_endpoint = field_validator("endpoint_policy_fingerprint")(ensure_sha256)
    _sha_transport = field_validator("transport_policy_fingerprint")(ensure_sha256)
    _sha_approval = field_validator("operator_approval_fingerprint")(ensure_sha256)
    _sha_external = field_validator("external_cognition_component_binding_fingerprint")(
        ensure_sha256
    )
    _sha_gateway = field_validator("existing_model_gateway_component_binding_fingerprint")(
        ensure_sha256
    )
    _sha_audit = field_validator("audit_chain_head")(ensure_sha256)
    _sha_observability = field_validator("observability_fingerprint")(ensure_sha256)
    _sha_integrity = field_validator("integrity_report_fingerprint")(ensure_sha256)

    @field_validator(
        "request_projection_fingerprints",
        "response_projection_fingerprints",
        "usage_record_fingerprints",
        "trust_assessment_fingerprints",
        "uncertainty_projection_fingerprints",
    )
    @classmethod
    def fingerprint_tuple_must_have_six(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != MAXIMUM_LIVE_PROVIDER_CALLS:
            raise ValueError("live-provider evidence must contain six fingerprints")
        for item in value:
            ensure_sha256(item)
        return value

    @model_validator(mode="after")
    def evidence_bundle_must_be_exact(self) -> Self:
        if (
            self.pilot_id != PILOT_ID
            or self.program_id != PROGRAM_ID
            or self.authorization_id != AUTHORIZATION_TRANSACTION_ID
            or self.provider_id != PROVIDER_ID
            or self.provider_api_family != PROVIDER_API_FAMILY
            or self.selected_model_id != SELECTED_MODEL_ID
            or self.credential_source != "process_environment"
            or self.credential_value_retained
            or self.credential_fingerprint_created
            or self.provider_application_state_storage_requested
            or self.provider_background_state_requested
            or self.provider_streaming_requested
            or self.provider_zero_data_retention_claimed
            or self.total_tokens != self.total_input_tokens + self.total_output_tokens
            or not self.integrity_passed
            or self.temporary_files_retained != 0
            or not self.credential_references_released
            or not self.redacted
            or self.memory_effect
            or self.tool_effect
            or self.production_effect
            or self.post_pilot_provider_runtime_active
            or self.post_pilot_network_runtime_active
        ):
            raise ValueError("live-provider evidence violates AION-248 boundaries")
        expected = evidence_report_fingerprint(self.model_dump(mode="json"))
        if self.report_fingerprint is None:
            object.__setattr__(self, "report_fingerprint", expected)
        elif self.report_fingerprint != expected:
            raise ValueError("live-provider evidence report fingerprint mismatch")
        return self


def validate_selected_model(model_id: str) -> str:
    """Return an approved model ID or fail closed."""

    if model_id != SELECTED_MODEL_ID:
        raise ValueError("selected model must be the exact AION-248 model")
    if model_id not in ALLOWED_MODEL_IDS:
        raise ValueError("selected model is outside the allowed GPT-5.6 set")
    return model_id


def validate_model_candidate(model_id: str) -> str:
    """Validate the contract-level GPT-5.6 allowlist."""

    if model_id not in ALLOWED_MODEL_IDS:
        raise ValueError("model candidate is not an exact approved GPT-5.6 model ID")
    return model_id


def validate_endpoint(*, scheme: str, host: str, path: str, method: str) -> None:
    """Fail closed unless the endpoint is exactly the authorized endpoint."""

    if (
        scheme != ENDPOINT_SCHEME
        or host != ENDPOINT_HOST
        or path != ENDPOINT_PATH
        or method != HTTP_METHOD
    ):
        raise ValueError("unauthorized live-provider endpoint")


def validate_responses_payload(payload: Mapping[str, object]) -> None:
    """Validate an OpenAI Responses API payload before transport."""

    required = {"model", "input", "store", "background", "stream", "reasoning"}
    missing = required.difference(payload)
    if missing:
        raise ValueError("live-provider payload missing required policy fields")
    if payload.get("model") != SELECTED_MODEL_ID:
        raise ValueError("live-provider payload model mismatch")
    if payload.get("store") is not False:
        raise ValueError("live-provider payload must set store false")
    if payload.get("background") is not False:
        raise ValueError("live-provider payload must set background false")
    if payload.get("stream") is not False:
        raise ValueError("live-provider payload must set stream false")
    reasoning = payload.get("reasoning")
    if not isinstance(reasoning, Mapping) or reasoning.get("effort") != REASONING_EFFORT:
        raise ValueError("live-provider payload reasoning effort mismatch")
    forbidden = {
        "tools",
        "tool_choice",
        "files",
        "file_ids",
        "previous_response_id",
        "image",
        "images",
        "audio",
    }
    for key in forbidden:
        if key in payload:
            raise ValueError("live-provider payload contains forbidden field")
    assert_no_protected_material(
        {
            key: value
            for key, value in payload.items()
            if key not in {"input"}
        }
    )


def evidence_report_fingerprint(payload: Mapping[str, object]) -> str:
    """Calculate the committed evidence fingerprint."""

    clean = dict(payload)
    clean.pop("report_fingerprint", None)
    return live_provider_fingerprint(clean)


def default_zero_counters() -> dict[str, int]:
    """Return all prohibited counters at zero."""

    return dict.fromkeys(sorted(ZERO_COUNTER_TARGETS), 0)


def default_required_counters() -> dict[str, int]:
    """Return required counter targets."""

    return dict(sorted(REQUIRED_COUNTER_TARGETS.items()))


def _reject_non_finite_numbers(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are not allowed")
    if isinstance(value, Mapping):
        for nested in value.values():
            _reject_non_finite_numbers(nested)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for nested in value:
            _reject_non_finite_numbers(nested)


def _reject_protected_material(value: object) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if any(part in normalized_key for part in PROTECTED_KEY_PARTS):
                if nested not in (False, 0, None):
                    raise ValueError("protected live-provider material is not retainable")
                continue
            _reject_protected_material(nested)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for item in value:
            _reject_protected_material(item)
    elif isinstance(value, str):
        normalized_value = value.lower()
        if any(marker in normalized_value for marker in PROTECTED_VALUE_MARKERS):
            raise ValueError("protected live-provider material is not retainable")
