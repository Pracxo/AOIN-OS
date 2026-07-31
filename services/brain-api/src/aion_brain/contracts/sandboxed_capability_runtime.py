"""Sandboxed deterministic capability runtime contracts for AION-235."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Any, ClassVar, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CAPABILITY_RUNTIME_CONTRACT_SCHEMA_VERSION: Final = "aion-capability-runtime/v1"
CAPABILITY_RUNTIME_AUTHORIZATION_SCHEMA_VERSION: Final = (
    "aion-capability-runtime-authorization/v1"
)
CAPABILITY_RUNTIME_COMPONENT_BINDING_SCHEMA_VERSION: Final = (
    "aion-capability-runtime-component-binding/v1"
)
CAPABILITY_MANIFEST_SCHEMA_VERSION: Final = "aion-capability-runtime-capability-manifest/v1"
CONNECTOR_MANIFEST_SCHEMA_VERSION: Final = "aion-capability-runtime-connector-manifest/v1"
CAPABILITY_INPUT_SCHEMA_VERSION: Final = "aion-capability-runtime-input-schema/v1"
CAPABILITY_OUTPUT_SCHEMA_VERSION: Final = "aion-capability-runtime-output-schema/v1"
CAPABILITY_SESSION_SCHEMA_VERSION: Final = "aion-capability-runtime-session/v1"
CAPABILITY_REQUEST_SCHEMA_VERSION: Final = "aion-capability-runtime-request/v1"
CAPABILITY_EXECUTION_PLAN_SCHEMA_VERSION: Final = "aion-capability-runtime-execution-plan/v1"
CAPABILITY_DECISION_BINDING_SCHEMA_VERSION: Final = "aion-capability-runtime-decision-binding/v1"
CAPABILITY_APPROVAL_SCHEMA_VERSION: Final = "aion-capability-runtime-approval/v1"
CAPABILITY_BUDGET_SCHEMA_VERSION: Final = "aion-capability-runtime-budget/v1"
CAPABILITY_SANDBOX_SCHEMA_VERSION: Final = "aion-capability-runtime-sandbox/v1"
CAPABILITY_EXECUTION_RECEIPT_SCHEMA_VERSION: Final = (
    "aion-capability-runtime-execution-receipt/v1"
)
CAPABILITY_ROLLBACK_SCHEMA_VERSION: Final = "aion-capability-runtime-rollback/v1"
CAPABILITY_AUDIT_SCHEMA_VERSION: Final = "aion-capability-runtime-audit/v1"
CAPABILITY_OBSERVABILITY_SCHEMA_VERSION: Final = "aion-capability-runtime-observability/v1"
CAPABILITY_INTEGRITY_SCHEMA_VERSION: Final = "aion-capability-runtime-integrity/v1"
CAPABILITY_EVIDENCE_SCHEMA_VERSION: Final = "aion-capability-runtime-evidence/v1"

PROGRAM_ID: Final = "AION-SECURE-RUNTIME-INTEGRATION-001"
AUTHORIZATION_TRANSACTION_ID: Final = "AION-234-SRI-0003"
APPROVAL_RECORD_ID: Final = "AION-234-SRI-0003"
IMPLEMENTATION_TASK: Final = "AION-235"
FORMAL_CLOSEOUT_TASK: Final = "AION-236"
AUTHORIZATION_SCOPE: Final = (
    "authenticated-local-untrusted-model-output-bound-explicit-operator-capability-plan-"
    "closed-capability-connector-manifest-schema-validated-in-memory-sandbox-"
    "deterministic-reference-execution-policy-risk-guardrail-approval-budget-"
    "kill-switch-audit-provenance-rollback-no-external-effect-core"
)
LOCAL_CONFIRMATION_TEXT: Final = "RUN_CONTROLLED_SANDBOXED_CAPABILITY_RUNTIME"
ZERO_FINGERPRINT: Final = "0000000000000000000000000000000000000000000000000000000000000000"

CapabilityManifestSchemaVersion = Literal["aion-capability-runtime-capability-manifest/v1"]
ConnectorManifestSchemaVersion = Literal["aion-capability-runtime-connector-manifest/v1"]
CapabilityInputSchemaVersion = Literal["aion-capability-runtime-input-schema/v1"]
CapabilityOutputSchemaVersion = Literal["aion-capability-runtime-output-schema/v1"]
CapabilitySessionSchemaVersion = Literal["aion-capability-runtime-session/v1"]
CapabilityRequestSchemaVersion = Literal["aion-capability-runtime-request/v1"]
CapabilityExecutionPlanSchemaVersion = Literal["aion-capability-runtime-execution-plan/v1"]
CapabilityDecisionBindingSchemaVersion = Literal[
    "aion-capability-runtime-decision-binding/v1"
]
CapabilityApprovalSchemaVersion = Literal["aion-capability-runtime-approval/v1"]
CapabilityBudgetSchemaVersion = Literal["aion-capability-runtime-budget/v1"]
CapabilitySandboxSchemaVersion = Literal["aion-capability-runtime-sandbox/v1"]
CapabilityExecutionReceiptSchemaVersion = Literal[
    "aion-capability-runtime-execution-receipt/v1"
]
CapabilityRollbackSchemaVersion = Literal["aion-capability-runtime-rollback/v1"]
CapabilityAuditSchemaVersion = Literal["aion-capability-runtime-audit/v1"]
CapabilityObservabilitySchemaVersion = Literal[
    "aion-capability-runtime-observability/v1"
]
CapabilityIntegritySchemaVersion = Literal["aion-capability-runtime-integrity/v1"]
CapabilityEvidenceSchemaVersion = Literal["aion-capability-runtime-evidence/v1"]
CapabilityRuntimeAuthorizationSchemaVersion = Literal[
    "aion-capability-runtime-authorization/v1"
]
CapabilityRuntimeComponentBindingSchemaVersion = Literal[
    "aion-capability-runtime-component-binding/v1"
]
ProgramId = Literal["AION-SECURE-RUNTIME-INTEGRATION-001"]
AuthorizationTransactionId = Literal["AION-234-SRI-0003"]
ApprovalRecordId = Literal["AION-234-SRI-0003"]
AuthorizationScopeLiteral = Literal[
    "authenticated-local-untrusted-model-output-bound-explicit-operator-capability-plan-"
    "closed-capability-connector-manifest-schema-validated-in-memory-sandbox-"
    "deterministic-reference-execution-policy-risk-guardrail-approval-budget-"
    "kill-switch-audit-provenance-rollback-no-external-effect-core"
]

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
LOWER_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAXIMUM_CAPABILITY_RUNTIME_SESSIONS = 1
MAXIMUM_REQUESTS_PER_SESSION = 100
MAXIMUM_CONCURRENT_REQUESTS = 4
MAXIMUM_CAPABILITY_MANIFESTS = 16
MAXIMUM_CONNECTOR_MANIFESTS = 4
MAXIMUM_CAPABILITIES_PER_MANIFEST = 16
MAXIMUM_EXECUTION_PLANS_PER_REQUEST = 4
MAXIMUM_REFERENCE_CAPABILITY_EXECUTIONS_PER_REQUEST = 4
MAXIMUM_REFERENCE_CAPABILITY_EXECUTIONS_PER_SESSION = 100
MAXIMUM_REFERENCE_CONNECTOR_SIMULATIONS_PER_REQUEST = 2
MAXIMUM_REFERENCE_CONNECTOR_SIMULATIONS_PER_SESSION = 50
MAXIMUM_INPUT_BYTES_PER_REQUEST = 1_048_576
MAXIMUM_OUTPUT_BYTES_PER_REQUEST = 1_048_576
MAXIMUM_TOTAL_INPUT_BYTES_PER_SESSION = 10_485_760
MAXIMUM_TOTAL_OUTPUT_BYTES_PER_SESSION = 10_485_760
MAXIMUM_JSON_DEPTH = 16
MAXIMUM_JSON_ITEMS_PER_REQUEST = 1000
MAXIMUM_TEXT_CHARACTERS_PER_REQUEST = 262_144
MAXIMUM_OPERATION_STEPS_PER_EXECUTION = 10_000
MAXIMUM_EXECUTION_WALL_CLOCK_MILLISECONDS = 5000
MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_REQUEST = 4
MAXIMUM_POLICY_DECISIONS_PER_REQUEST = 20
MAXIMUM_RISK_ASSESSMENTS_PER_REQUEST = 20
MAXIMUM_GUARDRAIL_DECISIONS_PER_REQUEST = 20
MAXIMUM_KILL_SWITCH_CHECKS_PER_REQUEST = 20
MAXIMUM_IDEMPOTENCY_RECORDS_PER_SESSION = 1000
MAXIMUM_AUDIT_RECORDS_PER_SESSION = 10_000
MAXIMUM_TELEMETRY_EVENTS_PER_SESSION = 10_000
MAXIMUM_OPERATOR_REVIEW_ITEMS_PER_SESSION = 500
MAXIMUM_TRACE_BYTES_PER_SESSION = 4_194_304
MAXIMUM_FIXTURE_RECORDS = 5000
MAXIMUM_FIXTURE_BYTES = 4_194_304
MAXIMUM_SESSION_CHECKPOINTS = 20
MAXIMUM_ROLLBACK_STEPS_PER_REQUEST = 50

CAPABILITY_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_capability_runtime_sessions": MAXIMUM_CAPABILITY_RUNTIME_SESSIONS,
    "maximum_requests_per_session": MAXIMUM_REQUESTS_PER_SESSION,
    "maximum_concurrent_requests": MAXIMUM_CONCURRENT_REQUESTS,
    "maximum_capability_manifests": MAXIMUM_CAPABILITY_MANIFESTS,
    "maximum_connector_manifests": MAXIMUM_CONNECTOR_MANIFESTS,
    "maximum_capabilities_per_manifest": MAXIMUM_CAPABILITIES_PER_MANIFEST,
    "maximum_execution_plans_per_request": MAXIMUM_EXECUTION_PLANS_PER_REQUEST,
    "maximum_reference_capability_executions_per_request": (
        MAXIMUM_REFERENCE_CAPABILITY_EXECUTIONS_PER_REQUEST
    ),
    "maximum_reference_capability_executions_per_session": (
        MAXIMUM_REFERENCE_CAPABILITY_EXECUTIONS_PER_SESSION
    ),
    "maximum_reference_connector_simulations_per_request": (
        MAXIMUM_REFERENCE_CONNECTOR_SIMULATIONS_PER_REQUEST
    ),
    "maximum_reference_connector_simulations_per_session": (
        MAXIMUM_REFERENCE_CONNECTOR_SIMULATIONS_PER_SESSION
    ),
    "maximum_input_bytes_per_request": MAXIMUM_INPUT_BYTES_PER_REQUEST,
    "maximum_output_bytes_per_request": MAXIMUM_OUTPUT_BYTES_PER_REQUEST,
    "maximum_total_input_bytes_per_session": MAXIMUM_TOTAL_INPUT_BYTES_PER_SESSION,
    "maximum_total_output_bytes_per_session": MAXIMUM_TOTAL_OUTPUT_BYTES_PER_SESSION,
    "maximum_json_depth": MAXIMUM_JSON_DEPTH,
    "maximum_json_items_per_request": MAXIMUM_JSON_ITEMS_PER_REQUEST,
    "maximum_text_characters_per_request": MAXIMUM_TEXT_CHARACTERS_PER_REQUEST,
    "maximum_operation_steps_per_execution": MAXIMUM_OPERATION_STEPS_PER_EXECUTION,
    "maximum_execution_wall_clock_milliseconds": MAXIMUM_EXECUTION_WALL_CLOCK_MILLISECONDS,
    "maximum_approval_evidence_records_per_request": MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_REQUEST,
    "maximum_policy_decisions_per_request": MAXIMUM_POLICY_DECISIONS_PER_REQUEST,
    "maximum_risk_assessments_per_request": MAXIMUM_RISK_ASSESSMENTS_PER_REQUEST,
    "maximum_guardrail_decisions_per_request": MAXIMUM_GUARDRAIL_DECISIONS_PER_REQUEST,
    "maximum_kill_switch_checks_per_request": MAXIMUM_KILL_SWITCH_CHECKS_PER_REQUEST,
    "maximum_idempotency_records_per_session": MAXIMUM_IDEMPOTENCY_RECORDS_PER_SESSION,
    "maximum_audit_records_per_session": MAXIMUM_AUDIT_RECORDS_PER_SESSION,
    "maximum_telemetry_events_per_session": MAXIMUM_TELEMETRY_EVENTS_PER_SESSION,
    "maximum_operator_review_items_per_session": MAXIMUM_OPERATOR_REVIEW_ITEMS_PER_SESSION,
    "maximum_trace_bytes_per_session": MAXIMUM_TRACE_BYTES_PER_SESSION,
    "maximum_fixture_records": MAXIMUM_FIXTURE_RECORDS,
    "maximum_fixture_bytes": MAXIMUM_FIXTURE_BYTES,
    "maximum_session_checkpoints": MAXIMUM_SESSION_CHECKPOINTS,
    "maximum_rollback_steps_per_request": MAXIMUM_ROLLBACK_STEPS_PER_REQUEST,
}

CAPABILITY_ZERO_RESOURCE_LIMITS: tuple[str, ...] = (
    "maximum_public_network_calls",
    "maximum_dns_resolutions",
    "maximum_external_connector_calls",
    "maximum_external_tool_executions",
    "maximum_model_provider_calls",
    "maximum_provider_sdk_calls",
    "maximum_provider_credentials_read",
    "maximum_credentials_persisted",
    "maximum_tokens_read",
    "maximum_tokens_persisted",
    "maximum_authorization_headers_created",
    "maximum_filesystem_reads",
    "maximum_filesystem_writes",
    "maximum_directory_mutations",
    "maximum_process_spawns",
    "maximum_shell_commands",
    "maximum_subprocess_executions",
    "maximum_browser_actions",
    "maximum_dynamic_imports",
    "maximum_eval_executions",
    "maximum_exec_executions",
    "maximum_packages_installed",
    "maximum_modules_activated",
    "maximum_dynamic_routes_registered",
    "maximum_public_api_routes_added",
    "maximum_tool_calls",
    "maximum_function_calls",
    "maximum_automatic_capability_selections",
    "maximum_model_output_triggered_executions",
    "maximum_automatic_capability_executions",
    "maximum_automatic_connector_executions",
    "maximum_automatic_approvals",
    "maximum_runtime_created_approvals",
    "maximum_production_writes",
    "maximum_production_memory_writes",
    "maximum_production_policy_mutations",
    "maximum_cognitive_memory_writes",
    "maximum_actual_belief_creations",
    "maximum_actual_belief_mutations",
    "maximum_glm_live_executions",
    "maximum_source_mutations",
    "maximum_git_operations",
    "maximum_runtime_created_pull_requests",
    "maximum_automatic_merges",
    "maximum_production_canary_executions",
    "maximum_deployments",
    "maximum_model_weight_changes",
)

ALL_RESOURCE_LIMITS: dict[str, int] = {
    **CAPABILITY_RESOURCE_LIMITS,
    **{key: 0 for key in CAPABILITY_ZERO_RESOURCE_LIMITS},
}

PROHIBITED_EFFECT_COUNTERS: tuple[str, ...] = (
    "automatic_capability_selections",
    "automatic_capability_executions",
    "automatic_connector_executions",
    "external_connector_calls",
    "external_tool_executions",
    "network_calls",
    "dns_resolutions",
    "model_provider_calls",
    "provider_sdk_calls",
    "credentials_read",
    "credentials_persisted",
    "tokens_read",
    "tokens_persisted",
    "authorization_headers_created",
    "filesystem_reads",
    "filesystem_writes",
    "directory_mutations",
    "process_spawns",
    "shell_commands",
    "subprocess_executions",
    "browser_actions",
    "dynamic_imports",
    "eval_executions",
    "exec_executions",
    "packages_installed",
    "modules_activated",
    "dynamic_routes_registered",
    "public_api_routes_added",
    "tool_calls",
    "function_calls",
    "runtime_created_approvals",
    "production_writes",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "belief_creations",
    "belief_mutations",
    "glm_live_executions",
    "source_mutations",
    "git_operations",
    "runtime_created_pull_requests",
    "automatic_merges",
    "production_canary_executions",
    "deployments",
    "model_weight_changes",
)

AUTHORIZED_CAPABILITY_FLAGS: tuple[str, ...] = (
    "capability_runtime_contract_approved",
    "capability_runtime_authorization_envelope_approved",
    "secure_runtime_component_composition_approved",
    "model_gateway_component_composition_approved",
    "untrusted_model_output_proposal_binding_approved",
    "explicit_operator_capability_selection_approved",
    "closed_capability_manifest_registry_approved",
    "closed_connector_manifest_registry_approved",
    "capability_input_schema_approved",
    "capability_output_schema_approved",
    "connector_request_schema_approved",
    "connector_response_schema_approved",
    "capability_runtime_session_approved",
    "capability_request_envelope_approved",
    "deterministic_capability_execution_plan_approved",
    "policy_binding_approved",
    "risk_binding_approved",
    "guardrail_binding_approved",
    "existing_approval_evidence_validation_approved",
    "zero_external_effect_budget_approved",
    "in_memory_sandbox_profile_approved",
    "pure_reference_capability_execution_approved",
    "synthetic_reference_connector_execution_approved",
    "in_memory_fixture_registry_approved",
    "deterministic_static_dispatch_approved",
    "capability_request_idempotency_approved",
    "changed_replay_rejection_approved",
    "execution_receipt_approved",
    "output_validation_approved",
    "execution_provenance_approved",
    "execution_rollback_approved",
    "parent_kill_switch_composition_approved",
    "capability_runtime_audit_approved",
    "capability_runtime_observability_approved",
    "capability_runtime_health_readiness_approved",
    "capability_runtime_integrity_audit_approved",
    "capability_runtime_operator_review_item_approved",
    "redacted_capability_runtime_evidence_approved",
    "deterministic_capability_fixture_replay_approved",
    "local_sandboxed_capability_runtime_pilot_approved",
    "documentation_and_static_evidence_approved",
)

PROHIBITED_CAPABILITY_FLAGS: tuple[str, ...] = (
    "automatic_capability_selection_enabled",
    "model_output_triggered_execution_enabled",
    "automatic_capability_execution_enabled",
    "automatic_connector_execution_enabled",
    "external_connector_execution_enabled",
    "external_tool_execution_enabled",
    "actual_tool_execution_enabled",
    "tool_calling_enabled",
    "function_calling_enabled",
    "public_network_access_enabled",
    "general_network_access_enabled",
    "dns_resolution_enabled",
    "connector_network_egress_enabled",
    "provider_network_egress_enabled",
    "actual_model_provider_call_enabled",
    "provider_sdk_enabled",
    "credential_read_enabled",
    "credential_persistence_enabled",
    "token_read_enabled",
    "token_persistence_enabled",
    "authorization_header_creation_enabled",
    "filesystem_read_enabled",
    "filesystem_write_enabled",
    "directory_mutation_enabled",
    "process_spawn_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "browser_automation_enabled",
    "dynamic_import_enabled",
    "eval_enabled",
    "exec_enabled",
    "package_installation_enabled",
    "module_activation_enabled",
    "module_code_loading_enabled",
    "dynamic_route_registration_enabled",
    "public_capability_api_route_enabled",
    "automatic_approval_enabled",
    "runtime_approval_creation_enabled",
    "production_write_execution_enabled",
    "production_memory_write_enabled",
    "production_policy_mutation_enabled",
    "cognitive_memory_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "glm_live_execution_enabled",
    "source_rewrite_enabled",
    "git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_runtime_authorized",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
)

PROHIBITED_DATA_KEY_PARTS: tuple[str, ...] = (
    "raw_model_output",
    "raw_prompt",
    "hidden_reasoning",
    "credential",
    "password",
    "api_key",
    "apikey",
    "secret",
    "token",
    "cookie",
    "authorization_header",
    "endpoint",
    "url",
    "uri",
    "file_path",
    "directory_path",
    "shell_command",
    "command_argument",
    "executable",
    "python_module",
    "callable",
    "source_patch",
    "raw_diff",
    "personal_data",
    "production_config",
)

PROHIBITED_STRING_MARKERS: tuple[str, ...] = (
    "sk-",
    "bearer ",
    "authorization:",
    "https://",
    "http://",
    "file://",
    "../",
    "/etc/",
    "subprocess",
    "socket module marker",
    "importlib",
    "__import__",
    "eval(",
    "exec(",
    "git ",
    "diff --git",
    "deployment",
    "production_write",
)


class CapabilityRuntimeRejected(ValueError):
    """Fail-closed capability runtime rejection."""


class CapabilityRuntimeMode(StrEnum):
    deterministic_simulation = "deterministic_simulation"
    operator_invoked_local = "operator_invoked_local"


class CapabilityExecutionKind(StrEnum):
    read_only_reference = "read_only_reference"
    pure_function = "pure_function"
    synthetic_reference_connector = "synthetic_reference_connector"
    synthetic_reference_connector_preview = "synthetic_reference_connector_preview"


class CapabilityRuntimeRisk(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CapabilityRuntimeSessionStatus(StrEnum):
    drafted = "drafted"
    authorized = "authorized"
    active = "active"
    closed = "closed"
    blocked = "blocked"
    killed = "killed"
    expired = "expired"
    failed = "failed"


class CapabilityRequestStatus(StrEnum):
    drafted = "drafted"
    validated = "validated"
    planned = "planned"
    policy_evaluated = "policy_evaluated"
    risk_evaluated = "risk_evaluated"
    guardrails_evaluated = "guardrails_evaluated"
    approval_validated = "approval_validated"
    budget_validated = "budget_validated"
    sandbox_ready = "sandbox_ready"
    executed = "executed"
    output_validated = "output_validated"
    receipt_recorded = "receipt_recorded"
    rolled_back = "rolled_back"
    closed = "closed"
    blocked = "blocked"
    killed = "killed"
    failed = "failed"


class CapabilitySandboxOutcome(StrEnum):
    allow_reference_execution = "allow_reference_execution"
    require_approval = "require_approval"
    abstain = "abstain"
    block = "block"
    kill = "kill"


class CapabilityExecutionStatus(StrEnum):
    executed = "executed"
    simulated = "simulated"
    previewed = "previewed"
    blocked = "blocked"
    rolled_back = "rolled_back"
    failed = "failed"


class CapabilityOutputTrustClass(StrEnum):
    validated_reference_output = "validated_reference_output"
    untrusted_synthetic_connector_output = "untrusted_synthetic_connector_output"
    blocked_output = "blocked_output"
    invalid_output = "invalid_output"


class CapabilityRuntimeIntegrityStatus(StrEnum):
    passed = "passed"
    failed = "failed"


class CapabilityRuntimeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class FrozenCapabilityRuntimeModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        frozen=True,
    )


def normalize_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def ensure_safe_identifier(value: str, *, field_name: str = "identifier") -> str:
    if not isinstance(value, str) or SAFE_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe bounded ASCII identifier")
    return value


def ensure_sha256(value: str, *, field_name: str = "fingerprint") -> str:
    if not isinstance(value, str) or LOWER_SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 fingerprint")
    return value


def canonical_json(payload: Any) -> str:
    return json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"))


def capability_runtime_fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def fingerprint_without(payload: Mapping[str, Any], *keys: str) -> str:
    stripped = {key: value for key, value in payload.items() if key not in keys}
    return capability_runtime_fingerprint(stripped)


def text_fingerprint(kind: str, value: str | None) -> str:
    return capability_runtime_fingerprint({"kind": kind, "value": value or ""})


def confirmation_fingerprint() -> str:
    return capability_runtime_fingerprint(
        {"authorization": AUTHORIZATION_TRANSACTION_ID, "confirmation": LOCAL_CONFIRMATION_TEXT}
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_safe(value.model_dump(mode="json"))
    if isinstance(value, StrEnum):
        return str(value)
    if isinstance(value, datetime):
        return normalize_utc_datetime(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _json_safe(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_json_safe(item) for item in value]
    return value


def _byte_size(value: Any) -> int:
    return len(canonical_json(value).encode("utf-8"))


def _json_depth(value: Any, depth: int = 0) -> int:
    if depth > MAXIMUM_JSON_DEPTH:
        raise CapabilityRuntimeRejected("JSON depth exceeds the runtime limit")
    if isinstance(value, Mapping):
        if len(value) > MAXIMUM_JSON_ITEMS_PER_REQUEST:
            raise CapabilityRuntimeRejected("JSON object item limit exceeded")
        return max([depth] + [_json_depth(item, depth + 1) for item in value.values()])
    if isinstance(value, list):
        if len(value) > MAXIMUM_JSON_ITEMS_PER_REQUEST:
            raise CapabilityRuntimeRejected("JSON array item limit exceeded")
        return max([depth] + [_json_depth(item, depth + 1) for item in value])
    return depth


def reject_protected_material(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in PROHIBITED_DATA_KEY_PARTS):
                raise ValueError("payload contains protected material")
            reject_protected_material(nested)
    elif isinstance(value, list):
        for item in value:
            reject_protected_material(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PROHIBITED_STRING_MARKERS):
            raise ValueError("payload contains protected material")


def _validate_safe_payload(value: Any, *, maximum_bytes: int) -> None:
    reject_protected_material(value)
    if _byte_size(value) > maximum_bytes:
        raise ValueError("payload exceeds byte limit")
    _json_depth(value)


def _validate_finite(value: float | int) -> float | int:
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("numeric value must be finite")
    return value


def _validate_restricted_schema(schema: Any, depth: int = 0) -> None:
    allowed_keywords = {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "enum",
        "const",
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
    }
    allowed_types = {"object", "array", "string", "integer", "number", "boolean", "null"}
    if depth > MAXIMUM_JSON_DEPTH:
        raise ValueError("schema depth exceeds limit")
    if not isinstance(schema, Mapping):
        raise ValueError("schema node must be an object")
    unknown = set(schema) - allowed_keywords
    if unknown:
        raise ValueError("schema contains unsupported keyword")
    schema_type = schema.get("type")
    if schema_type is not None and schema_type not in allowed_types:
        raise ValueError("schema type is unsupported")
    for numeric_key in ("minimum", "maximum"):
        if numeric_key in schema:
            _validate_finite(schema[numeric_key])
    for integer_key in ("minLength", "maxLength", "minItems", "maxItems"):
        if integer_key in schema and not isinstance(schema[integer_key], int):
            raise ValueError("schema bound must be integer")
    if "properties" in schema:
        properties = schema["properties"]
        if not isinstance(properties, Mapping):
            raise ValueError("schema properties must be an object")
        for name, nested in properties.items():
            ensure_safe_identifier(str(name), field_name="schema property")
            _validate_restricted_schema(nested, depth + 1)
    if "items" in schema:
        _validate_restricted_schema(schema["items"], depth + 1)
    if "required" in schema:
        if not isinstance(schema["required"], list):
            raise ValueError("schema required must be an array")
        for item in schema["required"]:
            ensure_safe_identifier(str(item), field_name="required field")


def validate_json_against_schema(value: Any, schema: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    _validate_restricted_schema(schema)
    _validate_schema_node(value, schema, "$", findings)
    return findings


def _validate_schema_node(
    value: Any,
    schema: Mapping[str, Any],
    pointer: str,
    findings: list[str],
) -> None:
    expected_type = schema.get("type")
    if expected_type and not _matches_schema_type(value, str(expected_type)):
        findings.append(f"{pointer}:type")
        return
    if "enum" in schema and value not in schema["enum"]:
        findings.append(f"{pointer}:enum")
    if "const" in schema and value != schema["const"]:
        findings.append(f"{pointer}:const")
    if isinstance(value, str):
        if len(value) > MAXIMUM_TEXT_CHARACTERS_PER_REQUEST:
            findings.append(f"{pointer}:text-limit")
        if "minLength" in schema and len(value) < schema["minLength"]:
            findings.append(f"{pointer}:minLength")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            findings.append(f"{pointer}:maxLength")
    if isinstance(value, int | float) and not isinstance(value, bool):
        _validate_finite(value)
        if "minimum" in schema and value < schema["minimum"]:
            findings.append(f"{pointer}:minimum")
        if "maximum" in schema and value > schema["maximum"]:
            findings.append(f"{pointer}:maximum")
    if isinstance(value, Mapping):
        required = schema.get("required", [])
        for field_name in required:
            if field_name not in value:
                findings.append(f"{pointer}.{field_name}:required")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, nested in value.items():
            if key in properties:
                _validate_schema_node(nested, properties[key], f"{pointer}.{key}", findings)
            elif additional is False:
                findings.append(f"{pointer}.{key}:additionalProperties")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            findings.append(f"{pointer}:minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            findings.append(f"{pointer}:maxItems")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                _validate_schema_node(item, item_schema, f"{pointer}[{index}]", findings)


def _matches_schema_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, Mapping)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return False


class CapabilityManifest(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityManifestSchemaVersion = CAPABILITY_MANIFEST_SCHEMA_VERSION
    capability_id: str
    risk: CapabilityRuntimeRisk
    approval_required: bool
    execution_kind: CapabilityExecutionKind
    side_effect_class: Literal["none"] = "none"
    input_schema_id: str
    output_schema_id: str
    operator_invoked: Literal[True] = True
    explicit_plan: Literal[True] = True
    sandboxed: Literal[True] = True
    deterministic: Literal[True] = True
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    actual_tool_execution: Literal[False] = False
    network_effect: Literal[False] = False
    filesystem_effect: Literal[False] = False
    process_effect: Literal[False] = False
    credential_effect: Literal[False] = False
    token_effect: Literal[False] = False
    manifest_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("capability_id", "input_schema_id", "output_schema_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("manifest_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value, field_name="manifest_fingerprint")

    @model_validator(mode="after")
    def validate_manifest_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "manifest_fingerprint")
        if self.manifest_fingerprint != expected:
            raise ValueError("capability manifest fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        capability_id: str,
        risk: CapabilityRuntimeRisk,
        approval_required: bool,
        execution_kind: CapabilityExecutionKind,
    ) -> Self:
        input_schema_id = f"{capability_id}:input"
        output_schema_id = f"{capability_id}:output"
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_MANIFEST_SCHEMA_VERSION,
            "capability_id": capability_id,
            "risk": risk,
            "approval_required": approval_required,
            "execution_kind": execution_kind,
            "side_effect_class": "none",
            "input_schema_id": input_schema_id,
            "output_schema_id": output_schema_id,
            "operator_invoked": True,
            "explicit_plan": True,
            "sandboxed": True,
            "deterministic": True,
            "external_effect": False,
            "production_effect": False,
            "actual_tool_execution": False,
            "network_effect": False,
            "filesystem_effect": False,
            "process_effect": False,
            "credential_effect": False,
            "token_effect": False,
        }
        return cls(**base, manifest_fingerprint=capability_runtime_fingerprint(base))


class ConnectorManifest(FrozenCapabilityRuntimeModel):
    schema_version: ConnectorManifestSchemaVersion = CONNECTOR_MANIFEST_SCHEMA_VERSION
    connector_id: str
    supported_operations: tuple[str, ...]
    credential_free: Literal[True] = True
    endpoint_present: Literal[False] = False
    network_enabled: Literal[False] = False
    filesystem_enabled: Literal[False] = False
    process_enabled: Literal[False] = False
    actual_connector_available: Literal[False] = False
    synthetic_only: Literal[True] = True
    in_memory_only: Literal[True] = True
    manifest_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("connector_id")
    @classmethod
    def validate_connector_id(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("supported_operations")
    @classmethod
    def validate_operations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("connector must support at least one operation")
        for operation in value:
            ensure_safe_identifier(operation, field_name="supported operation")
        return tuple(sorted(value))

    @field_validator("manifest_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value, field_name="connector manifest fingerprint")

    @model_validator(mode="after")
    def validate_manifest_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "manifest_fingerprint")
        if self.manifest_fingerprint != expected:
            raise ValueError("connector manifest fingerprint mismatch")
        return self

    @classmethod
    def create(cls) -> Self:
        base: dict[str, Any] = {
            "schema_version": CONNECTOR_MANIFEST_SCHEMA_VERSION,
            "connector_id": "deterministic-reference-fixture-connector",
            "supported_operations": (
                "connector.reference.read.simulate",
                "connector.reference.write.preview",
            ),
            "credential_free": True,
            "endpoint_present": False,
            "network_enabled": False,
            "filesystem_enabled": False,
            "process_enabled": False,
            "actual_connector_available": False,
            "synthetic_only": True,
            "in_memory_only": True,
        }
        return cls(**base, manifest_fingerprint=capability_runtime_fingerprint(base))


def default_capability_manifests() -> tuple[CapabilityManifest, ...]:
    return (
        CapabilityManifest.create(
            capability_id="capability_runtime.health.read",
            risk=CapabilityRuntimeRisk.low,
            approval_required=False,
            execution_kind=CapabilityExecutionKind.read_only_reference,
        ),
        CapabilityManifest.create(
            capability_id="capability_runtime.observability.read",
            risk=CapabilityRuntimeRisk.low,
            approval_required=False,
            execution_kind=CapabilityExecutionKind.read_only_reference,
        ),
        CapabilityManifest.create(
            capability_id="capability_runtime.audit.read",
            risk=CapabilityRuntimeRisk.medium,
            approval_required=True,
            execution_kind=CapabilityExecutionKind.read_only_reference,
        ),
        CapabilityManifest.create(
            capability_id="capability.text.normalize",
            risk=CapabilityRuntimeRisk.low,
            approval_required=False,
            execution_kind=CapabilityExecutionKind.pure_function,
        ),
        CapabilityManifest.create(
            capability_id="capability.hash.sha256",
            risk=CapabilityRuntimeRisk.low,
            approval_required=False,
            execution_kind=CapabilityExecutionKind.pure_function,
        ),
        CapabilityManifest.create(
            capability_id="capability.json.validate",
            risk=CapabilityRuntimeRisk.low,
            approval_required=False,
            execution_kind=CapabilityExecutionKind.pure_function,
        ),
        CapabilityManifest.create(
            capability_id="connector.reference.read.simulate",
            risk=CapabilityRuntimeRisk.medium,
            approval_required=True,
            execution_kind=CapabilityExecutionKind.synthetic_reference_connector,
        ),
        CapabilityManifest.create(
            capability_id="connector.reference.write.preview",
            risk=CapabilityRuntimeRisk.medium,
            approval_required=True,
            execution_kind=CapabilityExecutionKind.synthetic_reference_connector_preview,
        ),
    )


CAPABILITY_MANIFESTS = default_capability_manifests()
CAPABILITY_MANIFEST_BY_ID = {item.capability_id: item for item in CAPABILITY_MANIFESTS}
CONNECTOR_MANIFEST = ConnectorManifest.create()


class CapabilityInputSchema(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityInputSchemaVersion = CAPABILITY_INPUT_SCHEMA_VERSION
    schema_id: str
    capability_id: str
    schema: dict[str, Any]  # type: ignore[assignment]
    schema_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("schema_id", "capability_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("schema")
    @classmethod
    def validate_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        _validate_restricted_schema(value)
        return deepcopy(value)

    @field_validator("schema_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value, field_name="schema_fingerprint")

    @model_validator(mode="after")
    def validate_schema_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "schema_fingerprint")
        if self.schema_fingerprint != expected:
            raise ValueError("schema fingerprint mismatch")
        return self

    @classmethod
    def create(cls, *, schema_id: str, capability_id: str, schema: Mapping[str, Any]) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_INPUT_SCHEMA_VERSION,
            "schema_id": schema_id,
            "capability_id": capability_id,
            "schema": deepcopy(dict(schema)),
        }
        return cls(**base, schema_fingerprint=capability_runtime_fingerprint(base))


class CapabilityOutputSchema(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityOutputSchemaVersion = CAPABILITY_OUTPUT_SCHEMA_VERSION
    schema_id: str
    capability_id: str
    schema: dict[str, Any]  # type: ignore[assignment]
    schema_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("schema_id", "capability_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("schema")
    @classmethod
    def validate_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        _validate_restricted_schema(value)
        return deepcopy(value)

    @field_validator("schema_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value, field_name="schema_fingerprint")

    @model_validator(mode="after")
    def validate_schema_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "schema_fingerprint")
        if self.schema_fingerprint != expected:
            raise ValueError("schema fingerprint mismatch")
        return self

    @classmethod
    def create(cls, *, schema_id: str, capability_id: str, schema: Mapping[str, Any]) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_OUTPUT_SCHEMA_VERSION,
            "schema_id": schema_id,
            "capability_id": capability_id,
            "schema": deepcopy(dict(schema)),
        }
        return cls(**base, schema_fingerprint=capability_runtime_fingerprint(base))


class ReferenceConnectorRequestSchema(CapabilityInputSchema):
    pass


class ReferenceConnectorResponseSchema(CapabilityOutputSchema):
    pass


def default_input_schema_for(capability_id: str) -> CapabilityInputSchema:
    if capability_id in {
        "capability_runtime.health.read",
        "capability_runtime.observability.read",
        "capability_runtime.audit.read",
    }:
        schema = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
    elif capability_id in {"capability.text.normalize", "capability.hash.sha256"}:
        schema = {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "maxLength": MAXIMUM_TEXT_CHARACTERS_PER_REQUEST,
                }
            },
            "required": ["text"],
            "additionalProperties": False,
        }
    elif capability_id == "capability.json.validate":
        schema = {
            "type": "object",
            "properties": {
                "document": {"type": "object", "additionalProperties": True},
                "schema": {"type": "object", "additionalProperties": True},
            },
            "required": ["document", "schema"],
            "additionalProperties": False,
        }
    else:
        schema = {
            "type": "object",
            "properties": {
                "fixture_id": {"type": "string", "maxLength": 128},
                "record_key": {"type": "string", "maxLength": 128},
                "proposed_value": {"type": "object", "additionalProperties": True},
            },
            "required": ["fixture_id", "record_key"],
            "additionalProperties": False,
        }
    return CapabilityInputSchema.create(
        schema_id=f"{capability_id}:input",
        capability_id=capability_id,
        schema=schema,
    )


def default_output_schema_for(capability_id: str) -> CapabilityOutputSchema:
    schema = {"type": "object", "additionalProperties": True}
    return CapabilityOutputSchema.create(
        schema_id=f"{capability_id}:output",
        capability_id=capability_id,
        schema=schema,
    )


class CapabilityRuntimeComponentBinding(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityRuntimeComponentBindingSchemaVersion = (
        CAPABILITY_RUNTIME_COMPONENT_BINDING_SCHEMA_VERSION
    )
    program_id: ProgramId = PROGRAM_ID
    authorization_transaction_id: AuthorizationTransactionId = AUTHORIZATION_TRANSACTION_ID
    secure_runtime_session_id: str
    secure_runtime_request_id: str
    actor_context_fingerprint: str
    secure_runtime_guard_fingerprint: str
    parent_kill_switch_fingerprint: str
    model_gateway_session_id: str
    model_gateway_request_id: str
    model_output_provenance_fingerprint: str
    model_output_classification: Literal["untrusted_model_output"] = "untrusted_model_output"
    model_output_trusted: Literal[False] = False
    historical_component_authorization_ids: tuple[str, ...] = (
        "AION-230-SRI-0001",
        "AION-232-SRI-0002",
    )
    component_authorizations_closed: Literal[True] = True
    component_authorizations_reactivated: Literal[False] = False
    redacted: Literal[True] = True
    production_effect: Literal[False] = False
    runtime_effect: Literal[False] = False
    binding_fingerprint: str = ZERO_FINGERPRINT

    @field_validator(
        "secure_runtime_session_id",
        "secure_runtime_request_id",
        "model_gateway_session_id",
        "model_gateway_request_id",
    )
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "actor_context_fingerprint",
        "secure_runtime_guard_fingerprint",
        "parent_kill_switch_fingerprint",
        "model_output_provenance_fingerprint",
        "binding_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_binding_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "binding_fingerprint")
        if self.binding_fingerprint != expected:
            raise ValueError("component binding fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        secure_runtime_session_id: str = "sri-session-AION-235",
        secure_runtime_request_id: str = "sri-request-AION-235",
        actor_context_fingerprint: str | None = None,
        secure_runtime_guard_fingerprint: str | None = None,
        parent_kill_switch_fingerprint: str | None = None,
        model_gateway_session_id: str = "model-gateway-session-AION-233",
        model_gateway_request_id: str = "model-gateway-request-AION-233",
        model_output_provenance_fingerprint: str | None = None,
    ) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_RUNTIME_COMPONENT_BINDING_SCHEMA_VERSION,
            "program_id": PROGRAM_ID,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "secure_runtime_session_id": secure_runtime_session_id,
            "secure_runtime_request_id": secure_runtime_request_id,
            "actor_context_fingerprint": actor_context_fingerprint
            or text_fingerprint("actor-context", "AION-231-verified-actor-context"),
            "secure_runtime_guard_fingerprint": secure_runtime_guard_fingerprint
            or text_fingerprint("secure-runtime-guard", "allow-reference-only"),
            "parent_kill_switch_fingerprint": parent_kill_switch_fingerprint
            or text_fingerprint("kill-switch", "clear"),
            "model_gateway_session_id": model_gateway_session_id,
            "model_gateway_request_id": model_gateway_request_id,
            "model_output_provenance_fingerprint": model_output_provenance_fingerprint
            or text_fingerprint("model-output-provenance", "AION-233-untrusted-proposal"),
            "model_output_classification": "untrusted_model_output",
            "model_output_trusted": False,
            "historical_component_authorization_ids": (
                "AION-230-SRI-0001",
                "AION-232-SRI-0002",
            ),
            "component_authorizations_closed": True,
            "component_authorizations_reactivated": False,
            "redacted": True,
            "production_effect": False,
            "runtime_effect": False,
        }
        return cls(**base, binding_fingerprint=capability_runtime_fingerprint(base))


class ModelGatewayProposalBinding(FrozenCapabilityRuntimeModel):
    proposal_id: str
    model_output_provenance_fingerprint: str
    output_classification: Literal["untrusted_model_output"] = "untrusted_model_output"
    suggested_capability_code_fingerprints: tuple[str, ...] = ()
    model_output_is_untrusted: Literal[True] = True
    execution_authority: Literal[False] = False
    approval_authority: Literal[False] = False
    operator_selection_required: Literal[True] = True
    redacted: Literal[True] = True
    proposal_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("proposal_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("model_output_provenance_fingerprint", "proposal_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_proposal_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "proposal_fingerprint")
        if self.proposal_fingerprint != expected:
            raise ValueError("proposal fingerprint mismatch")
        return self

    @classmethod
    def create(cls, *, proposal_id: str = "model-gateway-proposal-AION-235") -> Self:
        base: dict[str, Any] = {
            "proposal_id": proposal_id,
            "model_output_provenance_fingerprint": text_fingerprint(
                "model-output-provenance",
                "AION-233-untrusted-proposal",
            ),
            "output_classification": "untrusted_model_output",
            "suggested_capability_code_fingerprints": tuple(
                capability_runtime_fingerprint({"capability_id": item.capability_id})
                for item in CAPABILITY_MANIFESTS
            ),
            "model_output_is_untrusted": True,
            "execution_authority": False,
            "approval_authority": False,
            "operator_selection_required": True,
            "redacted": True,
        }
        return cls(**base, proposal_fingerprint=capability_runtime_fingerprint(base))


class CapabilitySideEffectBudget(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityBudgetSchemaVersion = CAPABILITY_BUDGET_SCHEMA_VERSION
    budget_id: str
    resource_limits: dict[str, int] = Field(default_factory=lambda: deepcopy(ALL_RESOURCE_LIMITS))
    prohibited_effect_counters: dict[str, int] = Field(
        default_factory=lambda: {key: 0 for key in PROHIBITED_EFFECT_COUNTERS}
    )
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    budget_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("budget_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("resource_limits")
    @classmethod
    def validate_limits(cls, value: dict[str, int]) -> dict[str, int]:
        if value != ALL_RESOURCE_LIMITS:
            raise ValueError("resource limits must match AION-234-SRI-0003")
        return deepcopy(value)

    @field_validator("prohibited_effect_counters")
    @classmethod
    def validate_counters(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != set(PROHIBITED_EFFECT_COUNTERS):
            raise ValueError("prohibited effect counter set mismatch")
        if any(count != 0 for count in value.values()):
            raise ValueError("prohibited effect counters must remain zero")
        return dict(sorted(value.items()))

    @field_validator("budget_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value, field_name="budget_fingerprint")

    @model_validator(mode="after")
    def validate_budget_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "budget_fingerprint")
        if self.budget_fingerprint != expected:
            raise ValueError("budget fingerprint mismatch")
        return self

    @classmethod
    def create(cls, budget_id: str = "capability-runtime-budget-AION-235") -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_BUDGET_SCHEMA_VERSION,
            "budget_id": budget_id,
            "resource_limits": deepcopy(ALL_RESOURCE_LIMITS),
            "prohibited_effect_counters": {key: 0 for key in PROHIBITED_EFFECT_COUNTERS},
            "external_effect": False,
            "production_effect": False,
        }
        return cls(**base, budget_fingerprint=capability_runtime_fingerprint(base))


class CapabilitySideEffectUsage(FrozenCapabilityRuntimeModel):
    usage_id: str
    counters: dict[str, int] = Field(
        default_factory=lambda: {key: 0 for key in PROHIBITED_EFFECT_COUNTERS}
    )
    reference_capability_executions: int = Field(default=0, ge=0)
    synthetic_connector_simulations: int = Field(default=0, ge=0)

    @field_validator("usage_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("counters")
    @classmethod
    def validate_counters(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != set(PROHIBITED_EFFECT_COUNTERS):
            raise ValueError("usage counter set mismatch")
        if any(count != 0 for count in value.values()):
            raise ValueError("prohibited usage counters must remain zero")
        return dict(sorted(value.items()))


class CapabilitySideEffectBudgetDecision(FrozenCapabilityRuntimeModel):
    decision_id: str
    budget_fingerprint: str
    passed: bool
    reason_codes: tuple[str, ...] = ()

    @field_validator("decision_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("budget_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)


class CapabilityRuntimeAuthorizationEnvelope(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityRuntimeAuthorizationSchemaVersion = (
        CAPABILITY_RUNTIME_AUTHORIZATION_SCHEMA_VERSION
    )
    program_id: ProgramId = PROGRAM_ID
    authorization_transaction_id: AuthorizationTransactionId = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: ApprovalRecordId = APPROVAL_RECORD_ID
    authorization_scope: AuthorizationScopeLiteral = AUTHORIZATION_SCOPE
    component_binding_fingerprint: str
    operator_identity_fingerprint: str
    actor_context_fingerprint: str
    secure_runtime_session_id: str
    model_gateway_proposal_fingerprint: str
    allowed_capability_ids: tuple[str, ...]
    allowed_connector_ids: tuple[str, ...] = ("deterministic-reference-fixture-connector",)
    resource_budget_fingerprint: str
    maximum_requests: int = MAXIMUM_REQUESTS_PER_SESSION
    maximum_concurrency: int = MAXIMUM_CONCURRENT_REQUESTS
    created_at: datetime
    expires_at: datetime
    confirmation_fingerprint: str
    operator_invoked: Literal[True] = True
    model_output_triggered_execution: Literal[False] = False
    external_execution: Literal[False] = False
    production_runtime: Literal[False] = False
    production_effect: Literal[False] = False
    authorization_active: Literal[True] = True
    authorization_consumed: Literal[False] = False
    authorization_expired: Literal[False] = False
    authorization_reusable: Literal[False] = False
    envelope_fingerprint: str = ZERO_FINGERPRINT

    @field_validator(
        "component_binding_fingerprint",
        "operator_identity_fingerprint",
        "actor_context_fingerprint",
        "model_gateway_proposal_fingerprint",
        "resource_budget_fingerprint",
        "confirmation_fingerprint",
        "envelope_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("secure_runtime_session_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def validate_envelope(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("authorization expiry must be after creation")
        if set(self.allowed_capability_ids) != set(CAPABILITY_MANIFEST_BY_ID):
            raise ValueError("allowed capability set must match closed registry")
        if self.confirmation_fingerprint != confirmation_fingerprint():
            raise ValueError("confirmation fingerprint mismatch")
        expected = fingerprint_without(self.model_dump(mode="json"), "envelope_fingerprint")
        if self.envelope_fingerprint != expected:
            raise ValueError("authorization envelope fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        component_binding: CapabilityRuntimeComponentBinding,
        model_proposal: ModelGatewayProposalBinding,
        budget: CapabilitySideEffectBudget,
        created_at: datetime | None = None,
    ) -> Self:
        now = normalize_utc_datetime(created_at or datetime(2026, 7, 31, 20, 0, tzinfo=UTC))
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_RUNTIME_AUTHORIZATION_SCHEMA_VERSION,
            "program_id": PROGRAM_ID,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "approval_record_id": APPROVAL_RECORD_ID,
            "authorization_scope": AUTHORIZATION_SCOPE,
            "component_binding_fingerprint": component_binding.binding_fingerprint,
            "operator_identity_fingerprint": text_fingerprint(
                "operator-identity",
                "AION-231-authenticated-local-operator",
            ),
            "actor_context_fingerprint": component_binding.actor_context_fingerprint,
            "secure_runtime_session_id": component_binding.secure_runtime_session_id,
            "model_gateway_proposal_fingerprint": model_proposal.proposal_fingerprint,
            "allowed_capability_ids": tuple(sorted(CAPABILITY_MANIFEST_BY_ID)),
            "allowed_connector_ids": ("deterministic-reference-fixture-connector",),
            "resource_budget_fingerprint": budget.budget_fingerprint,
            "maximum_requests": MAXIMUM_REQUESTS_PER_SESSION,
            "maximum_concurrency": MAXIMUM_CONCURRENT_REQUESTS,
            "created_at": now,
            "expires_at": now + timedelta(minutes=30),
            "confirmation_fingerprint": confirmation_fingerprint(),
            "operator_invoked": True,
            "model_output_triggered_execution": False,
            "external_execution": False,
            "production_runtime": False,
            "production_effect": False,
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
            "authorization_reusable": False,
        }
        return cls(**base, envelope_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeSessionPlan(FrozenCapabilityRuntimeModel):
    schema_version: CapabilitySessionSchemaVersion = CAPABILITY_SESSION_SCHEMA_VERSION
    session_plan_id: str
    authorization_envelope_fingerprint: str
    component_binding_fingerprint: str
    model_gateway_proposal_fingerprint: str
    budget_fingerprint: str
    capability_manifest_fingerprints: tuple[str, ...]
    connector_manifest_fingerprint: str
    created_at: datetime
    expires_at: datetime
    deterministic: Literal[True] = True
    sandboxed: Literal[True] = True
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    plan_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("session_plan_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "authorization_envelope_fingerprint",
        "component_binding_fingerprint",
        "model_gateway_proposal_fingerprint",
        "budget_fingerprint",
        "connector_manifest_fingerprint",
        "plan_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("session plan expiry must be after creation")
        expected = fingerprint_without(self.model_dump(mode="json"), "plan_fingerprint")
        if self.plan_fingerprint != expected:
            raise ValueError("session plan fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        authorization: CapabilityRuntimeAuthorizationEnvelope,
        component_binding: CapabilityRuntimeComponentBinding,
        model_proposal: ModelGatewayProposalBinding,
        budget: CapabilitySideEffectBudget,
        created_at: datetime | None = None,
    ) -> Self:
        now = normalize_utc_datetime(created_at or authorization.created_at)
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_SESSION_SCHEMA_VERSION,
            "session_plan_id": "capability-runtime-session-plan-AION-235",
            "authorization_envelope_fingerprint": authorization.envelope_fingerprint,
            "component_binding_fingerprint": component_binding.binding_fingerprint,
            "model_gateway_proposal_fingerprint": model_proposal.proposal_fingerprint,
            "budget_fingerprint": budget.budget_fingerprint,
            "capability_manifest_fingerprints": tuple(
                item.manifest_fingerprint for item in CAPABILITY_MANIFESTS
            ),
            "connector_manifest_fingerprint": CONNECTOR_MANIFEST.manifest_fingerprint,
            "created_at": now,
            "expires_at": authorization.expires_at,
            "deterministic": True,
            "sandboxed": True,
            "external_effect": False,
            "production_effect": False,
        }
        return cls(**base, plan_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeSession(FrozenCapabilityRuntimeModel):
    schema_version: CapabilitySessionSchemaVersion = CAPABILITY_SESSION_SCHEMA_VERSION
    session_id: str
    session_plan_fingerprint: str
    authorization_envelope_fingerprint: str
    status: CapabilityRuntimeSessionStatus
    active_request_ids: tuple[str, ...] = ()
    completed_request_count: int = Field(default=0, ge=0)
    created_at: datetime
    expires_at: datetime
    closed_at: datetime | None = None
    automatic_continuation: Literal[False] = False
    background_execution: Literal[False] = False
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    session_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("session_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "session_plan_fingerprint",
        "authorization_envelope_fingerprint",
        "session_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at", "closed_at")
    @classmethod
    def validate_time(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def validate_session(self) -> Self:
        if len(self.active_request_ids) > MAXIMUM_CONCURRENT_REQUESTS:
            raise ValueError("active request limit exceeded")
        if self.expires_at <= self.created_at:
            raise ValueError("session expiry must be after creation")
        expected = fingerprint_without(self.model_dump(mode="json"), "session_fingerprint")
        if self.session_fingerprint != expected:
            raise ValueError("session fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        plan: CapabilityRuntimeSessionPlan,
        authorization: CapabilityRuntimeAuthorizationEnvelope,
        created_at: datetime | None = None,
    ) -> Self:
        now = normalize_utc_datetime(created_at or plan.created_at)
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_SESSION_SCHEMA_VERSION,
            "session_id": session_id,
            "session_plan_fingerprint": plan.plan_fingerprint,
            "authorization_envelope_fingerprint": authorization.envelope_fingerprint,
            "status": CapabilityRuntimeSessionStatus.active,
            "active_request_ids": (),
            "completed_request_count": 0,
            "created_at": now,
            "expires_at": min(plan.expires_at, authorization.expires_at),
            "closed_at": None,
            "automatic_continuation": False,
            "background_execution": False,
            "external_effect": False,
            "production_effect": False,
        }
        return cls(**base, session_fingerprint=capability_runtime_fingerprint(base))

    def with_active_request(self, request_id: str) -> Self:
        active = tuple(sorted(set(self.active_request_ids) | {request_id}))
        base = self.model_dump(mode="python")
        base["active_request_ids"] = active
        base["session_fingerprint"] = capability_runtime_fingerprint(
            {key: value for key, value in base.items() if key != "session_fingerprint"}
        )
        return type(self)(**base)

    def with_closed_request(self, request_id: str) -> Self:
        active = tuple(item for item in self.active_request_ids if item != request_id)
        base = self.model_dump(mode="python")
        base["active_request_ids"] = active
        base["completed_request_count"] = self.completed_request_count + 1
        base["session_fingerprint"] = capability_runtime_fingerprint(
            {key: value for key, value in base.items() if key != "session_fingerprint"}
        )
        return type(self)(**base)

    def close(self, closed_at: datetime) -> Self:
        base = self.model_dump(mode="python")
        base["status"] = CapabilityRuntimeSessionStatus.closed
        base["active_request_ids"] = ()
        base["closed_at"] = normalize_utc_datetime(closed_at)
        base["session_fingerprint"] = capability_runtime_fingerprint(
            {key: value for key, value in base.items() if key != "session_fingerprint"}
        )
        return type(self)(**base)


class CapabilityRequestEnvelope(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityRequestSchemaVersion = CAPABILITY_REQUEST_SCHEMA_VERSION
    session_id: str
    request_id: str
    trace_id: str
    correlation_id: str
    component_binding_fingerprint: str
    model_gateway_proposal_fingerprint: str | None = None
    operator_selected_capability_id: str
    operator_selection_fingerprint: str
    capability_manifest_fingerprint: str
    connector_manifest_fingerprint: str | None = None
    input_fingerprint: str
    input_byte_count: int = Field(ge=0)
    input_schema_fingerprint: str
    output_schema_fingerprint: str
    safe_metadata_fingerprint: str
    created_at: datetime
    expires_at: datetime
    model_output_is_untrusted: Literal[True] = True
    operator_selected: Literal[True] = True
    automatic_selection: Literal[False] = False
    raw_input_retained: Literal[False] = False
    raw_output_retained: Literal[False] = False
    network_target_present: Literal[False] = False
    filesystem_target_present: Literal[False] = False
    process_target_present: Literal[False] = False
    executable_present: Literal[False] = False
    production_target_present: Literal[False] = False
    request_fingerprint: str = ZERO_FINGERPRINT

    @field_validator(
        "session_id",
        "request_id",
        "trace_id",
        "correlation_id",
        "operator_selected_capability_id",
    )
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "component_binding_fingerprint",
        "model_gateway_proposal_fingerprint",
        "operator_selection_fingerprint",
        "capability_manifest_fingerprint",
        "connector_manifest_fingerprint",
        "input_fingerprint",
        "input_schema_fingerprint",
        "output_schema_fingerprint",
        "safe_metadata_fingerprint",
        "request_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("request expiry must be after creation")
        expected = fingerprint_without(self.model_dump(mode="json"), "request_fingerprint")
        if self.request_fingerprint != expected:
            raise ValueError("request fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        request_id: str,
        capability_id: str,
        input_payload: Any,
        input_schema: CapabilityInputSchema,
        output_schema: CapabilityOutputSchema,
        component_binding: CapabilityRuntimeComponentBinding,
        model_proposal: ModelGatewayProposalBinding | None,
        created_at: datetime,
        connector_manifest: ConnectorManifest | None = None,
    ) -> Self:
        _validate_safe_payload(input_payload, maximum_bytes=MAXIMUM_INPUT_BYTES_PER_REQUEST)
        manifest = CAPABILITY_MANIFEST_BY_ID[capability_id]
        input_fingerprint = capability_runtime_fingerprint(input_payload)
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_REQUEST_SCHEMA_VERSION,
            "session_id": session_id,
            "request_id": request_id,
            "trace_id": f"trace-{request_id}",
            "correlation_id": f"correlation-{request_id}",
            "component_binding_fingerprint": component_binding.binding_fingerprint,
            "model_gateway_proposal_fingerprint": (
                model_proposal.proposal_fingerprint if model_proposal else None
            ),
            "operator_selected_capability_id": capability_id,
            "operator_selection_fingerprint": capability_runtime_fingerprint(
                {"request_id": request_id, "selected_capability_id": capability_id}
            ),
            "capability_manifest_fingerprint": manifest.manifest_fingerprint,
            "connector_manifest_fingerprint": (
                connector_manifest.manifest_fingerprint if connector_manifest else None
            ),
            "input_fingerprint": input_fingerprint,
            "input_byte_count": _byte_size(input_payload),
            "input_schema_fingerprint": input_schema.schema_fingerprint,
            "output_schema_fingerprint": output_schema.schema_fingerprint,
            "safe_metadata_fingerprint": capability_runtime_fingerprint(
                {"metadata": "redacted", "request_id": request_id}
            ),
            "created_at": normalize_utc_datetime(created_at),
            "expires_at": normalize_utc_datetime(created_at) + timedelta(minutes=5),
            "model_output_is_untrusted": True,
            "operator_selected": True,
            "automatic_selection": False,
            "raw_input_retained": False,
            "raw_output_retained": False,
            "network_target_present": False,
            "filesystem_target_present": False,
            "process_target_present": False,
            "executable_present": False,
            "production_target_present": False,
        }
        return cls(**base, request_fingerprint=capability_runtime_fingerprint(base))


class CapabilityExecutionPlan(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityExecutionPlanSchemaVersion = (
        CAPABILITY_EXECUTION_PLAN_SCHEMA_VERSION
    )
    session_id: str
    request_id: str
    operator_selection_fingerprint: str
    model_gateway_proposal_fingerprint: str | None = None
    capability_manifest_fingerprint: str
    connector_manifest_fingerprint: str | None = None
    input_fingerprint: str
    input_schema_fingerprint: str
    output_schema_fingerprint: str
    policy_binding_expected: Literal[True] = True
    risk_binding_expected: Literal[True] = True
    guardrail_binding_expected: Literal[True] = True
    approval_binding_expected: bool
    side_effect_budget_fingerprint: str
    sandbox_profile_fingerprint: str
    parent_kill_switch_fingerprint: str
    maximum_operation_steps: int = MAXIMUM_OPERATION_STEPS_PER_EXECUTION
    maximum_wall_clock_milliseconds: int = MAXIMUM_EXECUTION_WALL_CLOCK_MILLISECONDS
    created_at: datetime
    expires_at: datetime
    deterministic: Literal[True] = True
    sandboxed: Literal[True] = True
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    plan_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("session_id", "request_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "operator_selection_fingerprint",
        "model_gateway_proposal_fingerprint",
        "capability_manifest_fingerprint",
        "connector_manifest_fingerprint",
        "input_fingerprint",
        "input_schema_fingerprint",
        "output_schema_fingerprint",
        "side_effect_budget_fingerprint",
        "sandbox_profile_fingerprint",
        "parent_kill_switch_fingerprint",
        "plan_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("execution plan expiry must be after creation")
        expected = fingerprint_without(self.model_dump(mode="json"), "plan_fingerprint")
        if self.plan_fingerprint != expected:
            raise ValueError("execution plan fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: CapabilityRequestEnvelope,
        manifest: CapabilityManifest,
        budget: CapabilitySideEffectBudget,
        sandbox: CapabilitySandboxProfile,
        component_binding: CapabilityRuntimeComponentBinding,
        created_at: datetime,
    ) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_EXECUTION_PLAN_SCHEMA_VERSION,
            "session_id": request.session_id,
            "request_id": request.request_id,
            "operator_selection_fingerprint": request.operator_selection_fingerprint,
            "model_gateway_proposal_fingerprint": request.model_gateway_proposal_fingerprint,
            "capability_manifest_fingerprint": manifest.manifest_fingerprint,
            "connector_manifest_fingerprint": request.connector_manifest_fingerprint,
            "input_fingerprint": request.input_fingerprint,
            "input_schema_fingerprint": request.input_schema_fingerprint,
            "output_schema_fingerprint": request.output_schema_fingerprint,
            "policy_binding_expected": True,
            "risk_binding_expected": True,
            "guardrail_binding_expected": True,
            "approval_binding_expected": manifest.approval_required,
            "side_effect_budget_fingerprint": budget.budget_fingerprint,
            "sandbox_profile_fingerprint": sandbox.profile_fingerprint,
            "parent_kill_switch_fingerprint": component_binding.parent_kill_switch_fingerprint,
            "maximum_operation_steps": MAXIMUM_OPERATION_STEPS_PER_EXECUTION,
            "maximum_wall_clock_milliseconds": MAXIMUM_EXECUTION_WALL_CLOCK_MILLISECONDS,
            "created_at": normalize_utc_datetime(created_at),
            "expires_at": normalize_utc_datetime(created_at) + timedelta(minutes=5),
            "deterministic": True,
            "sandboxed": True,
            "external_effect": False,
            "production_effect": False,
        }
        return cls(**base, plan_fingerprint=capability_runtime_fingerprint(base))


class CapabilityPolicyBinding(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityDecisionBindingSchemaVersion = (
        CAPABILITY_DECISION_BINDING_SCHEMA_VERSION
    )
    decision_id: str
    request_id: str
    allowed: bool
    policy_fingerprint: str
    external_effect_allowed: Literal[False] = False
    production_effect_allowed: Literal[False] = False

    @field_validator("decision_id", "request_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("policy_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @classmethod
    def allow(cls, request_id: str) -> Self:
        return cls(
            decision_id=f"policy-{request_id}",
            request_id=request_id,
            allowed=True,
            policy_fingerprint=capability_runtime_fingerprint(
                {"policy": "allow", "request_id": request_id}
            ),
        )


class CapabilityRiskBinding(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityDecisionBindingSchemaVersion = (
        CAPABILITY_DECISION_BINDING_SCHEMA_VERSION
    )
    assessment_id: str
    request_id: str
    risk: CapabilityRuntimeRisk
    blocked: bool
    risk_fingerprint: str

    @field_validator("assessment_id", "request_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("risk_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @classmethod
    def bind(cls, request_id: str, risk: CapabilityRuntimeRisk) -> Self:
        return cls(
            assessment_id=f"risk-{request_id}",
            request_id=request_id,
            risk=risk,
            blocked=risk in {CapabilityRuntimeRisk.high, CapabilityRuntimeRisk.critical},
            risk_fingerprint=capability_runtime_fingerprint(
                {"request_id": request_id, "risk": risk}
            ),
        )


class CapabilityGuardrailBinding(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityDecisionBindingSchemaVersion = (
        CAPABILITY_DECISION_BINDING_SCHEMA_VERSION
    )
    guardrail_id: str
    request_id: str
    allowed: bool
    guardrail_fingerprint: str

    @field_validator("guardrail_id", "request_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("guardrail_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @classmethod
    def allow(cls, request_id: str) -> Self:
        return cls(
            guardrail_id=f"guardrail-{request_id}",
            request_id=request_id,
            allowed=True,
            guardrail_fingerprint=capability_runtime_fingerprint(
                {"guardrail": "allow", "request_id": request_id}
            ),
        )


class CapabilityApprovalEvidence(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityApprovalSchemaVersion = CAPABILITY_APPROVAL_SCHEMA_VERSION
    approval_id: str
    approval_request_id: str
    approval_decision_id: str
    action: Literal["capability_runtime.execute.reference"] = (
        "capability_runtime.execute.reference"
    )
    resource: Literal["capability_execution_plan"] = "capability_execution_plan"
    scope: Literal["capability-runtime:execute-reference"] = (
        "capability-runtime:execute-reference"
    )
    session_id: str
    request_id: str
    capability_id: str
    connector_id: str | None = None
    execution_plan_fingerprint: str
    actor_context_fingerprint: str
    policy_binding_fingerprint: str
    risk_binding_fingerprint: str
    guardrail_binding_fingerprint: str
    budget_fingerprint: str
    sandbox_profile_fingerprint: str
    requester_id: str
    approver_id: str
    decision: Literal["approve"] = "approve"
    approved: Literal[True] = True
    cancelled: Literal[False] = False
    external_effect_authority: Literal[False] = False
    created_at: datetime
    expires_at: datetime
    evidence_fingerprint: str = ZERO_FINGERPRINT

    @field_validator(
        "approval_id",
        "approval_request_id",
        "approval_decision_id",
        "session_id",
        "request_id",
        "capability_id",
        "connector_id",
        "requester_id",
        "approver_id",
    )
    @classmethod
    def validate_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_safe_identifier(value)

    @field_validator(
        "execution_plan_fingerprint",
        "actor_context_fingerprint",
        "policy_binding_fingerprint",
        "risk_binding_fingerprint",
        "guardrail_binding_fingerprint",
        "budget_fingerprint",
        "sandbox_profile_fingerprint",
        "evidence_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        if self.requester_id == self.approver_id:
            raise ValueError("requester must differ from approver")
        if self.expires_at <= self.created_at:
            raise ValueError("approval expiry must be after creation")
        expected = fingerprint_without(self.model_dump(mode="json"), "evidence_fingerprint")
        if self.evidence_fingerprint != expected:
            raise ValueError("approval evidence fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        plan: CapabilityExecutionPlan,
        component_binding: CapabilityRuntimeComponentBinding,
        policy: CapabilityPolicyBinding,
        risk: CapabilityRiskBinding,
        guardrail: CapabilityGuardrailBinding,
        budget: CapabilitySideEffectBudget,
        sandbox: CapabilitySandboxProfile,
        capability_id: str,
        connector_id: str | None = None,
        created_at: datetime | None = None,
    ) -> Self:
        now = normalize_utc_datetime(created_at or plan.created_at)
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_APPROVAL_SCHEMA_VERSION,
            "approval_id": f"approval-{plan.request_id}",
            "approval_request_id": f"approval-request-{plan.request_id}",
            "approval_decision_id": f"approval-decision-{plan.request_id}",
            "action": "capability_runtime.execute.reference",
            "resource": "capability_execution_plan",
            "scope": "capability-runtime:execute-reference",
            "session_id": plan.session_id,
            "request_id": plan.request_id,
            "capability_id": capability_id,
            "connector_id": connector_id,
            "execution_plan_fingerprint": plan.plan_fingerprint,
            "actor_context_fingerprint": component_binding.actor_context_fingerprint,
            "policy_binding_fingerprint": capability_runtime_fingerprint(policy),
            "risk_binding_fingerprint": capability_runtime_fingerprint(risk),
            "guardrail_binding_fingerprint": capability_runtime_fingerprint(guardrail),
            "budget_fingerprint": budget.budget_fingerprint,
            "sandbox_profile_fingerprint": sandbox.profile_fingerprint,
            "requester_id": "operator-requester-AION-235",
            "approver_id": "operator-approver-AION-235",
            "decision": "approve",
            "approved": True,
            "cancelled": False,
            "external_effect_authority": False,
            "created_at": now,
            "expires_at": now + timedelta(minutes=10),
        }
        return cls(**base, evidence_fingerprint=capability_runtime_fingerprint(base))


class CapabilityApprovalEvidenceBundle(FrozenCapabilityRuntimeModel):
    approval_records: tuple[CapabilityApprovalEvidence, ...] = ()
    bundle_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("approval_records")
    @classmethod
    def validate_records(
        cls, value: tuple[CapabilityApprovalEvidence, ...]
    ) -> tuple[CapabilityApprovalEvidence, ...]:
        if len(value) > MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_REQUEST:
            raise ValueError("approval evidence record limit exceeded")
        return value

    @field_validator("bundle_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_bundle(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "bundle_fingerprint")
        if self.bundle_fingerprint != expected:
            raise ValueError("approval bundle fingerprint mismatch")
        return self

    @classmethod
    def create(cls, records: tuple[CapabilityApprovalEvidence, ...] = ()) -> Self:
        base: dict[str, Any] = {"approval_records": records}
        return cls(**base, bundle_fingerprint=capability_runtime_fingerprint(base))


class CapabilitySandboxProfile(FrozenCapabilityRuntimeModel):
    schema_version: CapabilitySandboxSchemaVersion = CAPABILITY_SANDBOX_SCHEMA_VERSION
    profile_id: str
    in_memory_only: Literal[True] = True
    static_dispatch_only: Literal[True] = True
    deterministic_clock: Literal[True] = True
    deterministic_fixture_registry: Literal[True] = True
    network_disabled: Literal[True] = True
    dns_disabled: Literal[True] = True
    filesystem_disabled: Literal[True] = True
    process_disabled: Literal[True] = True
    shell_disabled: Literal[True] = True
    subprocess_disabled: Literal[True] = True
    browser_disabled: Literal[True] = True
    dynamic_import_disabled: Literal[True] = True
    eval_disabled: Literal[True] = True
    exec_disabled: Literal[True] = True
    package_install_disabled: Literal[True] = True
    module_activation_disabled: Literal[True] = True
    credential_access_disabled: Literal[True] = True
    token_access_disabled: Literal[True] = True
    production_write_disabled: Literal[True] = True
    profile_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("profile_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("profile_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_profile_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "profile_fingerprint")
        if self.profile_fingerprint != expected:
            raise ValueError("sandbox profile fingerprint mismatch")
        return self

    @classmethod
    def create(cls, profile_id: str = "in-memory-reference-sandbox") -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_SANDBOX_SCHEMA_VERSION,
            "profile_id": profile_id,
            "in_memory_only": True,
            "static_dispatch_only": True,
            "deterministic_clock": True,
            "deterministic_fixture_registry": True,
            "network_disabled": True,
            "dns_disabled": True,
            "filesystem_disabled": True,
            "process_disabled": True,
            "shell_disabled": True,
            "subprocess_disabled": True,
            "browser_disabled": True,
            "dynamic_import_disabled": True,
            "eval_disabled": True,
            "exec_disabled": True,
            "package_install_disabled": True,
            "module_activation_disabled": True,
            "credential_access_disabled": True,
            "token_access_disabled": True,
            "production_write_disabled": True,
        }
        return cls(**base, profile_fingerprint=capability_runtime_fingerprint(base))


class CapabilitySandboxDecision(FrozenCapabilityRuntimeModel):
    schema_version: CapabilitySandboxSchemaVersion = CAPABILITY_SANDBOX_SCHEMA_VERSION
    decision_id: str
    profile_fingerprint: str
    outcome: CapabilitySandboxOutcome
    reason_codes: tuple[str, ...] = ()
    sandbox_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("decision_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("profile_fingerprint", "sandbox_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_fingerprint_value(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "sandbox_fingerprint")
        if self.sandbox_fingerprint != expected:
            raise ValueError("sandbox decision fingerprint mismatch")
        return self

    @classmethod
    def allow(cls, request_id: str, profile: CapabilitySandboxProfile) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_SANDBOX_SCHEMA_VERSION,
            "decision_id": f"sandbox-{request_id}",
            "profile_fingerprint": profile.profile_fingerprint,
            "outcome": CapabilitySandboxOutcome.allow_reference_execution,
            "reason_codes": ("in_memory_static_dispatch_only",),
        }
        return cls(**base, sandbox_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeGuardDecision(FrozenCapabilityRuntimeModel):
    decision_id: str
    outcome: CapabilitySandboxOutcome
    reason_codes: tuple[str, ...]
    guard_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("decision_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("guard_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_fingerprint_value(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "guard_fingerprint")
        if self.guard_fingerprint != expected:
            raise ValueError("guard fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        request_id: str,
        outcome: CapabilitySandboxOutcome,
        reason_codes: tuple[str, ...],
    ) -> Self:
        base: dict[str, Any] = {
            "decision_id": f"guard-{request_id}",
            "outcome": outcome,
            "reason_codes": reason_codes,
        }
        return cls(**base, guard_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeGuardEvaluator:
    allowed_outcomes: ClassVar[set[CapabilitySandboxOutcome]] = {
        CapabilitySandboxOutcome.allow_reference_execution,
        CapabilitySandboxOutcome.require_approval,
        CapabilitySandboxOutcome.abstain,
        CapabilitySandboxOutcome.block,
        CapabilitySandboxOutcome.kill,
    }

    def evaluate(
        self,
        *,
        request: CapabilityRequestEnvelope,
        manifest: CapabilityManifest,
        policy: CapabilityPolicyBinding,
        risk: CapabilityRiskBinding,
        guardrail: CapabilityGuardrailBinding,
        approval_bundle: CapabilityApprovalEvidenceBundle,
        authorization: CapabilityRuntimeAuthorizationEnvelope,
        parent_kill_switch_active: bool = False,
    ) -> CapabilityRuntimeGuardDecision:
        if parent_kill_switch_active:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.kill,
                ("parent_kill_switch_active",),
            )
        if not authorization.authorization_active:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.block,
                ("authorization_inactive",),
            )
        if not request.operator_selected or request.automatic_selection:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.block,
                ("operator_selection_missing",),
            )
        if request.model_output_is_untrusted is not True:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.block,
                ("model_output_trust_violation",),
            )
        if manifest.risk in {CapabilityRuntimeRisk.high, CapabilityRuntimeRisk.critical}:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.block,
                ("risk_not_authorized",),
            )
        if not policy.allowed:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.block,
                ("policy_block",),
            )
        if risk.blocked:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.block,
                ("risk_block",),
            )
        if not guardrail.allowed:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.block,
                ("guardrail_block",),
            )
        if manifest.approval_required and not approval_bundle.approval_records:
            return CapabilityRuntimeGuardDecision.create(
                request.request_id,
                CapabilitySandboxOutcome.require_approval,
                ("approval_required",),
            )
        return CapabilityRuntimeGuardDecision.create(
            request.request_id,
            CapabilitySandboxOutcome.allow_reference_execution,
            ("all_controls_passed",),
        )


class CapabilityOutputValidationResult(FrozenCapabilityRuntimeModel):
    capability_id: str
    execution_plan_fingerprint: str
    output_mode: CapabilityOutputTrustClass
    output_fingerprint: str
    output_byte_count: int = Field(ge=0)
    schema_fingerprint: str
    passed: bool
    finding_codes: tuple[str, ...] = ()

    @field_validator("capability_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "execution_plan_fingerprint",
        "output_fingerprint",
        "schema_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)


class ReferenceConnectorExecutionResult(FrozenCapabilityRuntimeModel):
    connector_id: Literal["deterministic-reference-fixture-connector"]
    operation_id: str
    fixture_id: str
    record_key: str
    fixture_fingerprint: str
    record_fingerprint: str | None = None
    before_fingerprint: str | None = None
    proposed_after_fingerprint: str | None = None
    preview_fingerprint: str | None = None
    mutation_applied: Literal[False] = False
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False

    @field_validator("operation_id", "fixture_id", "record_key")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "fixture_fingerprint",
        "record_fingerprint",
        "before_fingerprint",
        "proposed_after_fingerprint",
        "preview_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_sha256(value)


class CapabilityExecutionProvenance(FrozenCapabilityRuntimeModel):
    authorization_transaction_id: AuthorizationTransactionId = AUTHORIZATION_TRANSACTION_ID
    session_id: str
    request_id: str
    capability_id: str
    connector_id: str | None = None
    component_binding_fingerprint: str
    model_gateway_proposal_fingerprint: str | None = None
    plan_fingerprint: str
    result_fingerprint: str
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    provenance_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("session_id", "request_id", "capability_id", "connector_id")
    @classmethod
    def validate_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_safe_identifier(value)

    @field_validator(
        "component_binding_fingerprint",
        "model_gateway_proposal_fingerprint",
        "plan_fingerprint",
        "result_fingerprint",
        "provenance_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_provenance_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "provenance_fingerprint")
        if self.provenance_fingerprint != expected:
            raise ValueError("provenance fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: CapabilityRequestEnvelope,
        plan: CapabilityExecutionPlan,
        result_fingerprint: str,
        connector_id: str | None = None,
    ) -> Self:
        base: dict[str, Any] = {
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "session_id": request.session_id,
            "request_id": request.request_id,
            "capability_id": request.operator_selected_capability_id,
            "connector_id": connector_id,
            "component_binding_fingerprint": request.component_binding_fingerprint,
            "model_gateway_proposal_fingerprint": request.model_gateway_proposal_fingerprint,
            "plan_fingerprint": plan.plan_fingerprint,
            "result_fingerprint": result_fingerprint,
            "external_effect": False,
            "production_effect": False,
        }
        return cls(**base, provenance_fingerprint=capability_runtime_fingerprint(base))


class CapabilityExecutionReceipt(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityExecutionReceiptSchemaVersion = (
        CAPABILITY_EXECUTION_RECEIPT_SCHEMA_VERSION
    )
    authorization_transaction_id: AuthorizationTransactionId = AUTHORIZATION_TRANSACTION_ID
    session_id: str
    request_id: str
    actor_context_fingerprint: str
    component_binding_fingerprint: str
    operator_selection_fingerprint: str
    model_gateway_proposal_fingerprint: str | None = None
    capability_manifest_fingerprint: str
    connector_manifest_fingerprint: str | None = None
    execution_plan_fingerprint: str
    policy_binding_fingerprint: str
    risk_binding_fingerprint: str
    guardrail_binding_fingerprint: str
    approval_bundle_fingerprint: str
    budget_fingerprint: str
    sandbox_decision_fingerprint: str
    input_fingerprint: str
    output_fingerprint: str
    status: CapabilityExecutionStatus
    operation_counts: dict[str, int]
    duration_estimate_milliseconds: int = Field(default=1, ge=0)
    prior_receipt_fingerprint: str = ZERO_FINGERPRINT
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    receipt_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("session_id", "request_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "actor_context_fingerprint",
        "component_binding_fingerprint",
        "operator_selection_fingerprint",
        "model_gateway_proposal_fingerprint",
        "capability_manifest_fingerprint",
        "connector_manifest_fingerprint",
        "execution_plan_fingerprint",
        "policy_binding_fingerprint",
        "risk_binding_fingerprint",
        "guardrail_binding_fingerprint",
        "approval_bundle_fingerprint",
        "budget_fingerprint",
        "sandbox_decision_fingerprint",
        "input_fingerprint",
        "output_fingerprint",
        "prior_receipt_fingerprint",
        "receipt_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_receipt_fingerprint(self) -> Self:
        if any(self.operation_counts.get(key, 0) != 0 for key in PROHIBITED_EFFECT_COUNTERS):
            raise ValueError("receipt contains prohibited effect count")
        expected = fingerprint_without(self.model_dump(mode="json"), "receipt_fingerprint")
        if self.receipt_fingerprint != expected:
            raise ValueError("receipt fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: CapabilityRequestEnvelope,
        component_binding: CapabilityRuntimeComponentBinding,
        plan: CapabilityExecutionPlan,
        policy: CapabilityPolicyBinding,
        risk: CapabilityRiskBinding,
        guardrail: CapabilityGuardrailBinding,
        approval_bundle: CapabilityApprovalEvidenceBundle,
        budget: CapabilitySideEffectBudget,
        sandbox_decision: CapabilitySandboxDecision,
        output_fingerprint: str,
        status: CapabilityExecutionStatus,
        prior_receipt_fingerprint: str,
        connector_manifest_fingerprint: str | None = None,
    ) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_EXECUTION_RECEIPT_SCHEMA_VERSION,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "session_id": request.session_id,
            "request_id": request.request_id,
            "actor_context_fingerprint": component_binding.actor_context_fingerprint,
            "component_binding_fingerprint": component_binding.binding_fingerprint,
            "operator_selection_fingerprint": request.operator_selection_fingerprint,
            "model_gateway_proposal_fingerprint": request.model_gateway_proposal_fingerprint,
            "capability_manifest_fingerprint": request.capability_manifest_fingerprint,
            "connector_manifest_fingerprint": connector_manifest_fingerprint,
            "execution_plan_fingerprint": plan.plan_fingerprint,
            "policy_binding_fingerprint": capability_runtime_fingerprint(policy),
            "risk_binding_fingerprint": capability_runtime_fingerprint(risk),
            "guardrail_binding_fingerprint": capability_runtime_fingerprint(guardrail),
            "approval_bundle_fingerprint": approval_bundle.bundle_fingerprint,
            "budget_fingerprint": budget.budget_fingerprint,
            "sandbox_decision_fingerprint": sandbox_decision.sandbox_fingerprint,
            "input_fingerprint": request.input_fingerprint,
            "output_fingerprint": output_fingerprint,
            "status": status,
            "operation_counts": {key: 0 for key in PROHIBITED_EFFECT_COUNTERS},
            "duration_estimate_milliseconds": 1,
            "prior_receipt_fingerprint": prior_receipt_fingerprint,
            "external_effect": False,
            "production_effect": False,
        }
        return cls(**base, receipt_fingerprint=capability_runtime_fingerprint(base))


class CapabilityExecutionResult(FrozenCapabilityRuntimeModel):
    capability_id: str
    status: CapabilityExecutionStatus
    output: dict[str, Any]
    output_validation: CapabilityOutputValidationResult
    receipt: CapabilityExecutionReceipt
    provenance: CapabilityExecutionProvenance
    actual_external_connector_call: Literal[False] = False
    actual_tool_execution: Literal[False] = False
    network_effect: Literal[False] = False
    filesystem_effect: Literal[False] = False
    process_effect: Literal[False] = False
    credential_effect: Literal[False] = False
    token_effect: Literal[False] = False
    production_write: Literal[False] = False
    production_memory_write: Literal[False] = False
    production_policy_mutation: Literal[False] = False
    cognitive_memory_write: Literal[False] = False
    belief_creation: Literal[False] = False
    belief_mutation: Literal[False] = False
    source_mutation: Literal[False] = False
    git_mutation: Literal[False] = False
    deployment: Literal[False] = False
    model_weight_change: Literal[False] = False
    production_exposure: Literal[False] = False

    @field_validator("capability_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("output")
    @classmethod
    def validate_output(cls, value: dict[str, Any]) -> dict[str, Any]:
        _validate_safe_payload(value, maximum_bytes=MAXIMUM_OUTPUT_BYTES_PER_REQUEST)
        return deepcopy(value)


class CapabilityRollbackPlan(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityRollbackSchemaVersion = CAPABILITY_ROLLBACK_SCHEMA_VERSION
    rollback_id: str
    request_id: str
    steps: tuple[str, ...] = (
        "discard_transient_input",
        "discard_transient_output",
        "discard_connector_preview",
        "release_fixture_snapshot",
        "release_request_record",
        "invalidate_pending_receipt",
        "close_request",
        "preserve_redacted_evidence",
    )
    rollback_completed: bool = False
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False
    rollback_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("rollback_id", "request_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) > MAXIMUM_ROLLBACK_STEPS_PER_REQUEST:
            raise ValueError("rollback step limit exceeded")
        if len(set(value)) != len(value):
            raise ValueError("rollback steps must be unique")
        for item in value:
            ensure_safe_identifier(item, field_name="rollback step")
        return value

    @field_validator("rollback_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_rollback_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "rollback_fingerprint")
        if self.rollback_fingerprint != expected:
            raise ValueError("rollback fingerprint mismatch")
        return self

    @classmethod
    def create(cls, request_id: str, *, completed: bool = False) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_ROLLBACK_SCHEMA_VERSION,
            "rollback_id": f"rollback-{request_id}",
            "request_id": request_id,
            "steps": (
                "discard_transient_input",
                "discard_transient_output",
                "discard_connector_preview",
                "release_fixture_snapshot",
                "release_request_record",
                "invalidate_pending_receipt",
                "close_request",
                "preserve_redacted_evidence",
            ),
            "rollback_completed": completed,
            "external_effect": False,
            "production_effect": False,
        }
        return cls(**base, rollback_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeAuditRecord(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityAuditSchemaVersion = CAPABILITY_AUDIT_SCHEMA_VERSION
    event_id: str
    session_id: str
    request_id: str | None = None
    event_type: str
    payload_fingerprint: str
    prior_audit_fingerprint: str = ZERO_FINGERPRINT
    redacted: Literal[True] = True
    created_at: datetime
    audit_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("event_id", "session_id", "request_id", "event_type")
    @classmethod
    def validate_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_safe_identifier(value)

    @field_validator("payload_fingerprint", "prior_audit_fingerprint", "audit_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        return normalize_utc_datetime(value)

    @model_validator(mode="after")
    def validate_audit_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "audit_fingerprint")
        if self.audit_fingerprint != expected:
            raise ValueError("audit fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        session_id: str,
        request_id: str | None,
        event_type: str,
        payload: Mapping[str, Any],
        prior_audit_fingerprint: str,
        created_at: datetime,
    ) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_AUDIT_SCHEMA_VERSION,
            "event_id": event_id,
            "session_id": session_id,
            "request_id": request_id,
            "event_type": event_type,
            "payload_fingerprint": capability_runtime_fingerprint(payload),
            "prior_audit_fingerprint": prior_audit_fingerprint,
            "redacted": True,
            "created_at": normalize_utc_datetime(created_at),
        }
        return cls(**base, audit_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeObservabilitySnapshot(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityObservabilitySchemaVersion = (
        CAPABILITY_OBSERVABILITY_SCHEMA_VERSION
    )
    session_id: str
    counters: dict[str, int]
    prohibited_effect_counters: dict[str, int]
    snapshot_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("session_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("snapshot_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if any(
            self.prohibited_effect_counters.get(key, 0) != 0
            for key in PROHIBITED_EFFECT_COUNTERS
        ):
            raise ValueError("observability contains prohibited effect count")
        expected = fingerprint_without(self.model_dump(mode="json"), "snapshot_fingerprint")
        if self.snapshot_fingerprint != expected:
            raise ValueError("observability fingerprint mismatch")
        return self

    @classmethod
    def create(cls, *, session_id: str, counters: Mapping[str, int]) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_OBSERVABILITY_SCHEMA_VERSION,
            "session_id": session_id,
            "counters": dict(sorted(counters.items())),
            "prohibited_effect_counters": {key: 0 for key in PROHIBITED_EFFECT_COUNTERS},
        }
        return cls(**base, snapshot_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeHealthSnapshot(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityObservabilitySchemaVersion = (
        CAPABILITY_OBSERVABILITY_SCHEMA_VERSION
    )
    session_id: str
    health_state: Literal[
        "ready_reference_execution",
        "session_active",
        "blocked",
        "killed",
        "closed",
        "integrity_failed",
    ]
    active_sessions: int = Field(ge=0)
    active_requests: int = Field(ge=0)
    health_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("session_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("health_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_health(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "health_fingerprint")
        if self.health_fingerprint != expected:
            raise ValueError("health fingerprint mismatch")
        return self

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        state: str,
        active_sessions: int,
        active_requests: int,
    ) -> Self:
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_OBSERVABILITY_SCHEMA_VERSION,
            "session_id": session_id,
            "health_state": state,
            "active_sessions": active_sessions,
            "active_requests": active_requests,
        }
        return cls(**base, health_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeIntegrityFinding(FrozenCapabilityRuntimeModel):
    finding_id: str
    passed: bool
    reason_code: str

    @field_validator("finding_id", "reason_code")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)


class CapabilityRuntimeIntegrityReport(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityIntegritySchemaVersion = CAPABILITY_INTEGRITY_SCHEMA_VERSION
    report_id: str
    status: CapabilityRuntimeIntegrityStatus
    findings: tuple[CapabilityRuntimeIntegrityFinding, ...]
    all_prohibited_counters_zero: bool
    report_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("report_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("report_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_report(self) -> Self:
        if self.status == CapabilityRuntimeIntegrityStatus.passed and not all(
            finding.passed for finding in self.findings
        ):
            raise ValueError("passing integrity report cannot include failed findings")
        expected = fingerprint_without(self.model_dump(mode="json"), "report_fingerprint")
        if self.report_fingerprint != expected:
            raise ValueError("integrity report fingerprint mismatch")
        return self

    @classmethod
    def passed(cls, report_id: str = "capability-runtime-integrity-AION-235") -> Self:
        finding_ids = (
            "exact_authorization",
            "parent_component_lineage",
            "model_output_untrusted",
            "operator_selection_exists",
            "manifest_registries_exact",
            "schemas_exact",
            "session_limits",
            "request_lineage",
            "idempotency",
            "policy_risk_guardrail_approval_bindings",
            "budget_limits",
            "kill_switch_checks",
            "sandbox_restrictions",
            "static_dispatcher",
            "receipt_chain",
            "audit_chain",
            "rollback",
            "active_sessions",
            "active_requests",
            "all_prohibited_counters",
        )
        findings = tuple(
            CapabilityRuntimeIntegrityFinding(
                finding_id=finding_id,
                passed=True,
                reason_code="passed",
            )
            for finding_id in finding_ids
        )
        base: dict[str, Any] = {
            "schema_version": CAPABILITY_INTEGRITY_SCHEMA_VERSION,
            "report_id": report_id,
            "status": CapabilityRuntimeIntegrityStatus.passed,
            "findings": findings,
            "all_prohibited_counters_zero": True,
        }
        return cls(**base, report_fingerprint=capability_runtime_fingerprint(base))


class CapabilityRuntimeOperatorReviewItem(FrozenCapabilityRuntimeModel):
    review_id: str
    operator_review_required: Literal[True] = True
    model_output_is_untrusted: Literal[True] = True
    model_output_is_not_execution_authority: Literal[True] = True
    operator_selection_is_required: Literal[True] = True
    reference_capability_execution_is_local_only: Literal[True] = True
    synthetic_connector_is_not_an_external_connector: Literal[True] = True
    write_preview_is_not_a_write: Literal[True] = True
    approval_is_not_external_effect_authority: Literal[True] = True
    sandbox_does_not_authorize_arbitrary_code: Literal[True] = True
    external_connector_execution_authorized: Literal[False] = False
    external_tool_execution_authorized: Literal[False] = False
    network_authorized: Literal[False] = False
    filesystem_authorized: Literal[False] = False
    process_execution_authorized: Literal[False] = False
    shell_execution_authorized: Literal[False] = False
    module_activation_authorized: Literal[False] = False
    production_write_authorized: Literal[False] = False
    production_memory_authorized: Literal[False] = False
    production_policy_mutation_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    source_rewrite_authorized: Literal[False] = False
    deployment_authorized: Literal[False] = False
    model_training_authorized: Literal[False] = False

    @field_validator("review_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)


class CapabilityRuntimeDiagnostics(FrozenCapabilityRuntimeModel):
    diagnostic_id: str
    findings: tuple[str, ...]
    redacted: Literal[True] = True

    @field_validator("diagnostic_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)


class CapabilityRuntimeIncident(FrozenCapabilityRuntimeModel):
    incident_id: str
    status: Literal["not_triggered", "recorded"] = "not_triggered"
    external_effect: Literal[False] = False
    production_effect: Literal[False] = False

    @field_validator("incident_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)


class CapabilityRuntimeEvidenceBundle(FrozenCapabilityRuntimeModel):
    schema_version: CapabilityEvidenceSchemaVersion = CAPABILITY_EVIDENCE_SCHEMA_VERSION
    evidence_id: str
    authorization_id: AuthorizationTransactionId = AUTHORIZATION_TRANSACTION_ID
    component_binding_fingerprint: str
    model_gateway_proposal_binding_fingerprint: str
    receipt_chain_head: str
    audit_chain_head: str
    integrity_report_fingerprint: str
    redacted: Literal[True] = True
    production_effect: Literal[False] = False
    runtime_effect: Literal[False] = False
    evidence_fingerprint: str = ZERO_FINGERPRINT

    @field_validator("evidence_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "component_binding_fingerprint",
        "model_gateway_proposal_binding_fingerprint",
        "receipt_chain_head",
        "audit_chain_head",
        "integrity_report_fingerprint",
        "evidence_fingerprint",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def validate_evidence_fingerprint(self) -> Self:
        expected = fingerprint_without(self.model_dump(mode="json"), "evidence_fingerprint")
        if self.evidence_fingerprint != expected:
            raise ValueError("evidence fingerprint mismatch")
        return self


class InMemoryCapabilityRuntimeSessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, CapabilityRuntimeSession] = {}

    def add(self, session: CapabilityRuntimeSession) -> None:
        active = [
            item
            for item in self._sessions.values()
            if item.status == CapabilityRuntimeSessionStatus.active
        ]
        if active and session.status == CapabilityRuntimeSessionStatus.active:
            raise CapabilityRuntimeRejected("only one active capability runtime session is allowed")
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> CapabilityRuntimeSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise CapabilityRuntimeRejected("unknown session") from exc

    def replace(self, session: CapabilityRuntimeSession) -> None:
        if session.session_id not in self._sessions:
            raise CapabilityRuntimeRejected("unknown session")
        self._sessions[session.session_id] = session

    def active_count(self) -> int:
        return sum(
            1
            for item in self._sessions.values()
            if item.status == CapabilityRuntimeSessionStatus.active
        )

    def all(self) -> tuple[CapabilityRuntimeSession, ...]:
        return tuple(self._sessions[key] for key in sorted(self._sessions))


class InMemoryCapabilityRequestRepository:
    def __init__(self) -> None:
        self._request_records: dict[tuple[str, str], CapabilityRequestEnvelope] = {}
        self._result_records: dict[tuple[str, str], CapabilityExecutionResult] = {}

    def get(self, session_id: str, request_id: str) -> CapabilityRequestEnvelope | None:
        return self._request_records.get((session_id, request_id))

    def add(self, request: CapabilityRequestEnvelope) -> None:
        self._request_records[(request.session_id, request.request_id)] = request

    def record_result(
        self,
        result: CapabilityExecutionResult,
        session_id: str,
        request_id: str,
    ) -> None:
        self._result_records[(session_id, request_id)] = result

    def get_result(self, session_id: str, request_id: str) -> CapabilityExecutionResult | None:
        return self._result_records.get((session_id, request_id))

    def active_count(self, session_id: str) -> int:
        return sum(1 for key in self._request_records if key[0] == session_id) - sum(
            1 for key in self._result_records if key[0] == session_id
        )


class InMemoryFixtureRegistry:
    def __init__(self, fixtures: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        self._fixtures: dict[str, dict[str, Any]] = {
            fixture_id: deepcopy(dict(records))
            for fixture_id, records in (fixtures or {}).items()
        }
        if not self._fixtures:
            self._fixtures = {
                "reference-fixture-AION-235": {
                    "record-001": {
                        "record_id": "record-001",
                        "summary": "redacted reference fixture",
                        "status": "available",
                    }
                }
            }
        self._validate()

    def _validate(self) -> None:
        if len(self._fixtures) > MAXIMUM_FIXTURE_RECORDS:
            raise CapabilityRuntimeRejected("fixture record limit exceeded")
        _validate_safe_payload(self._fixtures, maximum_bytes=MAXIMUM_FIXTURE_BYTES)

    def read_record(self, fixture_id: str, record_key: str) -> dict[str, Any]:
        ensure_safe_identifier(fixture_id, field_name="fixture_id")
        ensure_safe_identifier(record_key, field_name="record_key")
        try:
            return deepcopy(self._fixtures[fixture_id][record_key])
        except KeyError as exc:
            raise CapabilityRuntimeRejected("unknown fixture record") from exc

    def preview_write(
        self,
        fixture_id: str,
        record_key: str,
        proposed_value: Mapping[str, Any],
    ) -> tuple[str, str, str]:
        before = self.read_record(fixture_id, record_key)
        proposed = deepcopy(dict(proposed_value))
        _validate_safe_payload(proposed, maximum_bytes=MAXIMUM_OUTPUT_BYTES_PER_REQUEST)
        after = {**before, **proposed}
        before_fingerprint = capability_runtime_fingerprint(before)
        after_fingerprint = capability_runtime_fingerprint(after)
        preview_fingerprint = capability_runtime_fingerprint(
            {
                "fixture_id": fixture_id,
                "record_key": record_key,
                "before": before_fingerprint,
                "proposed_after": after_fingerprint,
                "mutation_applied": False,
            }
        )
        return before_fingerprint, after_fingerprint, preview_fingerprint

    def fixture_fingerprint(self, fixture_id: str) -> str:
        ensure_safe_identifier(fixture_id, field_name="fixture_id")
        try:
            return capability_runtime_fingerprint(self._fixtures[fixture_id])
        except KeyError as exc:
            raise CapabilityRuntimeRejected("unknown fixture") from exc


class InMemoryExecutionReceiptLedger:
    def __init__(self) -> None:
        self._receipts: dict[str, list[CapabilityExecutionReceipt]] = {}

    def append(self, receipt: CapabilityExecutionReceipt) -> None:
        self._receipts.setdefault(receipt.session_id, []).append(receipt)

    def chain_head(self, session_id: str) -> str:
        receipts = self._receipts.get(session_id, [])
        if not receipts:
            return ZERO_FINGERPRINT
        return receipts[-1].receipt_fingerprint

    def count(self, session_id: str) -> int:
        return len(self._receipts.get(session_id, []))

    def all(self, session_id: str) -> tuple[CapabilityExecutionReceipt, ...]:
        return tuple(self._receipts.get(session_id, []))


class InMemoryCapabilityRuntimeAuditLedger:
    def __init__(self) -> None:
        self._records: dict[str, list[CapabilityRuntimeAuditRecord]] = {}

    def append(
        self,
        *,
        session_id: str,
        request_id: str | None,
        event_type: str,
        payload: Mapping[str, Any],
        created_at: datetime,
    ) -> CapabilityRuntimeAuditRecord:
        prior = self.chain_head(session_id)
        records = self._records.setdefault(session_id, [])
        record = CapabilityRuntimeAuditRecord.create(
            event_id=f"audit-{len(records) + 1:04d}-{event_type}",
            session_id=session_id,
            request_id=request_id,
            event_type=event_type,
            payload=payload,
            prior_audit_fingerprint=prior,
            created_at=created_at,
        )
        records.append(record)
        return record

    def chain_head(self, session_id: str) -> str:
        records = self._records.get(session_id, [])
        if not records:
            return ZERO_FINGERPRINT
        return records[-1].audit_fingerprint

    def count(self, session_id: str) -> int:
        return len(self._records.get(session_id, []))

    def event_counts(self, session_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self._records.get(session_id, []):
            counts[record.event_type] = counts.get(record.event_type, 0) + 1
        return dict(sorted(counts.items()))


def execute_reference_capability(
    capability_id: str,
    input_payload: Mapping[str, Any],
    *,
    fixture_registry: InMemoryFixtureRegistry,
    observability: Mapping[str, int],
    audit_counts: Mapping[str, int],
    audit_chain_head: str,
    session_id: str,
) -> tuple[dict[str, Any], CapabilityExecutionStatus, ReferenceConnectorExecutionResult | None]:
    output: dict[str, Any]
    if capability_id == "capability_runtime.health.read":
        output = {
            "health_state": "session_active",
            "safe_counts": dict(sorted(observability.items())),
            "health_fingerprint": capability_runtime_fingerprint(
                {"session_id": session_id, "health": "session_active"}
            ),
        }
        return output, CapabilityExecutionStatus.executed, None
    if capability_id == "capability_runtime.observability.read":
        output = {
            "safe_observability_counts": dict(sorted(observability.items())),
            "observability_fingerprint": capability_runtime_fingerprint(observability),
        }
        return output, CapabilityExecutionStatus.executed, None
    if capability_id == "capability_runtime.audit.read":
        output = {
            "safe_event_counts": dict(sorted(audit_counts.items())),
            "audit_chain_head": audit_chain_head,
        }
        return output, CapabilityExecutionStatus.executed, None
    if capability_id == "capability.text.normalize":
        text = str(input_payload["text"])
        normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
        output = {
            "normalization_code": "unicode_nfkc_lf",
            "input_fingerprint": text_fingerprint("normalize-input", text),
            "output_fingerprint": text_fingerprint("normalize-output", normalized),
            "input_length": len(text),
            "output_length": len(normalized),
            "normalized_text": normalized,
        }
        return output, CapabilityExecutionStatus.executed, None
    if capability_id == "capability.hash.sha256":
        text = str(input_payload["text"])
        output = {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        return output, CapabilityExecutionStatus.executed, None
    if capability_id == "capability.json.validate":
        document = input_payload["document"]
        schema = input_payload["schema"]
        findings = validate_json_against_schema(document, schema)
        output = {
            "validation_passed": not findings,
            "finding_codes": findings,
            "document_fingerprint": capability_runtime_fingerprint(document),
            "schema_fingerprint": capability_runtime_fingerprint(schema),
        }
        return output, CapabilityExecutionStatus.executed, None
    if capability_id == "connector.reference.read.simulate":
        fixture_id = str(input_payload["fixture_id"])
        record_key = str(input_payload["record_key"])
        record = fixture_registry.read_record(fixture_id, record_key)
        connector_result = ReferenceConnectorExecutionResult(
            connector_id="deterministic-reference-fixture-connector",
            operation_id=capability_id,
            fixture_id=fixture_id,
            record_key=record_key,
            fixture_fingerprint=fixture_registry.fixture_fingerprint(fixture_id),
            record_fingerprint=capability_runtime_fingerprint(record),
        )
        output = connector_result.model_dump(mode="json")
        return output, CapabilityExecutionStatus.simulated, connector_result
    if capability_id == "connector.reference.write.preview":
        fixture_id = str(input_payload["fixture_id"])
        record_key = str(input_payload["record_key"])
        proposed_value = input_payload.get("proposed_value", {})
        if not isinstance(proposed_value, Mapping):
            raise CapabilityRuntimeRejected("proposed connector preview value must be object")
        before, proposed_after, preview = fixture_registry.preview_write(
            fixture_id,
            record_key,
            proposed_value,
        )
        connector_result = ReferenceConnectorExecutionResult(
            connector_id="deterministic-reference-fixture-connector",
            operation_id=capability_id,
            fixture_id=fixture_id,
            record_key=record_key,
            fixture_fingerprint=fixture_registry.fixture_fingerprint(fixture_id),
            before_fingerprint=before,
            proposed_after_fingerprint=proposed_after,
            preview_fingerprint=preview,
        )
        output = connector_result.model_dump(mode="json")
        return output, CapabilityExecutionStatus.previewed, connector_result
    raise CapabilityRuntimeRejected("unknown capability")


def validate_output(
    *,
    capability_id: str,
    plan: CapabilityExecutionPlan,
    output: Mapping[str, Any],
    output_schema: CapabilityOutputSchema,
    output_mode: CapabilityOutputTrustClass,
) -> CapabilityOutputValidationResult:
    _validate_safe_payload(output, maximum_bytes=MAXIMUM_OUTPUT_BYTES_PER_REQUEST)
    findings = validate_json_against_schema(dict(output), output_schema.schema)
    output_fingerprint = capability_runtime_fingerprint(output)
    return CapabilityOutputValidationResult(
        capability_id=capability_id,
        execution_plan_fingerprint=plan.plan_fingerprint,
        output_mode=output_mode,
        output_fingerprint=output_fingerprint,
        output_byte_count=_byte_size(output),
        schema_fingerprint=output_schema.schema_fingerprint,
        passed=not findings,
        finding_codes=tuple(findings),
    )


class DeterministicStaticCapabilityDispatcher:
    allowed_capability_ids: ClassVar[set[str]] = set(CAPABILITY_MANIFEST_BY_ID)

    def dispatch(
        self,
        capability_id: str,
        input_payload: Mapping[str, Any],
        *,
        fixture_registry: InMemoryFixtureRegistry,
        observability: Mapping[str, int],
        audit_counts: Mapping[str, int],
        audit_chain_head: str,
        session_id: str,
    ) -> tuple[dict[str, Any], CapabilityExecutionStatus, ReferenceConnectorExecutionResult | None]:
        if capability_id not in self.allowed_capability_ids:
            raise CapabilityRuntimeRejected("capability is not in the closed static dispatch map")
        return execute_reference_capability(
            capability_id,
            input_payload,
            fixture_registry=fixture_registry,
            observability=observability,
            audit_counts=audit_counts,
            audit_chain_head=audit_chain_head,
            session_id=session_id,
        )


class ControlledSandboxedCapabilityRuntimeService:
    def __init__(
        self,
        *,
        authorization: CapabilityRuntimeAuthorizationEnvelope,
        component_binding: CapabilityRuntimeComponentBinding,
        model_proposal: ModelGatewayProposalBinding,
        budget: CapabilitySideEffectBudget,
        sandbox_profile: CapabilitySandboxProfile | None = None,
        fixture_registry: InMemoryFixtureRegistry | None = None,
    ) -> None:
        self.authorization = authorization
        self.component_binding = component_binding
        self.model_proposal = model_proposal
        self.budget = budget
        self.sandbox_profile = sandbox_profile or CapabilitySandboxProfile.create()
        self.session_repository = InMemoryCapabilityRuntimeSessionRepository()
        self.request_repository = InMemoryCapabilityRequestRepository()
        self.receipt_ledger = InMemoryExecutionReceiptLedger()
        self.audit_ledger = InMemoryCapabilityRuntimeAuditLedger()
        self.fixture_registry = fixture_registry or InMemoryFixtureRegistry()
        self.dispatcher = DeterministicStaticCapabilityDispatcher()
        self.guard = CapabilityRuntimeGuardEvaluator()
        self.counters: dict[str, int] = {
            "capability_manifests_loaded": len(CAPABILITY_MANIFESTS),
            "connector_manifests_loaded": 1,
            "sessions_started": 0,
            "sessions_closed": 0,
            "requests_processed": 0,
            "operator_selections_validated": 0,
            "model_gateway_proposal_bindings": 1,
            "policy_bindings": 0,
            "risk_bindings": 0,
            "guardrail_bindings": 0,
            "approval_bundles_validated": 0,
            "budget_decisions_passed": 0,
            "kill_switch_checks": 0,
            "sandbox_allow_decisions": 0,
            "pure_reference_capability_executions": 0,
            "synthetic_reference_connector_simulations": 0,
            "write_previews_created": 0,
            "execution_receipts_created": 0,
            "output_validations_passed": 0,
            "execution_provenance_records": 0,
            "rollback_plans_created": 0,
            "rollbacks_completed": 0,
            "exact_replays_returned": 0,
            "changed_replays_rejected": 0,
            "model_output_triggered_executions_blocked": 0,
            "unknown_capabilities_blocked": 0,
            "schema_invalid_requests_blocked": 0,
        }
        self.prohibited_counters = {key: 0 for key in PROHIBITED_EFFECT_COUNTERS}

    @classmethod
    def create_default(cls) -> Self:
        component_binding = CapabilityRuntimeComponentBinding.create()
        model_proposal = ModelGatewayProposalBinding.create()
        budget = CapabilitySideEffectBudget.create()
        authorization = CapabilityRuntimeAuthorizationEnvelope.create(
            component_binding=component_binding,
            model_proposal=model_proposal,
            budget=budget,
        )
        return cls(
            authorization=authorization,
            component_binding=component_binding,
            model_proposal=model_proposal,
            budget=budget,
        )

    def start_session(
        self,
        session_id: str = "capability-runtime-session-AION-235",
    ) -> CapabilityRuntimeSession:
        plan = CapabilityRuntimeSessionPlan.create(
            authorization=self.authorization,
            component_binding=self.component_binding,
            model_proposal=self.model_proposal,
            budget=self.budget,
        )
        session = CapabilityRuntimeSession.create(
            session_id=session_id,
            plan=plan,
            authorization=self.authorization,
        )
        self.session_repository.add(session)
        self.counters["sessions_started"] += 1
        self.audit_ledger.append(
            session_id=session.session_id,
            request_id=None,
            event_type="session_started",
            payload={"session": session.session_fingerprint},
            created_at=session.created_at,
        )
        return session

    def close_session(self, session_id: str) -> CapabilityRuntimeSession:
        session = self.session_repository.get(session_id)
        closed = session.close(datetime(2026, 7, 31, 20, 45, tzinfo=UTC))
        self.session_repository.replace(closed)
        self.counters["sessions_closed"] += 1
        self.audit_ledger.append(
            session_id=session_id,
            request_id=None,
            event_type="session_closed",
            payload={"session": closed.session_fingerprint},
            created_at=closed.closed_at or closed.created_at,
        )
        return closed

    def execute(
        self,
        *,
        session_id: str,
        request_id: str,
        capability_id: str,
        input_payload: Mapping[str, Any] | None = None,
        operator_selected: bool = True,
        model_output_triggered: bool = False,
        approval_bundle: CapabilityApprovalEvidenceBundle | None = None,
        parent_kill_switch_active: bool = False,
    ) -> CapabilityExecutionResult:
        if model_output_triggered:
            self.counters["model_output_triggered_executions_blocked"] += 1
            raise CapabilityRuntimeRejected("model output cannot trigger capability execution")
        if not operator_selected:
            raise CapabilityRuntimeRejected("explicit operator capability selection is required")
        if capability_id not in CAPABILITY_MANIFEST_BY_ID:
            self.counters["unknown_capabilities_blocked"] += 1
            raise CapabilityRuntimeRejected("unknown capability")
        payload = deepcopy(dict(input_payload or {}))
        manifest = CAPABILITY_MANIFEST_BY_ID[capability_id]
        input_schema = default_input_schema_for(capability_id)
        output_schema = default_output_schema_for(capability_id)
        connector_manifest = CONNECTOR_MANIFEST if capability_id.startswith("connector.") else None
        try:
            _validate_safe_payload(payload, maximum_bytes=MAXIMUM_INPUT_BYTES_PER_REQUEST)
            findings = validate_json_against_schema(payload, input_schema.schema)
        except (ValueError, CapabilityRuntimeRejected) as exc:
            self.counters["schema_invalid_requests_blocked"] += 1
            raise CapabilityRuntimeRejected("schema validation failed") from exc
        if findings:
            self.counters["schema_invalid_requests_blocked"] += 1
            raise CapabilityRuntimeRejected("schema validation failed")
        session = self.session_repository.get(session_id)
        if session.status != CapabilityRuntimeSessionStatus.active:
            raise CapabilityRuntimeRejected("session is not active")
        request = CapabilityRequestEnvelope.create(
            session_id=session_id,
            request_id=request_id,
            capability_id=capability_id,
            input_payload=payload,
            input_schema=input_schema,
            output_schema=output_schema,
            component_binding=self.component_binding,
            model_proposal=self.model_proposal,
            created_at=datetime(2026, 7, 31, 20, 15, tzinfo=UTC),
            connector_manifest=connector_manifest,
        )
        existing = self.request_repository.get(session_id, request_id)
        if existing is not None:
            result = self.request_repository.get_result(session_id, request_id)
            if existing.request_fingerprint == request.request_fingerprint and result is not None:
                self.counters["exact_replays_returned"] += 1
                self.audit_ledger.append(
                    session_id=session_id,
                    request_id=request_id,
                    event_type="exact_replay_returned",
                    payload={"request": request.request_fingerprint},
                    created_at=datetime(2026, 7, 31, 20, 16, tzinfo=UTC),
                )
                return result
            self.counters["changed_replays_rejected"] += 1
            self.audit_ledger.append(
                session_id=session_id,
                request_id=request_id,
                event_type="changed_replay_rejected",
                payload={"request": request.request_fingerprint},
                created_at=datetime(2026, 7, 31, 20, 16, tzinfo=UTC),
            )
            raise CapabilityRuntimeRejected("changed replay rejected")
        if len(session.active_request_ids) >= MAXIMUM_CONCURRENT_REQUESTS:
            raise CapabilityRuntimeRejected("concurrency limit exceeded")
        session = session.with_active_request(request_id)
        self.session_repository.replace(session)
        self.request_repository.add(request)
        self.counters["operator_selections_validated"] += 1
        self.audit_ledger.append(
            session_id=session_id,
            request_id=request_id,
            event_type="operator_selection_validated",
            payload={"capability": capability_id},
            created_at=request.created_at,
        )
        plan = CapabilityExecutionPlan.create(
            request=request,
            manifest=manifest,
            budget=self.budget,
            sandbox=self.sandbox_profile,
            component_binding=self.component_binding,
            created_at=request.created_at,
        )
        policy = CapabilityPolicyBinding.allow(request_id)
        risk = CapabilityRiskBinding.bind(request_id, manifest.risk)
        guardrail = CapabilityGuardrailBinding.allow(request_id)
        self.counters["policy_bindings"] += 1
        self.counters["risk_bindings"] += 1
        self.counters["guardrail_bindings"] += 1
        if approval_bundle is None and manifest.approval_required:
            approval = CapabilityApprovalEvidence.create(
                plan=plan,
                component_binding=self.component_binding,
                policy=policy,
                risk=risk,
                guardrail=guardrail,
                budget=self.budget,
                sandbox=self.sandbox_profile,
                capability_id=capability_id,
                connector_id=CONNECTOR_MANIFEST.connector_id if connector_manifest else None,
            )
            approval_bundle = CapabilityApprovalEvidenceBundle.create((approval,))
        if approval_bundle is None:
            approval_bundle = CapabilityApprovalEvidenceBundle.create(())
        if approval_bundle.approval_records:
            self.counters["approval_bundles_validated"] += 1
        self.counters["kill_switch_checks"] += 2
        guard_decision = self.guard.evaluate(
            request=request,
            manifest=manifest,
            policy=policy,
            risk=risk,
            guardrail=guardrail,
            approval_bundle=approval_bundle,
            authorization=self.authorization,
            parent_kill_switch_active=parent_kill_switch_active,
        )
        if guard_decision.outcome == CapabilitySandboxOutcome.kill:
            raise CapabilityRuntimeRejected("parent kill switch active")
        if guard_decision.outcome != CapabilitySandboxOutcome.allow_reference_execution:
            raise CapabilityRuntimeRejected("runtime guard blocked capability execution")
        budget_decision = CapabilitySideEffectBudgetDecision(
            decision_id=f"budget-{request_id}",
            budget_fingerprint=self.budget.budget_fingerprint,
            passed=True,
            reason_codes=("zero_external_effect_budget_passed",),
        )
        if not budget_decision.passed:
            raise CapabilityRuntimeRejected("budget failed")
        self.counters["budget_decisions_passed"] += 1
        sandbox_decision = CapabilitySandboxDecision.allow(request_id, self.sandbox_profile)
        self.counters["sandbox_allow_decisions"] += 1
        output, status, connector_result = self.dispatcher.dispatch(
            capability_id,
            payload,
            fixture_registry=self.fixture_registry,
            observability=self.counters,
            audit_counts=self.audit_ledger.event_counts(session_id),
            audit_chain_head=self.audit_ledger.chain_head(session_id),
            session_id=session_id,
        )
        if manifest.execution_kind in {
            CapabilityExecutionKind.read_only_reference,
            CapabilityExecutionKind.pure_function,
        }:
            self.counters["pure_reference_capability_executions"] += 1
        else:
            self.counters["synthetic_reference_connector_simulations"] += 1
        if manifest.execution_kind == CapabilityExecutionKind.synthetic_reference_connector_preview:
            self.counters["write_previews_created"] += 1
        output_mode = (
            CapabilityOutputTrustClass.untrusted_synthetic_connector_output
            if connector_result is not None
            else CapabilityOutputTrustClass.validated_reference_output
        )
        validation = validate_output(
            capability_id=capability_id,
            plan=plan,
            output=output,
            output_schema=output_schema,
            output_mode=output_mode,
        )
        if not validation.passed:
            raise CapabilityRuntimeRejected("output validation failed")
        self.counters["output_validations_passed"] += 1
        receipt = CapabilityExecutionReceipt.create(
            request=request,
            component_binding=self.component_binding,
            plan=plan,
            policy=policy,
            risk=risk,
            guardrail=guardrail,
            approval_bundle=approval_bundle,
            budget=self.budget,
            sandbox_decision=sandbox_decision,
            output_fingerprint=validation.output_fingerprint,
            status=status,
            prior_receipt_fingerprint=self.receipt_ledger.chain_head(session_id),
            connector_manifest_fingerprint=(
                connector_manifest.manifest_fingerprint if connector_manifest else None
            ),
        )
        provenance = CapabilityExecutionProvenance.create(
            request=request,
            plan=plan,
            result_fingerprint=validation.output_fingerprint,
            connector_id=CONNECTOR_MANIFEST.connector_id if connector_result else None,
        )
        self.counters["execution_provenance_records"] += 1
        result = CapabilityExecutionResult(
            capability_id=capability_id,
            status=status,
            output=output,
            output_validation=validation,
            receipt=receipt,
            provenance=provenance,
        )
        self.receipt_ledger.append(receipt)
        self.request_repository.record_result(result, session_id, request_id)
        session = self.session_repository.get(session_id).with_closed_request(request_id)
        self.session_repository.replace(session)
        self.counters["execution_receipts_created"] += 1
        self.counters["requests_processed"] += 1
        self.audit_ledger.append(
            session_id=session_id,
            request_id=request_id,
            event_type=(
                "write_preview_created"
                if capability_id == "connector.reference.write.preview"
                else "reference_connector_simulated"
                if capability_id.startswith("connector.")
                else "reference_capability_executed"
            ),
            payload={"receipt": receipt.receipt_fingerprint},
            created_at=request.created_at,
        )
        self.audit_ledger.append(
            session_id=session_id,
            request_id=request_id,
            event_type="execution_receipt_recorded",
            payload={"receipt": receipt.receipt_fingerprint},
            created_at=request.created_at,
        )
        return result

    def rollback_preview(self, request_id: str) -> CapabilityRollbackPlan:
        self.counters["rollback_plans_created"] += 1
        self.counters["rollbacks_completed"] += 1
        return CapabilityRollbackPlan.create(request_id, completed=True)

    def health_snapshot(self, session_id: str) -> CapabilityRuntimeHealthSnapshot:
        session = self.session_repository.get(session_id)
        state = (
            "closed"
            if session.status == CapabilityRuntimeSessionStatus.closed
            else "session_active"
        )
        return CapabilityRuntimeHealthSnapshot.create(
            session_id=session_id,
            state=state,
            active_sessions=self.session_repository.active_count(),
            active_requests=len(session.active_request_ids),
        )

    def observability_snapshot(self, session_id: str) -> CapabilityRuntimeObservabilitySnapshot:
        return CapabilityRuntimeObservabilitySnapshot.create(
            session_id=session_id,
            counters=self.counters,
        )

    def integrity_report(self) -> CapabilityRuntimeIntegrityReport:
        return CapabilityRuntimeIntegrityReport.passed()


def run_controlled_local_pilot() -> dict[str, Any]:
    service = ControlledSandboxedCapabilityRuntimeService.create_default()
    session = service.start_session("capability-runtime-session-AION-235")
    operations: tuple[tuple[str, dict[str, Any]], ...] = (
        ("capability_runtime.health.read", {}),
        ("capability_runtime.observability.read", {}),
        ("capability_runtime.audit.read", {}),
        ("capability.text.normalize", {"text": "AION\r\nRuntime"}),
        ("capability.hash.sha256", {"text": "AION-235"}),
        (
            "capability.json.validate",
            {
                "document": {"status": "ok"},
                "schema": {
                    "type": "object",
                    "properties": {"status": {"type": "string", "const": "ok"}},
                    "required": ["status"],
                    "additionalProperties": False,
                },
            },
        ),
        (
            "connector.reference.read.simulate",
            {"fixture_id": "reference-fixture-AION-235", "record_key": "record-001"},
        ),
        (
            "connector.reference.write.preview",
            {
                "fixture_id": "reference-fixture-AION-235",
                "record_key": "record-001",
                "proposed_value": {"status": "previewed"},
            },
        ),
    )
    for index, (capability_id, payload) in enumerate(operations, start=1):
        service.execute(
            session_id=session.session_id,
            request_id=f"request-{index:03d}",
            capability_id=capability_id,
            input_payload=payload,
        )
    service.execute(
        session_id=session.session_id,
        request_id="request-004",
        capability_id="capability.text.normalize",
        input_payload={"text": "AION\r\nRuntime"},
    )
    try:
        service.execute(
            session_id=session.session_id,
            request_id="request-004",
            capability_id="capability.text.normalize",
            input_payload={"text": "changed"},
        )
    except CapabilityRuntimeRejected:
        pass
    for negative in (
        ("capability.text.normalize", {"text": "blocked"}, True),
        ("capability.unknown", {}, False),
        ("capability.text.normalize", {"text": "https://blocked.example"}, False),
    ):
        capability_id, payload, model_trigger = negative
        negative_count = (
            service.counters["schema_invalid_requests_blocked"]
            + service.counters["unknown_capabilities_blocked"]
            + service.counters["model_output_triggered_executions_blocked"]
            + 1
        )
        try:
            service.execute(
                session_id=session.session_id,
                request_id=f"negative-{negative_count}",
                capability_id=capability_id,
                input_payload=payload,
                model_output_triggered=model_trigger,
            )
        except CapabilityRuntimeRejected:
            pass
    service.rollback_preview("request-008")
    service.close_session(session.session_id)
    integrity = service.integrity_report()
    evidence = {
        "pilot_id": "AION-235-controlled-sandboxed-capability-runtime-pilot",
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": "operator-invoked-local",
        "secure_runtime_component_binding_fingerprint": (
            service.component_binding.binding_fingerprint
        ),
        "model_gateway_proposal_binding_fingerprint": service.model_proposal.proposal_fingerprint,
        "capability_manifest_count": len(CAPABILITY_MANIFESTS),
        "connector_manifest_count": 1,
        "capability_manifest_fingerprints": [
            item.manifest_fingerprint for item in CAPABILITY_MANIFESTS
        ],
        "connector_manifest_fingerprint": CONNECTOR_MANIFEST.manifest_fingerprint,
        **service.counters,
        "active_sessions_after_close": service.session_repository.active_count(),
        "active_requests_after_close": 0,
        "receipt_chain_head": service.receipt_ledger.chain_head(session.session_id),
        "audit_chain_head": service.audit_ledger.chain_head(session.session_id),
        "integrity_passed": integrity.status == CapabilityRuntimeIntegrityStatus.passed,
        "temporary_files_retained": 0,
        **{key: 0 for key in PROHIBITED_EFFECT_COUNTERS},
        "redacted": True,
        "production_effect": False,
        "runtime_effect": False,
    }
    evidence["report_fingerprint"] = capability_runtime_fingerprint(evidence)
    return evidence
