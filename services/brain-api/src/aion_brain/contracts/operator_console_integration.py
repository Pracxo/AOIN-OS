"""AION-237 controlled local Operator Console integration contracts."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

OPERATOR_CONSOLE_CONTRACT_SCHEMA_VERSION = "aion-operator-console-integration/v1"
OPERATOR_CONSOLE_AUTHORIZATION_SCHEMA_VERSION = "aion-operator-console-authorization/v1"
OPERATOR_CONSOLE_COMPONENT_BINDING_SCHEMA_VERSION = (
    "aion-operator-console-component-binding/v1"
)
OPERATOR_CONSOLE_SESSION_SCHEMA_VERSION = "aion-operator-console-session/v1"
OPERATOR_CONSOLE_ROUTE_MANIFEST_SCHEMA_VERSION = "aion-operator-console-route-manifest/v1"
OPERATOR_CONSOLE_ORIGIN_POLICY_SCHEMA_VERSION = "aion-operator-console-origin-policy/v1"
OPERATOR_CONSOLE_NONCE_SCHEMA_VERSION = "aion-operator-console-mutation-nonce/v1"
OPERATOR_CONSOLE_HTTP_REQUEST_SCHEMA_VERSION = "aion-operator-console-http-request/v1"
OPERATOR_CONSOLE_HTTP_RESPONSE_SCHEMA_VERSION = "aion-operator-console-http-response/v1"
OPERATOR_CONSOLE_ACTION_SCHEMA_VERSION = "aion-operator-console-action/v1"
OPERATOR_CONSOLE_PROJECTION_SCHEMA_VERSION = "aion-operator-console-projection/v1"
OPERATOR_CONSOLE_AUDIT_SCHEMA_VERSION = "aion-operator-console-audit/v1"
OPERATOR_CONSOLE_OBSERVABILITY_SCHEMA_VERSION = "aion-operator-console-observability/v1"
OPERATOR_CONSOLE_INTEGRITY_SCHEMA_VERSION = "aion-operator-console-integrity/v1"
OPERATOR_CONSOLE_EVIDENCE_SCHEMA_VERSION = "aion-operator-console-evidence/v1"

PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
AUTHORIZATION_TRANSACTION_ID = "AION-236-SRI-0004"
APPROVAL_RECORD_ID = "AION-236-SRI-0004"
IMPLEMENTATION_TASK = "AION-237"
FORMAL_CLOSEOUT_TASK = "AION-238"
AUTHORIZATION_SCOPE = (
    "authenticated-local-loopback-same-origin-operator-console-bridge-secure-session-"
    "bootstrap-live-read-projection-explicit-model-simulation-explicit-reference-"
    "capability-execution-synthetic-connector-preview-request-nonce-origin-host-csp-"
    "kill-switch-audit-receipt-integrity-integrated-pilot-no-external-effect-core"
)

SECURE_RUNTIME_IMPLEMENTATION_TASK = "AION-231"
SECURE_RUNTIME_AUTHORIZATION_ID = "AION-230-SRI-0001"
MODEL_GATEWAY_IMPLEMENTATION_TASK = "AION-233"
MODEL_GATEWAY_AUTHORIZATION_ID = "AION-232-SRI-0002"
CAPABILITY_RUNTIME_IMPLEMENTATION_TASK = "AION-235"
CAPABILITY_RUNTIME_AUTHORIZATION_ID = "AION-234-SRI-0003"

LOOPBACK_BIND_HOST = "127.0.0.1"
LOCAL_CONFIRMATION_TEXT = "RUN_CONTROLLED_OPERATOR_CONSOLE_INTEGRATION"
CONFIRM_MODEL_TEXT = "SIMULATE_REFERENCE_TEXT_MODEL"
CONFIRM_MODEL_STRUCTURED = "SIMULATE_REFERENCE_STRUCTURED_MODEL"
CONFIRM_CAPABILITY = "EXECUTE_REFERENCE_CAPABILITY"
CONFIRM_CONNECTOR_READ = "SIMULATE_REFERENCE_CONNECTOR_READ"
CONFIRM_CONNECTOR_PREVIEW = "PREVIEW_REFERENCE_CONNECTOR_WRITE"
CONFIRM_KILL = "ACTIVATE_LOCAL_KILL_SWITCH"
CONFIRM_CLOSE = "CLOSE_LOCAL_OPERATOR_SESSION"

MUTATION_NONCE_REQUEST_HEADER = "X-AION-Mutation-Nonce"
MUTATION_NONCE_RESPONSE_HEADER = "X-AION-Mutation-Nonce"
OPERATOR_CONFIRMATION_HEADER = "X-AION-Operator-Confirmation"
ZERO_FINGERPRINT = "0" * 64

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "connect-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'none'"
)

SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Connection": "close",
}

STATIC_ASSET_MIME_TYPES: dict[str, str] = {
    "index.html": "text/html; charset=utf-8",
    "styles.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "live-console.js": "text/javascript; charset=utf-8",
}
STATIC_ASSET_ROUTES: dict[str, str] = {
    "/": "index.html",
    "/index.html": "index.html",
    "/styles.css": "styles.css",
    "/app.js": "app.js",
    "/live-console.js": "live-console.js",
}

POSITIVE_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_operator_console_sessions": 1,
    "maximum_sessions_per_operator_run": 2,
    "maximum_loopback_listeners": 1,
    "maximum_loopback_bind_attempts": 10,
    "maximum_routes": 10,
    "maximum_static_assets": 5,
    "maximum_session_seconds": 3600,
    "maximum_idle_seconds": 900,
    "maximum_requests_per_session": 200,
    "maximum_concurrent_requests": 4,
    "maximum_request_body_bytes": 262144,
    "maximum_response_body_bytes": 1048576,
    "maximum_json_depth": 16,
    "maximum_json_items_per_request": 1000,
    "maximum_bootstrap_reads_per_session": 5,
    "maximum_status_reads_per_session": 100,
    "maximum_health_reads_per_session": 100,
    "maximum_observability_reads_per_session": 100,
    "maximum_audit_reads_per_session": 50,
    "maximum_model_simulations_per_session": 20,
    "maximum_capability_executions_per_session": 50,
    "maximum_synthetic_connector_simulations_per_session": 20,
    "maximum_write_previews_per_session": 10,
    "maximum_kill_switch_activations_per_session": 1,
    "maximum_session_close_requests_per_session": 1,
    "maximum_mutation_nonce_rotations_per_session": 100,
    "maximum_operator_confirmations_per_session": 100,
    "maximum_receipt_projections_per_session": 2000,
    "maximum_audit_records_per_session": 10000,
    "maximum_console_event_records_per_session": 5000,
    "maximum_trace_bytes_per_session": 4194304,
    "maximum_pilot_loopback_http_requests": 50,
    "maximum_pilot_action_requests": 16,
}

ZERO_EFFECT_LIMIT_NAMES: tuple[str, ...] = (
    "maximum_public_listeners",
    "maximum_non_loopback_listeners",
    "maximum_zero_address_bindings",
    "maximum_ipv6_unspecified_bindings",
    "maximum_public_network_calls",
    "maximum_external_network_egress_calls",
    "maximum_dns_resolutions",
    "maximum_cors_wildcards",
    "maximum_cross_origin_action_requests",
    "maximum_browser_cookies_persisted",
    "maximum_browser_local_storage_writes",
    "maximum_browser_session_storage_writes",
    "maximum_browser_indexeddb_writes",
    "maximum_service_workers_registered",
    "maximum_websocket_connections",
    "maximum_server_sent_event_connections",
    "maximum_external_scripts_loaded",
    "maximum_external_styles_loaded",
    "maximum_external_fonts_loaded",
    "maximum_external_images_loaded",
    "maximum_login_forms",
    "maximum_password_inputs",
    "maximum_credential_inputs",
    "maximum_token_inputs",
    "maximum_session_tokens_issued",
    "maximum_access_tokens_issued",
    "maximum_refresh_tokens_issued",
    "maximum_file_uploads",
    "maximum_arbitrary_filesystem_reads",
    "maximum_filesystem_writes",
    "maximum_directory_mutations",
    "maximum_process_spawns",
    "maximum_shell_commands",
    "maximum_subprocess_executions",
    "maximum_browser_automation_actions",
    "maximum_dynamic_imports",
    "maximum_eval_executions",
    "maximum_exec_executions",
    "maximum_packages_installed",
    "maximum_modules_activated",
    "maximum_automatic_model_requests",
    "maximum_model_output_triggered_executions",
    "maximum_automatic_capability_selections",
    "maximum_automatic_capability_executions",
    "maximum_automatic_connector_executions",
    "maximum_model_provider_calls",
    "maximum_provider_network_egress_calls",
    "maximum_external_connector_calls",
    "maximum_external_tool_executions",
    "maximum_actual_tool_executions",
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
ZERO_EFFECT_LIMITS: dict[str, int] = {name: 0 for name in ZERO_EFFECT_LIMIT_NAMES}
ALL_RESOURCE_LIMITS: dict[str, int] = {**POSITIVE_RESOURCE_LIMITS, **ZERO_EFFECT_LIMITS}

AUTHORIZED_CAPABILITY_FLAGS: tuple[str, ...] = (
    "local_loopback_listener_available",
    "same_origin_static_asset_serving_available",
    "exact_static_asset_allowlist_available",
    "bounded_route_manifest_available",
    "loopback_host_validation_available",
    "same_origin_validation_available",
    "ephemeral_mutation_nonce_available",
    "mutation_nonce_rotation_available",
    "strict_content_type_validation_available",
    "strict_security_headers_available",
    "strict_content_security_policy_available",
    "operator_console_session_bootstrap_available",
    "status_read_projection_available",
    "health_read_projection_available",
    "observability_read_projection_available",
    "audit_read_projection_available",
    "explicit_model_simulation_request_available",
    "explicit_reference_capability_request_available",
    "explicit_synthetic_connector_request_available",
    "explicit_write_preview_request_available",
    "explicit_operator_confirmation_required",
    "kill_switch_activation_available",
    "session_close_available",
    "redacted_response_projection_available",
    "receipt_projection_available",
    "audit_projection_available",
    "operator_console_integrity_audit_available",
    "operator_console_health_readiness_available",
    "static_offline_fallback_mode_available",
    "live_mode_explicit_activation_required",
    "accessible_operator_controls_available",
)

PROHIBITED_CAPABILITY_FLAGS: tuple[str, ...] = (
    "public_listener_enabled",
    "non_loopback_listener_enabled",
    "zero_address_binding_enabled",
    "ipv6_unspecified_binding_enabled",
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "cors_wildcard_enabled",
    "cross_origin_action_requests_enabled",
    "browser_cookie_persistence_enabled",
    "browser_local_storage_enabled",
    "browser_session_storage_enabled",
    "browser_indexeddb_enabled",
    "service_worker_enabled",
    "websocket_enabled",
    "server_sent_events_enabled",
    "external_script_loading_enabled",
    "external_style_loading_enabled",
    "external_font_loading_enabled",
    "external_image_loading_enabled",
    "login_form_enabled",
    "password_input_enabled",
    "credential_input_enabled",
    "token_input_enabled",
    "browser_identity_assertion_input_enabled",
    "browser_public_key_input_enabled",
    "persistent_browser_session_enabled",
    "session_token_issuance_enabled",
    "access_token_issuance_enabled",
    "refresh_token_enabled",
    "arbitrary_route_registration_enabled",
    "file_upload_enabled",
    "arbitrary_filesystem_read_enabled",
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
    "automatic_model_request_enabled",
    "model_output_triggered_execution_enabled",
    "automatic_capability_selection_enabled",
    "automatic_capability_execution_enabled",
    "automatic_connector_execution_enabled",
    "actual_model_provider_call_enabled",
    "provider_network_egress_enabled",
    "external_connector_execution_enabled",
    "external_tool_execution_enabled",
    "actual_tool_execution_enabled",
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

PROHIBITED_COUNTER_NAMES: tuple[str, ...] = tuple(
    name.removeprefix("maximum_") for name in ZERO_EFFECT_LIMIT_NAMES
)

ACCEPTED_REFERENCE_CAPABILITY_IDS: tuple[str, ...] = (
    "capability_runtime.health.read",
    "capability_runtime.observability.read",
    "capability_runtime.audit.read",
    "capability.text.normalize",
    "capability.hash.sha256",
    "capability.json.validate",
)
ACCEPTED_CONNECTOR_OPERATIONS: tuple[str, str] = (
    "connector.reference.read.simulate",
    "connector.reference.write.preview",
)

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,191}$")
LOWER_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PROTECTED_MATERIAL_MARKERS = (
    "raw_assertion",
    "raw_signature",
    "private_key",
    "api_key",
    "password",
    "credential",
    "secret",
    "token",
    "cookie",
    "bearer",
    "authorization_header",
    "hidden_reasoning",
    "chain_of_thought",
    "raw_prompt",
    "raw_model_response",
    "raw_capability_input",
    "raw_capability_output",
    "raw_connector_fixture",
)


class OperatorConsoleMode(StrEnum):
    static_offline = "static_offline"
    live_local_loopback = "live_local_loopback"
    integrated_pilot = "integrated_pilot"


class OperatorConsoleSessionStatus(StrEnum):
    drafted = "drafted"
    authorized = "authorized"
    active = "active"
    closing = "closing"
    closed = "closed"
    killed = "killed"
    expired = "expired"
    blocked = "blocked"
    failed = "failed"


class OperatorConsoleRouteKind(StrEnum):
    static_asset = "static_asset"
    read_projection = "read_projection"
    model_simulation = "model_simulation"
    capability_execution = "capability_execution"
    connector_simulation = "connector_simulation"
    kill = "kill"
    session_close = "session_close"


class OperatorConsoleHttpDisposition(StrEnum):
    served = "served"
    accepted = "accepted"
    blocked = "blocked"
    rejected = "rejected"
    killed = "killed"
    closed = "closed"
    failed = "failed"


class OperatorConsoleNonceStatus(StrEnum):
    issued = "issued"
    current = "current"
    consumed = "consumed"
    rotated = "rotated"
    stale = "stale"
    invalidated = "invalidated"
    expired = "expired"


class OperatorConsoleOriginDecision(StrEnum):
    allow_same_origin = "allow_same_origin"
    block_host = "block_host"
    block_origin = "block_origin"
    block_forwarded_request = "block_forwarded_request"
    block_cross_site = "block_cross_site"
    block_invalid_target = "block_invalid_target"


class OperatorConsoleActionKind(StrEnum):
    model_text_simulation = "model_text_simulation"
    model_structured_simulation = "model_structured_simulation"
    reference_capability_execution = "reference_capability_execution"
    synthetic_connector_read = "synthetic_connector_read"
    synthetic_connector_write_preview = "synthetic_connector_write_preview"
    kill_switch_activation = "kill_switch_activation"
    session_close = "session_close"


class OperatorConsoleProjectionKind(StrEnum):
    bootstrap = "bootstrap"
    status = "status"
    health = "health"
    observability = "observability"
    audit = "audit"
    receipt = "receipt"
    action_result = "action_result"


class OperatorConsoleIntegrityStatus(StrEnum):
    passed = "passed"
    failed = "failed"


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")
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


def operator_console_fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def fingerprint_text(kind: str, value: str | None) -> str:
    return operator_console_fingerprint({"kind": kind, "value": value or ""})


def fingerprint_bytes(kind: str, value: bytes) -> str:
    return hashlib.sha256(kind.encode("utf-8") + b"\0" + value).hexdigest()


def fingerprint_mapping(kind: str, value: Mapping[str, Any]) -> str:
    return operator_console_fingerprint({"kind": kind, "value": value})


def resource_limits_fingerprint() -> str:
    return operator_console_fingerprint(ALL_RESOURCE_LIMITS)


def security_headers_fingerprint() -> str:
    return operator_console_fingerprint(SECURITY_HEADERS)


def route_manifest_fingerprint() -> str:
    return default_route_manifest().manifest_fingerprint or ZERO_FINGERPRINT


def protected_material_present(value: object) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in PROTECTED_MATERIAL_MARKERS)
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if protected_material_present(str(key)) or protected_material_present(nested):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return any(protected_material_present(item) for item in value)
    return False


def reject_protected_material(value: object) -> None:
    if protected_material_present(value):
        raise ValueError("protected material is not accepted by this local console route")


def json_depth(value: object) -> int:
    if isinstance(value, Mapping):
        if not value:
            return 1
        return 1 + max(json_depth(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if not value:
            return 1
        return 1 + max(json_depth(item) for item in value)
    return 1


def json_item_count(value: object) -> int:
    if isinstance(value, Mapping):
        return len(value) + sum(json_item_count(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) + sum(json_item_count(item) for item in value)
    return 1


def _json_safe(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return ensure_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _json_safe(nested) for key, nested in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_json_safe(nested) for nested in value]
    if isinstance(value, set):
        return sorted(_json_safe(nested) for nested in value)
    if isinstance(value, float):
        if not isfinite(value):
            raise TypeError("non-finite numeric values are not supported")
        return value
    return value


def _reject_non_finite_numbers(value: object) -> None:
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("finite numeric values are required")
    if isinstance(value, Mapping):
        for nested in value.values():
            _reject_non_finite_numbers(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _reject_non_finite_numbers(nested)


def _sorted_unique(values: Iterable[str], *, allow_empty: bool = False) -> tuple[str, ...]:
    result = tuple(sorted({ensure_safe_identifier(item) for item in values}))
    if not allow_empty and not result:
        raise ValueError("at least one safe identifier is required")
    return result


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Iterable):
        raise ValueError("bounded string tuple is required")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("bounded string tuple is required")
        result.append(item)
    return tuple(result)


class OperatorConsoleBaseModel(BaseModel):
    """Base strict Pydantic v2 model for AION-237 contracts."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def console_common_values_must_be_safe(self) -> Self:
        _reject_non_finite_numbers(self.model_dump(mode="python"))
        return self


class OperatorConsoleFingerprintedModel(OperatorConsoleBaseModel):
    """Model that self-populates and verifies one canonical fingerprint field."""

    _fingerprint_field: ClassVar[str | None] = None

    @model_validator(mode="after")
    def console_fingerprint_must_match(self) -> Self:
        field_name = self._fingerprint_field
        if field_name is None:
            return self
        expected = operator_console_fingerprint(
            self.model_dump(mode="json", exclude={field_name})
        )
        current = getattr(self, field_name)
        if current is None:
            object.__setattr__(self, field_name, expected)
        elif current != expected:
            raise ValueError("fingerprint must match canonical operator console payload")
        return self


class OperatorConsoleRouteDefinition(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "route_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_ROUTE_MANIFEST_SCHEMA_VERSION
    method: Literal["GET", "POST"]
    path: str
    kind: OperatorConsoleRouteKind
    read_only: bool
    requires_json_content_type: bool
    requires_same_origin_mutation_nonce: bool
    requires_origin: bool
    requires_operator_confirmation: bool
    maximum_per_session: int = Field(ge=1)
    route_fingerprint: str | None = None

    @field_validator("path")
    @classmethod
    def route_path_must_be_exact(cls, value: str) -> str:
        if value not in AUTHORIZED_ROUTE_PAIRS:
            raise ValueError("route path is not authorized")
        return value


AUTHORIZED_ROUTE_PAIRS: dict[str, str] = {
    "/aion/local/v1/bootstrap": "GET",
    "/aion/local/v1/status": "GET",
    "/aion/local/v1/health": "GET",
    "/aion/local/v1/observability": "GET",
    "/aion/local/v1/audit": "GET",
    "/aion/local/v1/model/simulate": "POST",
    "/aion/local/v1/capability/execute": "POST",
    "/aion/local/v1/connector/simulate": "POST",
    "/aion/local/v1/kill": "POST",
    "/aion/local/v1/session/close": "POST",
}


class OperatorConsoleRouteManifest(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "manifest_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_ROUTE_MANIFEST_SCHEMA_VERSION
    routes: tuple[OperatorConsoleRouteDefinition, ...]
    exact_routes_only: bool = True
    dynamic_path_registration_enabled: bool = False
    wildcard_routes_enabled: bool = False
    path_parameters_enabled: bool = False
    post_requires_json_content_type: bool = True
    post_requires_same_origin_mutation_nonce: bool = True
    state_changing_post_requires_operator_confirmation: bool = True
    cors_wildcard_enabled: bool = False
    cookies_enabled: bool = False
    bearer_token_enabled: bool = False
    file_upload_enabled: bool = False
    multipart_enabled: bool = False
    form_urlencoded_enabled: bool = False
    manifest_fingerprint: str | None = None

    @model_validator(mode="after")
    def route_manifest_must_be_exact(self) -> Self:
        observed = {item.path: item.method for item in self.routes}
        if observed != AUTHORIZED_ROUTE_PAIRS or len(self.routes) != 10:
            raise ValueError("route manifest must contain exactly ten authorized routes")
        if not self.exact_routes_only or self.dynamic_path_registration_enabled:
            raise ValueError("route manifest cannot register dynamic routes")
        if self.wildcard_routes_enabled or self.path_parameters_enabled:
            raise ValueError("route manifest cannot contain wildcard or parameterized routes")
        if (
            self.cors_wildcard_enabled
            or self.cookies_enabled
            or self.bearer_token_enabled
            or self.file_upload_enabled
            or self.multipart_enabled
            or self.form_urlencoded_enabled
        ):
            raise ValueError("route manifest cannot authorize browser persistence or uploads")
        return self


def default_route_manifest() -> OperatorConsoleRouteManifest:
    get_limit = {
        "/aion/local/v1/bootstrap": "maximum_bootstrap_reads_per_session",
        "/aion/local/v1/status": "maximum_status_reads_per_session",
        "/aion/local/v1/health": "maximum_health_reads_per_session",
        "/aion/local/v1/observability": "maximum_observability_reads_per_session",
        "/aion/local/v1/audit": "maximum_audit_reads_per_session",
    }
    routes: list[OperatorConsoleRouteDefinition] = []
    for path, method in AUTHORIZED_ROUTE_PAIRS.items():
        kind = OperatorConsoleRouteKind.read_projection
        if path.endswith("/model/simulate"):
            kind = OperatorConsoleRouteKind.model_simulation
        elif path.endswith("/capability/execute"):
            kind = OperatorConsoleRouteKind.capability_execution
        elif path.endswith("/connector/simulate"):
            kind = OperatorConsoleRouteKind.connector_simulation
        elif path.endswith("/kill"):
            kind = OperatorConsoleRouteKind.kill
        elif path.endswith("/session/close"):
            kind = OperatorConsoleRouteKind.session_close
        if method == "GET":
            maximum = POSITIVE_RESOURCE_LIMITS[get_limit[path]]
        elif kind == OperatorConsoleRouteKind.model_simulation:
            maximum = POSITIVE_RESOURCE_LIMITS["maximum_model_simulations_per_session"]
        elif kind == OperatorConsoleRouteKind.capability_execution:
            maximum = POSITIVE_RESOURCE_LIMITS["maximum_capability_executions_per_session"]
        elif kind == OperatorConsoleRouteKind.connector_simulation:
            maximum = POSITIVE_RESOURCE_LIMITS[
                "maximum_synthetic_connector_simulations_per_session"
            ]
        elif kind == OperatorConsoleRouteKind.kill:
            maximum = POSITIVE_RESOURCE_LIMITS["maximum_kill_switch_activations_per_session"]
        else:
            maximum = POSITIVE_RESOURCE_LIMITS["maximum_session_close_requests_per_session"]
        routes.append(
            OperatorConsoleRouteDefinition(
                method=method,  # type: ignore[arg-type]
                path=path,
                kind=kind,
                read_only=method == "GET",
                requires_json_content_type=method == "POST",
                requires_same_origin_mutation_nonce=method == "POST",
                requires_origin=method == "POST",
                requires_operator_confirmation=method == "POST",
                maximum_per_session=maximum,
            )
        )
    return OperatorConsoleRouteManifest(routes=tuple(routes))


class OperatorConsoleStaticAsset(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "asset_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_CONTRACT_SCHEMA_VERSION
    route_path: str
    asset_name: str
    mime_type: str
    byte_count: int = Field(ge=0)
    sha256: str
    content: bytes = Field(default=b"", exclude=True, repr=False)
    cache_control: Literal["no-store"] = "no-store"
    symlink: bool = False
    arbitrary_file_read: bool = False
    asset_fingerprint: str | None = None

    @model_validator(mode="after")
    def static_asset_must_be_exact(self) -> Self:
        if STATIC_ASSET_ROUTES.get(self.route_path) != self.asset_name:
            raise ValueError("static asset route mismatch")
        if STATIC_ASSET_MIME_TYPES.get(self.asset_name) != self.mime_type:
            raise ValueError("static asset MIME mismatch")
        if self.symlink or self.arbitrary_file_read:
            raise ValueError("static asset must be injected exact bytes only")
        if self.sha256 != hashlib.sha256(self.content).hexdigest():
            raise ValueError("static asset byte fingerprint mismatch")
        if self.byte_count != len(self.content):
            raise ValueError("static asset byte count mismatch")
        return self


class OperatorConsoleStaticAssetManifest(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "manifest_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_CONTRACT_SCHEMA_VERSION
    assets: tuple[OperatorConsoleStaticAsset, ...]
    exact_asset_allowlist: bool = True
    arbitrary_file_reads_enabled: bool = False
    directory_listing_enabled: bool = False
    range_requests_enabled: bool = False
    remote_asset_fallback_enabled: bool = False
    manifest_fingerprint: str | None = None

    @model_validator(mode="after")
    def static_manifest_must_be_exact(self) -> Self:
        observed = {item.route_path: item.asset_name for item in self.assets}
        if observed != STATIC_ASSET_ROUTES or len(self.assets) != 5:
            raise ValueError("static asset manifest must contain exactly five route entries")
        if (
            not self.exact_asset_allowlist
            or self.arbitrary_file_reads_enabled
            or self.directory_listing_enabled
            or self.range_requests_enabled
            or self.remote_asset_fallback_enabled
        ):
            raise ValueError("static asset manifest cannot widen file serving")
        return self


def static_asset_manifest_from_bytes(
    assets: Mapping[str, bytes],
) -> OperatorConsoleStaticAssetManifest:
    entries: list[OperatorConsoleStaticAsset] = []
    for route_path, asset_name in STATIC_ASSET_ROUTES.items():
        try:
            content = assets[asset_name]
        except KeyError as exc:
            raise ValueError("missing injected static asset") from exc
        entries.append(
            OperatorConsoleStaticAsset(
                route_path=route_path,
                asset_name=asset_name,
                mime_type=STATIC_ASSET_MIME_TYPES[asset_name],
                byte_count=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                content=content,
            )
        )
    return OperatorConsoleStaticAssetManifest(assets=tuple(entries))


class OperatorConsoleContentSecurityPolicy(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "policy_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_CONTRACT_SCHEMA_VERSION
    header_value: str = CONTENT_SECURITY_POLICY
    unsafe_inline_enabled: bool = False
    unsafe_eval_enabled: bool = False
    remote_asset_loading_enabled: bool = False
    policy_fingerprint: str | None = None

    @model_validator(mode="after")
    def csp_must_be_exact(self) -> Self:
        if self.header_value != CONTENT_SECURITY_POLICY:
            raise ValueError("Content Security Policy mismatch")
        if self.unsafe_inline_enabled or self.unsafe_eval_enabled:
            raise ValueError("CSP cannot enable unsafe script execution")
        if self.remote_asset_loading_enabled:
            raise ValueError("CSP cannot enable remote assets")
        return self


class OperatorConsoleSecurityHeaders(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "headers_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_CONTRACT_SCHEMA_VERSION
    headers: Mapping[str, str] = Field(default_factory=lambda: dict(SECURITY_HEADERS))
    csp: OperatorConsoleContentSecurityPolicy = Field(
        default_factory=OperatorConsoleContentSecurityPolicy
    )
    cors_headers_emitted: bool = False
    cookies_emitted: bool = False
    headers_fingerprint: str | None = None

    @model_validator(mode="after")
    def security_headers_must_be_exact(self) -> Self:
        if (
            dict(self.headers) != SECURITY_HEADERS
            or self.csp.header_value != CONTENT_SECURITY_POLICY
        ):
            raise ValueError("security headers mismatch")
        if self.cors_headers_emitted or self.cookies_emitted:
            raise ValueError("security headers cannot emit CORS or cookies")
        return self


class OperatorConsoleOriginPolicy(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "policy_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_ORIGIN_POLICY_SCHEMA_VERSION
    bind_host: str = LOOPBACK_BIND_HOST
    bound_port: int = Field(ge=1, le=65535)
    bound_origin: str
    forwarded_headers_rejected: bool = True
    cors_enabled: bool = False
    hostname_binding_enabled: bool = False
    policy_fingerprint: str | None = None

    @model_validator(mode="after")
    def origin_policy_must_be_loopback_only(self) -> Self:
        if self.bind_host != LOOPBACK_BIND_HOST:
            raise ValueError("Operator Console binds only to numeric IPv4 loopback")
        if self.bound_origin != f"http://{LOOPBACK_BIND_HOST}:{self.bound_port}":
            raise ValueError("bound origin must match loopback host and port")
        if not self.forwarded_headers_rejected or self.cors_enabled:
            raise ValueError("forwarded headers and CORS cannot be enabled")
        if self.hostname_binding_enabled:
            raise ValueError("hostname binding is not authorized")
        return self


class OperatorConsoleOriginDecisionRecord(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "decision_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_ORIGIN_POLICY_SCHEMA_VERSION
    request_id: str
    method: str
    route_path: str
    decision: OperatorConsoleOriginDecision
    host_fingerprint: str
    origin_fingerprint: str
    reason_codes: tuple[str, ...]
    created_at: datetime
    decision_fingerprint: str | None = None

    @field_validator("request_id", "method")
    @classmethod
    def origin_decision_ids_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("host_fingerprint", "origin_fingerprint")
    @classmethod
    def origin_decision_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def origin_decision_reasons_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return _sorted_unique(_string_tuple(value), allow_empty=False)

    @field_validator("created_at")
    @classmethod
    def origin_decision_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class OperatorConsoleMutationNonceRecord(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "record_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_NONCE_SCHEMA_VERSION
    console_session_id: str
    nonce_fingerprint: str
    generation: int = Field(ge=1)
    status: OperatorConsoleNonceStatus
    host_fingerprint: str
    origin_fingerprint: str
    issued_at: datetime
    expires_at: datetime
    raw_nonce_retained: bool = False
    record_fingerprint: str | None = None

    @field_validator("console_session_id")
    @classmethod
    def nonce_session_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("nonce_fingerprint", "host_fingerprint", "origin_fingerprint")
    @classmethod
    def nonce_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("issued_at", "expires_at")
    @classmethod
    def nonce_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def nonce_record_must_be_ephemeral(self) -> Self:
        if self.raw_nonce_retained:
            raise ValueError("raw mutation nonce cannot be retained")
        if self.expires_at <= self.issued_at:
            raise ValueError("nonce expiry must follow issuance")
        return self


class OperatorConsoleComponentBinding(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_COMPONENT_BINDING_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    secure_runtime_implementation_task: str = SECURE_RUNTIME_IMPLEMENTATION_TASK
    secure_runtime_authorization_id: str = SECURE_RUNTIME_AUTHORIZATION_ID
    secure_runtime_authorization_closed: bool = True
    model_gateway_implementation_task: str = MODEL_GATEWAY_IMPLEMENTATION_TASK
    model_gateway_authorization_id: str = MODEL_GATEWAY_AUTHORIZATION_ID
    model_gateway_authorization_closed: bool = True
    capability_runtime_implementation_task: str = CAPABILITY_RUNTIME_IMPLEMENTATION_TASK
    capability_runtime_authorization_id: str = CAPABILITY_RUNTIME_AUTHORIZATION_ID
    capability_runtime_authorization_closed: bool = True
    secure_runtime_session_id: str
    secure_runtime_request_identity_fingerprint: str
    actor_context_fingerprint: str
    secure_runtime_kill_switch_fingerprint: str
    model_gateway_session_fingerprint: str
    model_gateway_provider_manifest_fingerprint: str
    model_gateway_model_manifest_fingerprint: str
    capability_runtime_session_fingerprint: str
    capability_manifest_fingerprint: str
    connector_manifest_fingerprint: str
    receipt_chain_heads: Mapping[str, str]
    audit_chain_heads: Mapping[str, str]
    bound_at: datetime
    read_only: bool = True
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False
    binding_fingerprint: str | None = None

    @field_validator(
        "secure_runtime_session_id",
        "secure_runtime_implementation_task",
        "secure_runtime_authorization_id",
        "model_gateway_implementation_task",
        "model_gateway_authorization_id",
        "capability_runtime_implementation_task",
        "capability_runtime_authorization_id",
    )
    @classmethod
    def binding_ids_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "secure_runtime_request_identity_fingerprint",
        "actor_context_fingerprint",
        "secure_runtime_kill_switch_fingerprint",
        "model_gateway_session_fingerprint",
        "model_gateway_provider_manifest_fingerprint",
        "model_gateway_model_manifest_fingerprint",
        "capability_runtime_session_fingerprint",
        "capability_manifest_fingerprint",
        "connector_manifest_fingerprint",
    )
    @classmethod
    def binding_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("bound_at")
    @classmethod
    def binding_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def binding_must_preserve_authority(self) -> Self:
        if (
            self.program_id != PROGRAM_ID
            or self.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or not self.secure_runtime_authorization_closed
            or not self.model_gateway_authorization_closed
            or not self.capability_runtime_authorization_closed
            or not self.read_only
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("component binding violates AION-237 authority")
        return self


class OperatorConsoleIntegrationAuthorizationEnvelope(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "envelope_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_AUTHORIZATION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    console_session_id: str
    component_binding: OperatorConsoleComponentBinding
    operator_identity_fingerprint: str
    actor_context_fingerprint: str
    bound_host: str = LOOPBACK_BIND_HOST
    bound_port: int = Field(ge=1, le=65535)
    bound_origin: str
    route_manifest_fingerprint: str
    static_asset_manifest_fingerprint: str
    security_headers_fingerprint: str
    resource_limits_fingerprint: str
    created_at: datetime
    expires_at: datetime
    idle_expires_at: datetime
    confirmation_fingerprint: str
    operator_invoked: bool = True
    local_loopback: bool = True
    same_origin: bool = True
    public_listener: bool = False
    external_network_effect: bool = False
    browser_persistence: bool = False
    production_runtime: bool = False
    production_effect: bool = False
    envelope_fingerprint: str | None = None

    @field_validator("console_session_id")
    @classmethod
    def auth_session_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "operator_identity_fingerprint",
        "actor_context_fingerprint",
        "route_manifest_fingerprint",
        "static_asset_manifest_fingerprint",
        "security_headers_fingerprint",
        "resource_limits_fingerprint",
        "confirmation_fingerprint",
    )
    @classmethod
    def auth_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at", "expires_at", "idle_expires_at")
    @classmethod
    def auth_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def auth_envelope_must_be_local_only(self) -> Self:
        if self.bound_host != LOOPBACK_BIND_HOST:
            raise ValueError("authorization envelope must bind loopback host")
        if self.bound_origin != f"http://{LOOPBACK_BIND_HOST}:{self.bound_port}":
            raise ValueError("authorization envelope origin mismatch")
        if self.expires_at <= self.created_at or self.idle_expires_at <= self.created_at:
            raise ValueError("authorization envelope expiry mismatch")
        if self.idle_expires_at > self.created_at + timedelta(
            seconds=POSITIVE_RESOURCE_LIMITS["maximum_idle_seconds"]
        ):
            raise ValueError("idle expiry exceeds AION-237 limit")
        if (
            not self.operator_invoked
            or not self.local_loopback
            or not self.same_origin
            or self.public_listener
            or self.external_network_effect
            or self.browser_persistence
            or self.production_runtime
            or self.production_effect
        ):
            raise ValueError("authorization envelope cannot widen runtime authority")
        return self


class OperatorConsoleSessionBootstrap(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "bootstrap_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_SESSION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    console_session_id: str
    secure_runtime_session_fingerprint: str
    operator_identity_fingerprint: str
    actor_context_fingerprint: str
    bound_origin: str
    route_manifest: OperatorConsoleRouteManifest
    static_asset_manifest: OperatorConsoleStaticAssetManifest | None
    security_headers: OperatorConsoleSecurityHeaders
    current_nonce_fingerprint: str
    expires_at: datetime
    idle_expires_at: datetime
    live_mode: OperatorConsoleMode = OperatorConsoleMode.live_local_loopback
    browser_persistence_flags: Mapping[str, bool]
    production_flags: Mapping[str, bool]
    bootstrap_fingerprint: str | None = None

    @field_validator(
        "secure_runtime_session_fingerprint",
        "operator_identity_fingerprint",
        "actor_context_fingerprint",
        "current_nonce_fingerprint",
    )
    @classmethod
    def bootstrap_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("expires_at", "idle_expires_at")
    @classmethod
    def bootstrap_timestamps_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def bootstrap_must_not_authenticate_browser(self) -> Self:
        if any(self.browser_persistence_flags.values()) or any(self.production_flags.values()):
            raise ValueError("bootstrap cannot create browser or production authority")
        return self


class OperatorConsoleSession(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "session_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_SESSION_SCHEMA_VERSION
    console_session_id: str
    status: OperatorConsoleSessionStatus
    mode: OperatorConsoleMode
    authorization: OperatorConsoleIntegrationAuthorizationEnvelope
    bootstrap_count: int = Field(ge=0)
    request_count: int = Field(ge=0)
    active_request_ids: tuple[str, ...] = Field(default_factory=tuple)
    receipt_count: int = Field(ge=0)
    audit_count: int = Field(ge=0)
    created_at: datetime
    expires_at: datetime
    idle_expires_at: datetime
    closed_at: datetime | None = None
    killed_at: datetime | None = None
    session_fingerprint: str | None = None

    @field_validator("console_session_id")
    @classmethod
    def session_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("active_request_ids", mode="before")
    @classmethod
    def active_requests_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return _sorted_unique(_string_tuple(value), allow_empty=True)

    @field_validator("created_at", "expires_at", "idle_expires_at", "closed_at", "killed_at")
    @classmethod
    def session_timestamps_must_be_utc(cls, value: datetime | None) -> datetime | None:
        return ensure_utc(value) if value is not None else None

    @model_validator(mode="after")
    def session_must_be_bounded(self) -> Self:
        if len(self.active_request_ids) > POSITIVE_RESOURCE_LIMITS["maximum_concurrent_requests"]:
            raise ValueError("active request limit exceeded")
        if self.expires_at <= self.created_at or self.idle_expires_at <= self.created_at:
            raise ValueError("session expiry mismatch")
        return self


class OperatorConsoleHttpRequestRecord(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "request_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_HTTP_REQUEST_SCHEMA_VERSION
    request_id: str
    method: str
    route_path: str
    body_byte_count: int = Field(ge=0)
    host_fingerprint: str
    origin_fingerprint: str
    nonce_fingerprint: str
    created_at: datetime
    raw_body_retained: bool = False
    request_fingerprint: str | None = None

    @field_validator("request_id", "method")
    @classmethod
    def request_record_ids_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("host_fingerprint", "origin_fingerprint", "nonce_fingerprint")
    @classmethod
    def request_record_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def request_record_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def request_record_must_be_redacted(self) -> Self:
        if self.raw_body_retained:
            raise ValueError("raw request bodies cannot be retained")
        return self


class OperatorConsoleHttpResponseRecord(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "response_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_HTTP_RESPONSE_SCHEMA_VERSION
    request_id: str
    status_code: int = Field(ge=100, le=599)
    disposition: OperatorConsoleHttpDisposition
    body_byte_count: int = Field(ge=0)
    response_body_fingerprint: str
    security_headers_fingerprint: str
    created_at: datetime
    raw_body_retained: bool = False
    response_fingerprint: str | None = None

    @field_validator("request_id")
    @classmethod
    def response_record_ids_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("response_body_fingerprint", "security_headers_fingerprint")
    @classmethod
    def response_record_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("created_at")
    @classmethod
    def response_record_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def response_record_must_be_redacted(self) -> Self:
        if self.raw_body_retained:
            raise ValueError("raw response bodies cannot be retained")
        return self


class OperatorConsoleModelSimulationRequest(OperatorConsoleBaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: str = OPERATOR_CONSOLE_ACTION_SCHEMA_VERSION
    request_id: str
    mode: Literal["text", "structured_json"]
    transient_prompt: str = Field(repr=False, exclude=True, max_length=8192)
    structured_output_schema: Mapping[str, Any] | None = None
    operator_confirmation: str
    safe_metadata: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("request_id")
    @classmethod
    def model_request_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @model_validator(mode="after")
    def model_request_must_be_explicit(self) -> Self:
        expected = (
            CONFIRM_MODEL_STRUCTURED
            if self.mode == "structured_json"
            else CONFIRM_MODEL_TEXT
        )
        if self.operator_confirmation != expected:
            raise ValueError("model simulation confirmation mismatch")
        reject_protected_material(self.transient_prompt)
        reject_protected_material(self.safe_metadata)
        if self.mode == "structured_json" and not self.structured_output_schema:
            raise ValueError("structured schema is required")
        return self


class OperatorConsoleCapabilityExecutionRequest(OperatorConsoleBaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: str = OPERATOR_CONSOLE_ACTION_SCHEMA_VERSION
    request_id: str
    capability_id: str
    transient_input: Mapping[str, Any] = Field(default_factory=dict, repr=False, exclude=True)
    input_schema_id: str
    output_schema_id: str
    existing_approval_id: str | None = None
    operator_confirmation: str
    safe_metadata: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("request_id", "capability_id", "input_schema_id", "output_schema_id")
    @classmethod
    def capability_request_ids_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @model_validator(mode="after")
    def capability_request_must_be_operator_selected(self) -> Self:
        if self.capability_id not in ACCEPTED_REFERENCE_CAPABILITY_IDS:
            raise ValueError("capability is not authorized for the local console")
        if self.operator_confirmation != CONFIRM_CAPABILITY:
            raise ValueError("capability confirmation mismatch")
        reject_protected_material(self.transient_input)
        reject_protected_material(self.safe_metadata)
        return self


class OperatorConsoleConnectorSimulationRequest(OperatorConsoleBaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: str = OPERATOR_CONSOLE_ACTION_SCHEMA_VERSION
    request_id: str
    operation: str
    fixture_id: str
    record_key: str
    transient_proposed_value: Mapping[str, Any] | None = Field(
        default=None, repr=False, exclude=True
    )
    existing_approval_id: str
    operator_confirmation: str

    @field_validator("request_id", "operation", "fixture_id", "record_key", "existing_approval_id")
    @classmethod
    def connector_request_ids_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @model_validator(mode="after")
    def connector_request_must_be_synthetic(self) -> Self:
        if self.operation not in ACCEPTED_CONNECTOR_OPERATIONS:
            raise ValueError("connector operation is not authorized")
        expected = (
            CONFIRM_CONNECTOR_PREVIEW
            if self.operation == "connector.reference.write.preview"
            else CONFIRM_CONNECTOR_READ
        )
        if self.operator_confirmation != expected:
            raise ValueError("connector confirmation mismatch")
        reject_protected_material(self.transient_proposed_value or {})
        return self


class OperatorConsoleKillSwitchRequest(OperatorConsoleBaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: str = OPERATOR_CONSOLE_ACTION_SCHEMA_VERSION
    request_id: str
    operator_confirmation: str

    @field_validator("request_id")
    @classmethod
    def kill_request_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @model_validator(mode="after")
    def kill_request_must_be_explicit(self) -> Self:
        if self.operator_confirmation != CONFIRM_KILL:
            raise ValueError("kill-switch confirmation mismatch")
        return self


class OperatorConsoleSessionCloseRequest(OperatorConsoleBaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: str = OPERATOR_CONSOLE_ACTION_SCHEMA_VERSION
    request_id: str
    operator_confirmation: str

    @field_validator("request_id")
    @classmethod
    def close_request_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @model_validator(mode="after")
    def close_request_must_be_explicit(self) -> Self:
        if self.operator_confirmation != CONFIRM_CLOSE:
            raise ValueError("session-close confirmation mismatch")
        return self


class OperatorConsoleActionProjection(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "projection_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_PROJECTION_SCHEMA_VERSION
    projection_kind: OperatorConsoleProjectionKind = OperatorConsoleProjectionKind.action_result
    action_kind: OperatorConsoleActionKind
    request_id: str
    status: Literal["accepted", "blocked", "rejected"]
    output_fingerprint: str
    output_byte_count: int = Field(ge=0)
    receipt_fingerprint: str
    provenance_fingerprint: str
    validation_fingerprint: str
    transient_output: Any | None = Field(default=None, exclude=True, repr=False)
    synthetic: bool = True
    simulation_only: bool = True
    trusted: bool = False
    factual_status: Literal["unverified"] = "unverified"
    approval_effect: bool = False
    execution_effect: bool = False
    memory_effect: bool = False
    belief_effect: bool = False
    policy_effect: bool = False
    production_effect: bool = False
    writes_applied: int = 0
    projection_fingerprint: str | None = None

    @field_validator("request_id")
    @classmethod
    def action_projection_request_id_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator(
        "output_fingerprint",
        "receipt_fingerprint",
        "provenance_fingerprint",
        "validation_fingerprint",
    )
    @classmethod
    def action_projection_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def action_projection_must_have_zero_effects(self) -> Self:
        if (
            not self.synthetic
            or not self.simulation_only
            or self.trusted
            or self.approval_effect
            or self.execution_effect
            or self.memory_effect
            or self.belief_effect
            or self.policy_effect
            or self.production_effect
            or self.writes_applied != 0
        ):
            raise ValueError("action projection cannot authorize external or production effects")
        return self


OperatorConsoleModelSimulationProjection = OperatorConsoleActionProjection
OperatorConsoleCapabilityExecutionProjection = OperatorConsoleActionProjection
OperatorConsoleConnectorSimulationProjection = OperatorConsoleActionProjection


class OperatorConsoleStatusProjection(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "projection_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_PROJECTION_SCHEMA_VERSION
    projection_kind: OperatorConsoleProjectionKind = OperatorConsoleProjectionKind.status
    program_id: str = PROGRAM_ID
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    task_id: str = IMPLEMENTATION_TASK
    console_session_state: OperatorConsoleSessionStatus
    secure_runtime_state: str
    model_gateway_state: str
    capability_runtime_state: str
    model_output_trust_state: Literal["untrusted"] = "untrusted"
    operator_selection_required: bool = True
    loopback_state: Literal["127.0.0.1-only"] = "127.0.0.1-only"
    same_origin_state: Literal["required"] = "required"
    kill_switch_state: str
    active_request_count: int = Field(ge=0)
    receipt_count: int = Field(ge=0)
    audit_count: int = Field(ge=0)
    production_flags: Mapping[str, bool]
    projection_fingerprint: str | None = None

    @model_validator(mode="after")
    def status_projection_must_be_redacted(self) -> Self:
        if self.operator_selection_required is not True or any(self.production_flags.values()):
            raise ValueError("status projection cannot imply production authority")
        return self


class OperatorConsoleHealthProjection(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "health_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_PROJECTION_SCHEMA_VERSION
    projection_kind: OperatorConsoleProjectionKind = OperatorConsoleProjectionKind.health
    ready: bool
    component_availability: Mapping[str, bool]
    authorization_exact: bool
    session_valid: bool
    nonce_valid: bool
    host_policy_valid: bool
    origin_policy_valid: bool
    resource_budget_valid: bool
    kill_switch_clear: bool
    listener_active: bool
    integrity_status: OperatorConsoleIntegrityStatus
    health_fingerprint: str | None = None


class OperatorConsoleObservabilitySnapshot(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "observability_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_OBSERVABILITY_SCHEMA_VERSION
    request_counts_by_route: Mapping[str, int]
    status_code_counts: Mapping[str, int]
    counters: Mapping[str, int]
    bounded_durations_ms: Mapping[str, int] = Field(default_factory=dict)
    observability_fingerprint: str | None = None


class OperatorConsoleAuditProjection(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "projection_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_PROJECTION_SCHEMA_VERSION
    projection_kind: OperatorConsoleProjectionKind = OperatorConsoleProjectionKind.audit
    event_type_counts: Mapping[str, int]
    audit_chain_head: str
    receipt_chain_heads: Mapping[str, str]
    latest_safe_timestamps: Mapping[str, datetime]
    integrity_status: OperatorConsoleIntegrityStatus
    payloads_retained: bool = False
    projection_fingerprint: str | None = None

    @field_validator("audit_chain_head")
    @classmethod
    def audit_projection_head_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def audit_projection_must_exclude_payloads(self) -> Self:
        if self.payloads_retained:
            raise ValueError("audit projection cannot retain event payloads")
        return self


class OperatorConsoleReceiptProjection(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "projection_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_PROJECTION_SCHEMA_VERSION
    projection_kind: OperatorConsoleProjectionKind = OperatorConsoleProjectionKind.receipt
    request_id: str
    receipt_fingerprint: str
    prior_receipt_fingerprint: str
    action_kind: OperatorConsoleActionKind
    disposition: OperatorConsoleHttpDisposition
    projection_fingerprint: str | None = None


class OperatorConsoleAuditRecord(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "record_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_AUDIT_SCHEMA_VERSION
    session_id: str
    request_id: str | None = None
    sequence_number: int = Field(ge=1)
    event_type: str
    prior_record_fingerprint: str
    subject_fingerprints: tuple[str, ...] = Field(default_factory=tuple)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime
    payload_retained: bool = False
    record_fingerprint: str | None = None

    @field_validator("session_id", "event_type")
    @classmethod
    def audit_record_ids_must_be_safe(cls, value: str) -> str:
        return ensure_safe_identifier(value)

    @field_validator("request_id")
    @classmethod
    def audit_record_request_id_must_be_safe(cls, value: str | None) -> str | None:
        return ensure_safe_identifier(value) if value is not None else None

    @field_validator("prior_record_fingerprint")
    @classmethod
    def audit_record_prior_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @field_validator("subject_fingerprints", mode="before")
    @classmethod
    def audit_record_fingerprints_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return tuple(ensure_sha256(item) for item in _string_tuple(value))

    @field_validator("reason_codes", mode="before")
    @classmethod
    def audit_record_reasons_must_be_safe(cls, value: object) -> tuple[str, ...]:
        return _sorted_unique(_string_tuple(value), allow_empty=True)

    @field_validator("created_at")
    @classmethod
    def audit_record_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def audit_record_must_be_redacted(self) -> Self:
        if self.payload_retained:
            raise ValueError("audit records cannot retain raw payloads")
        return self


class OperatorConsoleIntegrityFinding(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "finding_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_INTEGRITY_SCHEMA_VERSION
    finding_id: str
    category: str
    status: OperatorConsoleIntegrityStatus
    reason_codes: tuple[str, ...]
    finding_fingerprint: str | None = None


class OperatorConsoleIntegrityReport(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "report_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_INTEGRITY_SCHEMA_VERSION
    report_id: str
    status: OperatorConsoleIntegrityStatus
    checked_categories: tuple[str, ...]
    findings: tuple[OperatorConsoleIntegrityFinding, ...] = Field(default_factory=tuple)
    all_prohibited_counters_zero: bool
    active_requests_after_close: int = Field(ge=0)
    active_sessions_after_close: int = Field(ge=0)
    listener_closed: bool
    created_at: datetime
    report_fingerprint: str | None = None

    @model_validator(mode="after")
    def integrity_report_must_match_findings(self) -> Self:
        if self.status == OperatorConsoleIntegrityStatus.passed and self.findings:
            raise ValueError("passed integrity report cannot contain findings")
        if self.status == OperatorConsoleIntegrityStatus.passed and not (
            self.all_prohibited_counters_zero
            and self.active_requests_after_close == 0
            and self.active_sessions_after_close == 0
            and self.listener_closed
        ):
            raise ValueError("passed integrity report requires zero residual runtime state")
        return self


class OperatorConsoleOperatorReviewItem(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "review_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_EVIDENCE_SCHEMA_VERSION
    operator_review_required: bool = True
    local_bridge_is_not_production_runtime: bool = True
    browser_is_not_operator_identity: bool = True
    mutation_nonce_is_not_authentication: bool = True
    model_output_is_untrusted: bool = True
    model_output_is_not_execution_authority: bool = True
    operator_selection_is_required: bool = True
    reference_provider_is_not_live_provider: bool = True
    synthetic_connector_is_not_external_connector: bool = True
    write_preview_is_not_write: bool = True
    public_listener_authorized: bool = False
    external_egress_authorized: bool = False
    browser_persistence_authorized: bool = False
    provider_calls_authorized: bool = False
    external_connector_authorized: bool = False
    real_tool_authorized: bool = False
    production_write_authorized: bool = False
    deployment_authorized: bool = False
    model_training_authorized: bool = False
    review_fingerprint: str | None = None


class OperatorConsoleEvidenceBundle(OperatorConsoleFingerprintedModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
    _fingerprint_field: ClassVar[str | None] = "report_fingerprint"

    schema_version: str = OPERATOR_CONSOLE_EVIDENCE_SCHEMA_VERSION
    pilot_id: str
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    mode: Literal["live-local-loopback"] = "live-local-loopback"
    bind_host: str = LOOPBACK_BIND_HOST
    ephemeral_port_used: bool = True
    actual_port_retained: bool = False
    secure_runtime_component_binding_fingerprint: str
    model_gateway_component_binding_fingerprint: str
    capability_runtime_component_binding_fingerprint: str
    route_manifest_fingerprint: str
    static_asset_manifest_fingerprint: str
    security_headers_fingerprint: str
    counters: Mapping[str, int | bool]
    prohibited_effect_counters: Mapping[str, int]
    listener_audit_chain_head: str
    console_audit_chain_head: str
    secure_runtime_receipt_chain_head: str
    model_gateway_audit_chain_head: str
    capability_runtime_receipt_chain_head: str
    integrity_passed: bool = True
    temporary_files_retained: int = 0
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False
    report_fingerprint: str | None = None

    @field_validator(
        "secure_runtime_component_binding_fingerprint",
        "model_gateway_component_binding_fingerprint",
        "capability_runtime_component_binding_fingerprint",
        "route_manifest_fingerprint",
        "static_asset_manifest_fingerprint",
        "security_headers_fingerprint",
        "listener_audit_chain_head",
        "console_audit_chain_head",
        "secure_runtime_receipt_chain_head",
        "model_gateway_audit_chain_head",
        "capability_runtime_receipt_chain_head",
    )
    @classmethod
    def evidence_fingerprints_must_be_safe(cls, value: str) -> str:
        return ensure_sha256(value)

    @model_validator(mode="after")
    def evidence_bundle_must_be_redacted_and_zero_effect(self) -> Self:
        if (
            self.authorization_id != AUTHORIZATION_TRANSACTION_ID
            or self.bind_host != LOOPBACK_BIND_HOST
            or not self.ephemeral_port_used
            or self.actual_port_retained
            or not self.integrity_passed
            or self.temporary_files_retained != 0
            or not self.redacted
            or self.production_effect
            or self.runtime_effect
        ):
            raise ValueError("pilot evidence violates AION-237 boundary")
        if any(value != 0 for value in self.prohibited_effect_counters.values()):
            raise ValueError("pilot evidence contains prohibited effects")
        return self


__all__ = [
    "ACCEPTED_CONNECTOR_OPERATIONS",
    "ACCEPTED_REFERENCE_CAPABILITY_IDS",
    "ALL_RESOURCE_LIMITS",
    "APPROVAL_RECORD_ID",
    "AUTHORIZED_CAPABILITY_FLAGS",
    "AUTHORIZED_ROUTE_PAIRS",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CAPABILITY_RUNTIME_AUTHORIZATION_ID",
    "CAPABILITY_RUNTIME_IMPLEMENTATION_TASK",
    "CONFIRM_CAPABILITY",
    "CONFIRM_CLOSE",
    "CONFIRM_CONNECTOR_PREVIEW",
    "CONFIRM_CONNECTOR_READ",
    "CONFIRM_KILL",
    "CONFIRM_MODEL_STRUCTURED",
    "CONFIRM_MODEL_TEXT",
    "CONTENT_SECURITY_POLICY",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "LOCAL_CONFIRMATION_TEXT",
    "LOOPBACK_BIND_HOST",
    "MODEL_GATEWAY_AUTHORIZATION_ID",
    "MODEL_GATEWAY_IMPLEMENTATION_TASK",
    "MUTATION_NONCE_REQUEST_HEADER",
    "MUTATION_NONCE_RESPONSE_HEADER",
    "OPERATOR_CONFIRMATION_HEADER",
    "POSITIVE_RESOURCE_LIMITS",
    "PROGRAM_ID",
    "PROHIBITED_CAPABILITY_FLAGS",
    "PROHIBITED_COUNTER_NAMES",
    "SECURITY_HEADERS",
    "SECURE_RUNTIME_AUTHORIZATION_ID",
    "SECURE_RUNTIME_IMPLEMENTATION_TASK",
    "STATIC_ASSET_MIME_TYPES",
    "STATIC_ASSET_ROUTES",
    "ZERO_EFFECT_LIMITS",
    "ZERO_FINGERPRINT",
    "OperatorConsoleActionKind",
    "OperatorConsoleActionProjection",
    "OperatorConsoleAuditProjection",
    "OperatorConsoleAuditRecord",
    "OperatorConsoleBaseModel",
    "OperatorConsoleCapabilityExecutionProjection",
    "OperatorConsoleCapabilityExecutionRequest",
    "OperatorConsoleComponentBinding",
    "OperatorConsoleConnectorSimulationProjection",
    "OperatorConsoleConnectorSimulationRequest",
    "OperatorConsoleContentSecurityPolicy",
    "OperatorConsoleEvidenceBundle",
    "OperatorConsoleHealthProjection",
    "OperatorConsoleHttpDisposition",
    "OperatorConsoleHttpRequestRecord",
    "OperatorConsoleHttpResponseRecord",
    "OperatorConsoleIntegrityFinding",
    "OperatorConsoleIntegrityReport",
    "OperatorConsoleIntegrityStatus",
    "OperatorConsoleIntegrationAuthorizationEnvelope",
    "OperatorConsoleKillSwitchRequest",
    "OperatorConsoleMode",
    "OperatorConsoleModelSimulationProjection",
    "OperatorConsoleModelSimulationRequest",
    "OperatorConsoleMutationNonceRecord",
    "OperatorConsoleNonceStatus",
    "OperatorConsoleOperatorReviewItem",
    "OperatorConsoleOriginDecision",
    "OperatorConsoleOriginDecisionRecord",
    "OperatorConsoleOriginPolicy",
    "OperatorConsoleProjectionKind",
    "OperatorConsoleReceiptProjection",
    "OperatorConsoleRouteDefinition",
    "OperatorConsoleRouteKind",
    "OperatorConsoleRouteManifest",
    "OperatorConsoleSecurityHeaders",
    "OperatorConsoleSession",
    "OperatorConsoleSessionBootstrap",
    "OperatorConsoleSessionCloseRequest",
    "OperatorConsoleSessionStatus",
    "OperatorConsoleStaticAsset",
    "OperatorConsoleStaticAssetManifest",
    "OperatorConsoleStatusProjection",
    "canonical_json",
    "default_route_manifest",
    "fingerprint_bytes",
    "fingerprint_mapping",
    "fingerprint_text",
    "json_depth",
    "json_item_count",
    "operator_console_fingerprint",
    "reject_protected_material",
    "resource_limits_fingerprint",
    "route_manifest_fingerprint",
    "security_headers_fingerprint",
    "static_asset_manifest_from_bytes",
    "utc_now",
]
