"""Disabled v0.2 production-readiness qualification contracts."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

V02_QUALIFICATION_CONTRACT_SCHEMA_VERSION = "aion-v02-release-qualification/v1"
V02_QUALIFICATION_AUTHORIZATION_SCHEMA_VERSION = (
    "aion-v02-release-qualification-authorization/v1"
)
V02_QUALIFICATION_COMPONENT_BINDING_SCHEMA_VERSION = (
    "aion-v02-release-qualification-component-binding/v1"
)
V02_QUALIFICATION_SESSION_SCHEMA_VERSION = (
    "aion-v02-release-qualification-session/v1"
)
V02_READINESS_GAP_SCHEMA_VERSION = "aion-v02-readiness-gap/v1"
V02_GAP_MATRIX_SCHEMA_VERSION = "aion-v02-readiness-gap-matrix/v1"
V02_PRODUCTION_AUTH_COMPOSITION_SCHEMA_VERSION = (
    "aion-v02-production-auth-composition/v1"
)
V02_REQUEST_IDENTITY_INTEGRATION_SCHEMA_VERSION = (
    "aion-v02-request-identity-integration/v1"
)
V02_REPLAY_PROVISIONING_SCHEMA_VERSION = "aion-v02-replay-ledger-provisioning/v1"
V02_IDENTITY_PROVIDER_MANIFEST_SCHEMA_VERSION = (
    "aion-v02-identity-provider-manifest/v1"
)
V02_KEY_LIFECYCLE_SCHEMA_VERSION = "aion-v02-public-key-lifecycle/v1"
V02_PROTECTED_MATERIAL_SCHEMA_VERSION = "aion-v02-protected-material/v1"
V02_CREDENTIAL_LIFECYCLE_SCHEMA_VERSION = "aion-v02-credential-lifecycle/v1"
V02_TOKEN_LIFECYCLE_SCHEMA_VERSION = "aion-v02-token-lifecycle/v1"
V02_SESSION_LIFECYCLE_SCHEMA_VERSION = "aion-v02-session-lifecycle/v1"
V02_DEPLOYMENT_MANIFEST_SCHEMA_VERSION = (
    "aion-v02-deployment-artifact-manifest/v1"
)
V02_SBOM_SCHEMA_VERSION = "aion-v02-sbom-projection/v1"
V02_ARTIFACT_PROVENANCE_SCHEMA_VERSION = "aion-v02-artifact-provenance/v1"
V02_REPRODUCIBLE_BUILD_SCHEMA_VERSION = (
    "aion-v02-reproducible-build-evidence-projection/v1"
)
V02_ROLLBACK_SCHEMA_VERSION = "aion-v02-rollback-plan/v1"
V02_ROLLBACK_DRILL_SCHEMA_VERSION = "aion-v02-rollback-drill-plan/v1"
V02_OBSERVABILITY_SCHEMA_VERSION = "aion-v02-production-observability/v1"
V02_HEALTH_READINESS_SCHEMA_VERSION = "aion-v02-production-health-readiness/v1"
V02_THREAT_MODEL_SCHEMA_VERSION = "aion-v02-production-threat-model/v1"
V02_RUNTIME_GUARD_SCHEMA_VERSION = "aion-v02-runtime-release-guard/v1"
V02_RELEASE_GATE_SCHEMA_VERSION = "aion-v02-release-gate-matrix/v1"
V02_STAGING_PLAN_SCHEMA_VERSION = "aion-v02-staging-qualification-plan/v1"
V02_QUALIFICATION_RUN_SCHEMA_VERSION = "aion-v02-local-qualification-run/v1"
V02_QUALIFICATION_INTEGRITY_SCHEMA_VERSION = (
    "aion-v02-qualification-integrity/v1"
)
V02_QUALIFICATION_EVIDENCE_SCHEMA_VERSION = "aion-v02-qualification-evidence/v1"

PROGRAM_ID = "AION-V02-RELEASE-QUALIFICATION-001"
PROGRAM_NAME = "AION v0.2 Release Qualification Program"
AUTHORIZATION_TRANSACTION_ID = "AION-238-V02RQ-0001"
APPROVAL_RECORD_ID = "AION-238-V02RQ-0001"
IMPLEMENTATION_TASK = "AION-239"
FORMAL_CLOSEOUT_TASK = "AION-240"
FINAL_PLANNED_TASK = "AION-244"
CANDIDATE_ID = "disabled-v02-production-readiness-qualification-foundation-core"
WORKSTREAM = "v02-release-qualification-foundation"
AUTHORIZATION_SCOPE = (
    "disabled-production-readiness-qualification-production-auth-composition-request-"
    "identity-replay-ledger-provisioning-idp-adapter-key-rotation-protected-material-"
    "credential-token-session-lifecycle-deployment-artifact-sbom-provenance-rollback-"
    "observability-threat-model-runtime-guard-release-gate-staging-plan-no-production-"
    "activation-no-release-core"
)
LOCAL_QUALIFICATION_CONFIRMATION_TEXT = "RUN_DISABLED_V02_RELEASE_QUALIFICATION"
ZERO_FINGERPRINT = "0000000000000000000000000000000000000000000000000000000000000000"

PARENT_PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
PARENT_EVALUATION_ID = "AION-SRIPE-004"
PARENT_EVALUATION_BASE_COMMIT = "a0d262b245eb42d9f6e19709c0398e15af4832b8"
PARENT_EVALUATION_DECISION = (
    "CONTROLLED_OPERATOR_CONSOLE_INTEGRATED_LOCAL_RUNTIME_FINAL_EVALUATION_PASS_"
    "COMPLETE_SECURE_RUNTIME_INTEGRATION_PROGRAM_RECOMMEND_V02_RELEASE_"
    "QUALIFICATION_PROGRAM_AUTHORIZATION"
)
PARENT_EVALUATION_REPORT_FINGERPRINT = (
    "6e457d1a8bc226aa44697802d68b5d4cd5a272088a5ce6317048ab75503744ee"
)
PARENT_IMPLEMENTATION_TASK = "AION-237"
PARENT_IMPLEMENTATION_PR = 156
PARENT_IMPLEMENTATION_FEATURE_COMMIT = (
    "df1f89e1708638e32aef0532fb37ed150b85b600"
)
PARENT_IMPLEMENTATION_MERGE_COMMIT = "55f2721bb036886a693a36d870d49f49f7ecc6d1"
AION_238_HARNESS_COMMIT = "a0d262b245eb42d9f6e19709c0398e15af4832b8"
AION_238_CLOSEOUT_COMMIT = "1c83885ee801d7b46624e251c9f4699525f616d2"
AION_238_MERGE_COMMIT = "81076eab86a90e2f2097508b654e7869a5d144bf"
AION_238_MERGED_AT = "2026-08-01T14:48:17Z"
PILOT_ID = "AION-239-disabled-v02-production-readiness-qualification-pilot"
FOUNDATION_STATE = (
    "implemented_disabled_design_and_local_simulation_pending_AION-240_closeout"
)
FOUNDATION_PROGRAM_STATE = (
    "v02_release_qualification_foundation_implemented_disabled_pending_closeout"
)
FOUNDATION_DECISION = (
    "foundation_implemented_release_not_ready_staging_evidence_required"
)

SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
LOWER_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_NETWORK_OR_SECRET_MARKERS = (
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "mongodb://",
    "redis://",
    "amqp://",
    "jdbc:",
    "ldap://",
    "socket://",
    "-----begin",
    "bearer ",
    "authorization:",
    "authorization header",
    "client_secret",
    "client secret",
    "password=",
    "api_key=",
    "apikey=",
    "token=",
    "private_key",
    "private key",
    "connection string",
    "raw identity claim",
    "raw prompt",
    "raw model response",
    "hidden reasoning",
    "sk-",
    "ghp_",
    "xoxb-",
)
_PROHIBITED_VALUE_KEYS = {
    "api_key",
    "authorization_header",
    "client_secret",
    "connection_string",
    "credential_value",
    "database_password",
    "endpoint",
    "host",
    "hostname",
    "password",
    "private_key",
    "raw_claims",
    "raw_identity_assertion",
    "raw_model_response",
    "raw_prompt",
    "secret",
    "secret_value",
    "token",
    "token_value",
    "url",
    "username",
}
_SAFE_DESCRIPTOR_KEY_SUFFIXES = (
    "_code",
    "_codes",
    "_field",
    "_fields",
    "_id",
    "_ids",
    "_kind",
    "_name",
    "_role",
    "_roles",
    "_scope",
    "_scopes",
    "_status",
    "_type",
)


class V02QualificationMode(StrEnum):
    deterministic_local_simulation = "deterministic_local_simulation"
    operator_invoked_local = "operator_invoked_local"


class V02ReadinessDomain(StrEnum):
    production_auth_composition = "production_auth_composition"
    verified_request_identity = "verified_request_identity"
    replay_ledger_provisioning = "replay_ledger_provisioning"
    identity_provider_adapter = "identity_provider_adapter"
    public_key_lifecycle = "public_key_lifecycle"
    protected_material = "protected_material"
    credential_lifecycle = "credential_lifecycle"
    token_lifecycle = "token_lifecycle"
    session_lifecycle = "session_lifecycle"
    deployment_artifact = "deployment_artifact"
    software_bill_of_materials = "software_bill_of_materials"
    artifact_provenance = "artifact_provenance"
    reproducible_build = "reproducible_build"
    rollback = "rollback"
    observability = "observability"
    health_readiness = "health_readiness"
    threat_model = "threat_model"
    runtime_guard = "runtime_guard"
    release_gate_governance = "release_gate_governance"
    staging_qualification = "staging_qualification"


class V02GapSeverity(StrEnum):
    blocker = "blocker"
    critical = "critical"
    major = "major"
    minor = "minor"
    informational = "informational"


class V02GapStatus(StrEnum):
    open = "open"
    mitigation_designed_evidence_pending = "mitigation_designed_evidence_pending"
    staging_evidence_required = "staging_evidence_required"
    production_evidence_required = "production_evidence_required"
    resolved_by_verified_evidence = "resolved_by_verified_evidence"
    blocked = "blocked"


class V02EvidenceMaturity(StrEnum):
    absent = "absent"
    design_recorded = "design_recorded"
    deterministic_simulation = "deterministic_simulation"
    verified_local = "verified_local"
    staging_required = "staging_required"
    production_required = "production_required"


class V02LifecyclePolicyKind(StrEnum):
    public_key = "public_key"
    protected_material = "protected_material"
    credential = "credential"
    token = "token"
    session = "session"


class V02ReleaseGateOutcome(StrEnum):
    pass_design = "pass_design"
    pass_verified_local = "pass_verified_local"
    requires_staging_evidence = "requires_staging_evidence"
    requires_production_evidence = "requires_production_evidence"
    blocked = "blocked"
    failed = "failed"


class V02QualificationFoundationDecision(StrEnum):
    foundation_implemented_release_not_ready_staging_evidence_required = (
        FOUNDATION_DECISION
    )
    foundation_blocked_remediation_required = "foundation_blocked_remediation_required"


class V02ThreatCategory(StrEnum):
    spoofing = "spoofing"
    tampering = "tampering"
    repudiation = "repudiation"
    information_disclosure = "information_disclosure"
    denial_of_service = "denial_of_service"
    elevation_of_privilege = "elevation_of_privilege"
    supply_chain = "supply_chain"
    operational_failure = "operational_failure"
    governance_bypass = "governance_bypass"


class V02IntegrityStatus(StrEnum):
    passed = "passed"
    failed = "failed"


class V02RuntimeGuardOutcome(StrEnum):
    allow_disabled_qualification = "allow_disabled_qualification"
    require_operator_review = "require_operator_review"
    block = "block"


class V02IdentityProviderProtocolKind(StrEnum):
    generic_oidc_metadata = "generic_oidc_metadata"
    offline_signed_assertion_bridge = "offline_signed_assertion_bridge"


class V02ObservabilitySignalKind(StrEnum):
    log = "log"
    metric = "metric"
    trace = "trace"
    audit = "audit"
    security_event = "security_event"


READINESS_DOMAINS: tuple[V02ReadinessDomain, ...] = tuple(V02ReadinessDomain)
CANONICAL_GAP_IDS: dict[V02ReadinessDomain, str] = {
    domain: f"V02-GAP-{index:03d}"
    for index, domain in enumerate(READINESS_DOMAINS, start=1)
}
CANONICAL_RELEASE_GATE_IDS: tuple[str, ...] = tuple(
    f"V02-GATE-{number:03d}" for number in range(1, 25)
)
PROTECTED_MATERIAL_CLASS_CODES: tuple[str, ...] = (
    "private_key_material",
    "public_key_material",
    "identity_assertion",
    "credential",
    "client_secret",
    "access_token",
    "refresh_token",
    "session_token",
    "approval_evidence",
    "operator_identity",
    "personal_data",
    "model_prompt",
    "model_response",
    "connector_payload",
    "production_configuration",
    "audit_sensitive_metadata",
)
POSITIVE_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_readiness_gaps": 100,
    "maximum_identity_provider_manifests": 5,
    "maximum_public_key_lifecycle_policies": 20,
    "maximum_protected_material_classes": 50,
    "maximum_credential_lifecycle_policies": 20,
    "maximum_token_lifecycle_policies": 20,
    "maximum_session_lifecycle_policies": 20,
    "maximum_replay_ledger_provisioning_plans": 10,
    "maximum_deployment_artifact_manifests": 10,
    "maximum_rollback_plans": 20,
    "maximum_rollback_drill_plans": 10,
    "maximum_observability_signal_definitions": 500,
    "maximum_health_readiness_checks": 200,
    "maximum_threat_scenarios": 500,
    "maximum_release_gates": 200,
    "maximum_artifact_provenance_records": 1000,
    "maximum_sbom_components": 10000,
    "maximum_release_evidence_records": 10000,
    "maximum_staging_qualification_plans": 10,
    "maximum_local_qualification_runs": 20,
}
ZERO_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_public_network_calls": 0,
    "maximum_dns_resolutions": 0,
    "maximum_external_identity_provider_calls": 0,
    "maximum_credentials_generated": 0,
    "maximum_credentials_read": 0,
    "maximum_credentials_persisted": 0,
    "maximum_secrets_provisioned": 0,
    "maximum_tokens_generated": 0,
    "maximum_tokens_read": 0,
    "maximum_tokens_persisted": 0,
    "maximum_session_tokens_issued": 0,
    "maximum_access_tokens_issued": 0,
    "maximum_refresh_tokens_issued": 0,
    "maximum_authorization_headers_created": 0,
    "maximum_live_key_rotations": 0,
    "maximum_live_replay_ledger_writes": 0,
    "maximum_production_database_operations": 0,
    "maximum_staging_deployments": 0,
    "maximum_production_deployments": 0,
    "maximum_rollback_executions": 0,
    "maximum_external_log_exports": 0,
    "maximum_external_metric_exports": 0,
    "maximum_external_trace_exports": 0,
    "maximum_model_provider_calls": 0,
    "maximum_external_connector_calls": 0,
    "maximum_external_tool_executions": 0,
    "maximum_production_writes": 0,
    "maximum_production_memory_writes": 0,
    "maximum_production_policy_mutations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_automatic_merges": 0,
    "maximum_production_canary_executions": 0,
    "maximum_model_weight_changes": 0,
    "maximum_v02_release_candidates_created": 0,
    "maximum_v02_tags_created": 0,
    "maximum_v02_releases_created": 0,
}
PROHIBITED_EFFECT_COUNTERS: dict[str, int] = {
    "actual_builds_executed": 0,
    "artifact_bytes_created": 0,
    "vulnerability_scans_executed": 0,
    "external_identity_provider_calls": 0,
    "credentials_generated": 0,
    "credentials_read": 0,
    "credentials_persisted": 0,
    "tokens_generated": 0,
    "tokens_read": 0,
    "tokens_persisted": 0,
    "session_tokens_issued": 0,
    "access_tokens_issued": 0,
    "refresh_tokens_issued": 0,
    "authorization_headers_created": 0,
    "live_key_rotations": 0,
    "live_replay_ledger_writes": 0,
    "database_operations": 0,
    "staging_deployments": 0,
    "production_deployments": 0,
    "rollback_executions": 0,
    "external_log_exports": 0,
    "external_metric_exports": 0,
    "external_trace_exports": 0,
    "release_candidates_created": 0,
    "v02_tags_created": 0,
    "v02_releases_created": 0,
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def canonical_json(payload: Any) -> str:
    return json.dumps(_json_ready(payload), sort_keys=True, separators=(",", ":"))


def v02_qualification_fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_ready(value.model_dump(mode="json"))
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware UTC")
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(value[key]) for key in sorted(value)}
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("numeric values must be finite")
    return value


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    return value.astimezone(UTC)


def _reject_protected_material(value: Any, key: str | None = None) -> None:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            key_text = str(nested_key).lower()
            if key_text in _PROHIBITED_VALUE_KEYS and nested_value not in (None, False, ""):
                raise ValueError("protected or operational value is not allowed")
            _reject_protected_material(nested_value, key_text)
        return
    if isinstance(value, tuple | list | set):
        for item in value:
            _reject_protected_material(item, key)
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("numeric values must be finite")
    if isinstance(value, str):
        if (
            key is not None
            and key not in _PROHIBITED_VALUE_KEYS
            and key.endswith(_SAFE_DESCRIPTOR_KEY_SUFFIXES)
            and SAFE_IDENTIFIER_PATTERN.fullmatch(value)
        ):
            return
        lowered = value.lower()
        if any(marker in lowered for marker in _NETWORK_OR_SECRET_MARKERS):
            raise ValueError("protected or operational value is not allowed")
        if key in _PROHIBITED_VALUE_KEYS and value:
            raise ValueError("protected or operational value is not allowed")


def _validate_identifier(value: str) -> str:
    if not SAFE_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError("identifier must be bounded safe ASCII")
    return value


def _validate_fingerprint(value: str) -> str:
    if not LOWER_SHA256_PATTERN.fullmatch(value):
        raise ValueError("fingerprint must be 64 lowercase SHA-256 characters")
    return value


class V02StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="before")
    @classmethod
    def reject_protected_values(cls, data: Any) -> Any:
        _reject_protected_material(data)
        return data

    @field_validator("*", mode="before")
    @classmethod
    def normalize_timestamps(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return _ensure_utc(value)
        return value


class V02FingerprintedModel(V02StrictModel):
    fingerprint_field: ClassVar[str] = "fingerprint"

    @model_validator(mode="after")
    def fingerprint_must_match(self) -> Self:
        field = self.fingerprint_field
        expected = v02_qualification_fingerprint(
            self.model_dump(mode="json", exclude={field})
        )
        current = getattr(self, field)
        if current is None:
            object.__setattr__(self, field, expected)
        elif current != expected:
            raise ValueError(f"{field} must match canonical payload")
        return self


class V02QualificationResourceLimits(V02StrictModel):
    maximum_readiness_gaps: int = 100
    maximum_identity_provider_manifests: int = 5
    maximum_public_key_lifecycle_policies: int = 20
    maximum_protected_material_classes: int = 50
    maximum_credential_lifecycle_policies: int = 20
    maximum_token_lifecycle_policies: int = 20
    maximum_session_lifecycle_policies: int = 20
    maximum_replay_ledger_provisioning_plans: int = 10
    maximum_deployment_artifact_manifests: int = 10
    maximum_rollback_plans: int = 20
    maximum_rollback_drill_plans: int = 10
    maximum_observability_signal_definitions: int = 500
    maximum_health_readiness_checks: int = 200
    maximum_threat_scenarios: int = 500
    maximum_release_gates: int = 200
    maximum_artifact_provenance_records: int = 1000
    maximum_sbom_components: int = 10000
    maximum_release_evidence_records: int = 10000
    maximum_staging_qualification_plans: int = 10
    maximum_local_qualification_runs: int = 20
    maximum_public_network_calls: int = 0
    maximum_dns_resolutions: int = 0
    maximum_external_identity_provider_calls: int = 0
    maximum_credentials_generated: int = 0
    maximum_credentials_read: int = 0
    maximum_credentials_persisted: int = 0
    maximum_secrets_provisioned: int = 0
    maximum_tokens_generated: int = 0
    maximum_tokens_read: int = 0
    maximum_tokens_persisted: int = 0
    maximum_session_tokens_issued: int = 0
    maximum_access_tokens_issued: int = 0
    maximum_refresh_tokens_issued: int = 0
    maximum_authorization_headers_created: int = 0
    maximum_live_key_rotations: int = 0
    maximum_live_replay_ledger_writes: int = 0
    maximum_production_database_operations: int = 0
    maximum_staging_deployments: int = 0
    maximum_production_deployments: int = 0
    maximum_rollback_executions: int = 0
    maximum_external_log_exports: int = 0
    maximum_external_metric_exports: int = 0
    maximum_external_trace_exports: int = 0
    maximum_model_provider_calls: int = 0
    maximum_external_connector_calls: int = 0
    maximum_external_tool_executions: int = 0
    maximum_production_writes: int = 0
    maximum_production_memory_writes: int = 0
    maximum_production_policy_mutations: int = 0
    maximum_actual_belief_mutations: int = 0
    maximum_source_mutations: int = 0
    maximum_git_operations: int = 0
    maximum_runtime_created_pull_requests: int = 0
    maximum_automatic_merges: int = 0
    maximum_production_canary_executions: int = 0
    maximum_model_weight_changes: int = 0
    maximum_v02_release_candidates_created: int = 0
    maximum_v02_tags_created: int = 0
    maximum_v02_releases_created: int = 0

    @model_validator(mode="after")
    def limits_are_exact(self) -> Self:
        if self.model_dump() != {**POSITIVE_RESOURCE_LIMITS, **ZERO_RESOURCE_LIMITS}:
            raise ValueError("v0.2 qualification resource limits must be exact")
        return self


class V02ReleaseQualificationComponentBinding(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "binding_fingerprint"

    schema_version: str = V02_QUALIFICATION_COMPONENT_BINDING_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    parent_program_id: str = PARENT_PROGRAM_ID
    parent_evaluation_id: str = PARENT_EVALUATION_ID
    parent_evaluation_report_fingerprint: str = PARENT_EVALUATION_REPORT_FINGERPRINT
    aion_238_task: str = "AION-238"
    aion_237_implementation_commit: str = PARENT_IMPLEMENTATION_FEATURE_COMMIT
    aion_237_merge_commit: str = PARENT_IMPLEMENTATION_MERGE_COMMIT
    secure_runtime_implementation_status: str = "secure_runtime_integration_program_complete"
    model_gateway_implementation_status: str = "implemented_disabled_local"
    capability_runtime_implementation_status: str = "implemented_disabled_local"
    operator_console_implementation_status: str = "implemented_loopback_only_local"
    current_main_commit: str = AION_238_MERGE_COMMIT
    component_fingerprints: dict[str, str] = Field(default_factory=dict)
    binding_timestamp: datetime = Field(default_factory=utc_now)
    read_only: bool = True
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False
    binding_fingerprint: str | None = None


class V02ReleaseQualificationAuthorizationEnvelope(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "envelope_fingerprint"

    schema_version: str = V02_QUALIFICATION_AUTHORIZATION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    candidate_id: str = CANDIDATE_ID
    workstream: str = WORKSTREAM
    implementation_task: str = IMPLEMENTATION_TASK
    formal_closeout_task: str = FORMAL_CLOSEOUT_TASK
    final_planned_task: str = FINAL_PLANNED_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    component_binding_fingerprint: str
    qualification_session_id: str
    operator_identity_fingerprint: str
    allowed_readiness_domains: tuple[V02ReadinessDomain, ...] = READINESS_DOMAINS
    resource_limit_fingerprint: str
    required_release_gate_ids: tuple[str, ...] = CANONICAL_RELEASE_GATE_IDS
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    confirmation_fingerprint: str
    operator_invoked: bool = True
    deterministic_local: bool = True
    design_and_simulation_only: bool = True
    production_auth: bool = False
    external_idp: bool = False
    credential_effect: bool = False
    token_effect: bool = False
    database_effect: bool = False
    deployment_effect: bool = False
    release_effect: bool = False
    authorization_active: bool = True
    authorization_consumed: bool = False
    authorization_expired: bool = False
    authorization_reusable: bool = False
    envelope_fingerprint: str | None = None

    @model_validator(mode="after")
    def authorization_is_current_and_bounded(self) -> Self:
        if tuple(self.allowed_readiness_domains) != READINESS_DOMAINS:
            raise ValueError("authorization must include all 20 readiness domains")
        if tuple(self.required_release_gate_ids) != CANONICAL_RELEASE_GATE_IDS:
            raise ValueError("authorization must bind all 24 release gates")
        if self.expires_at <= self.created_at:
            raise ValueError("authorization envelope expiry must follow creation")
        if self.expires_at - self.created_at > timedelta(hours=1):
            raise ValueError("authorization envelope expiry exceeds one hour")
        for key in (
            "component_binding_fingerprint",
            "operator_identity_fingerprint",
            "resource_limit_fingerprint",
            "confirmation_fingerprint",
        ):
            _validate_fingerprint(getattr(self, key))
        return self


class V02QualificationSessionPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "session_plan_fingerprint"

    schema_version: str = V02_QUALIFICATION_SESSION_SCHEMA_VERSION
    session_id: str
    mode: V02QualificationMode = V02QualificationMode.operator_invoked_local
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    candidate_id: str = CANDIDATE_ID
    readiness_domains: tuple[V02ReadinessDomain, ...] = READINESS_DOMAINS
    maximum_local_runs: int = 20
    automatic_continuation_enabled: bool = False
    background_execution_enabled: bool = False
    persistent_state_enabled: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    session_plan_fingerprint: str | None = None

    @model_validator(mode="after")
    def session_plan_is_bounded(self) -> Self:
        if tuple(self.readiness_domains) != READINESS_DOMAINS:
            raise ValueError("session plan must cover all readiness domains")
        if self.expires_at - self.created_at > timedelta(hours=1):
            raise ValueError("qualification session expiry exceeds one hour")
        _validate_identifier(self.session_id)
        return self


class V02QualificationSession(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "session_fingerprint"

    schema_version: str = V02_QUALIFICATION_SESSION_SCHEMA_VERSION
    session_id: str
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    session_plan_fingerprint: str
    active: bool = True
    runs_completed: int = 0
    started_at: datetime = Field(default_factory=utc_now)
    closed_at: datetime | None = None
    candidate_references_loaded: bool = False
    evidence_references_loaded: bool = False
    session_fingerprint: str | None = None

    def close(self, closed_at: datetime | None = None) -> V02QualificationSession:
        return self.model_copy(
            update={
                "active": False,
                "closed_at": _ensure_utc(closed_at or utc_now()),
                "candidate_references_loaded": False,
                "evidence_references_loaded": False,
                "session_fingerprint": None,
            }
        )


class V02GapEvidenceRequirement(V02StrictModel):
    evidence_code: str
    maturity_required: V02EvidenceMaturity
    staging_evidence_required: bool
    production_evidence_required: bool


class V02ProductionReadinessGap(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "gap_fingerprint"

    schema_version: str = V02_READINESS_GAP_SCHEMA_VERSION
    gap_id: str
    readiness_domain: V02ReadinessDomain
    severity: V02GapSeverity
    minimum_severity: V02GapSeverity
    current_status: V02GapStatus
    evidence_maturity: V02EvidenceMaturity
    required_evidence_codes: tuple[str, ...]
    dependency_gap_ids: tuple[str, ...] = ()
    responsible_role_code: str
    target_task: str
    design_fingerprint: str
    current_evidence_fingerprints: tuple[str, ...] = ()
    operational_evidence_required: bool
    staging_evidence_required: bool
    production_evidence_required: bool
    gap_fingerprint: str | None = None

    @model_validator(mode="after")
    def gap_state_is_consistent(self) -> Self:
        if self.gap_id != CANONICAL_GAP_IDS.get(self.readiness_domain):
            raise ValueError("canonical gap ID does not match readiness domain")
        if self.current_status is V02GapStatus.resolved_by_verified_evidence:
            if not self.current_evidence_fingerprints:
                raise ValueError("resolved gaps require verified evidence")
            if self.evidence_maturity not in {
                V02EvidenceMaturity.verified_local,
                V02EvidenceMaturity.staging_required,
                V02EvidenceMaturity.production_required,
            }:
                raise ValueError("resolved gaps require verified evidence maturity")
        if self.evidence_maturity is V02EvidenceMaturity.design_recorded:
            allowed = {
                V02GapStatus.mitigation_designed_evidence_pending,
                V02GapStatus.staging_evidence_required,
                V02GapStatus.production_evidence_required,
            }
            if self.current_status not in allowed:
                raise ValueError("design evidence cannot resolve readiness gaps")
        if self.current_status is V02GapStatus.resolved_by_verified_evidence:
            if self.staging_evidence_required or self.production_evidence_required:
                raise ValueError("staging or production evidence gaps remain unresolved")
        severity_rank = {
            V02GapSeverity.blocker: 5,
            V02GapSeverity.critical: 4,
            V02GapSeverity.major: 3,
            V02GapSeverity.minor: 2,
            V02GapSeverity.informational: 1,
        }
        if severity_rank[self.severity] < severity_rank[self.minimum_severity]:
            raise ValueError("gap severity cannot be downgraded without evidence")
        _validate_identifier(self.gap_id)
        _validate_fingerprint(self.design_fingerprint)
        for item in self.current_evidence_fingerprints:
            _validate_fingerprint(item)
        return self


class V02ProductionReadinessGapMatrix(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "gap_matrix_fingerprint"

    schema_version: str = V02_GAP_MATRIX_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    gaps: tuple[V02ProductionReadinessGap, ...]
    evidence_requirements: tuple[V02GapEvidenceRequirement, ...]
    readiness_domains_represented: tuple[V02ReadinessDomain, ...]
    unresolved_operational_evidence: bool = True
    staging_evidence_required: bool = True
    production_evidence_required: bool = True
    gap_matrix_fingerprint: str | None = None

    @model_validator(mode="after")
    def matrix_is_complete_and_acyclic(self) -> Self:
        gap_ids = [gap.gap_id for gap in self.gaps]
        if len(gap_ids) != len(set(gap_ids)):
            raise ValueError("duplicate gap IDs are not allowed")
        domains = tuple(gap.readiness_domain for gap in self.gaps)
        if set(domains) != set(READINESS_DOMAINS):
            raise ValueError("gap matrix must cover all 20 readiness domains")
        if tuple(self.readiness_domains_represented) != READINESS_DOMAINS:
            raise ValueError("readiness domains must use deterministic ordering")
        graph = {gap.gap_id: set(gap.dependency_gap_ids) for gap in self.gaps}
        known = set(graph)
        for gap_id, dependencies in graph.items():
            if gap_id in dependencies:
                raise ValueError("gap cannot depend on itself")
            if dependencies - known:
                raise ValueError("gap dependency references unknown gap ID")
        _assert_acyclic(graph)
        return self


class V02ProductionAuthComponentBinding(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "component_fingerprint"

    component_code: str
    component_status: str
    source_contract_fingerprint: str
    component_fingerprint: str | None = None


class V02ProductionAuthCompositionPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "composition_fingerprint"

    schema_version: str = V02_PRODUCTION_AUTH_COMPOSITION_SCHEMA_VERSION
    component_order: tuple[str, ...]
    component_bindings: tuple[V02ProductionAuthComponentBinding, ...]
    fail_closed_behavior: str
    issuer_audience_validation: str
    trust_boundary_transitions: tuple[str, ...]
    replay_validation_order: tuple[str, ...]
    request_identity_construction_order: tuple[str, ...]
    actor_context_construction_order: tuple[str, ...]
    policy_and_approval_precedence: tuple[str, ...]
    session_creation_and_expiry: str
    error_redaction: str
    audit_requirements: tuple[str, ...]
    health_requirements: tuple[str, ...]
    rollback_boundary: str
    unresolved_production_evidence: bool = True
    production_auth_runtime_enabled: bool = False
    external_identity_provider_call_enabled: bool = False
    live_key_rotation_enabled: bool = False
    live_replay_ledger_enabled: bool = False
    composition_fingerprint: str | None = None


class V02ClaimMappingPolicy(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "mapping_fingerprint"

    claim_code: str
    target_field_code: str
    closed_allowlist: tuple[str, ...] = ()
    verified_claim_required: bool = True
    raw_claim_retained: bool = False
    mapping_fingerprint: str | None = None


class V02ActorContextProjectionPolicy(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "projection_fingerprint"

    projection_code: str
    source_fields: tuple[str, ...]
    target_actor_context_field: str
    privilege_expansion_allowed: bool = False
    workspace_substitution_allowed: bool = False
    anonymous_fallback_allowed: bool = False
    projection_fingerprint: str | None = None


class V02VerifiedRequestIdentityIntegrationPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "request_identity_plan_fingerprint"

    schema_version: str = V02_REQUEST_IDENTITY_INTEGRATION_SCHEMA_VERSION
    claim_mappings: tuple[V02ClaimMappingPolicy, ...]
    actor_context_projection_policies: tuple[V02ActorContextProjectionPolicy, ...]
    browser_headers_create_identity: bool = False
    cookies_create_identity: bool = False
    bearer_tokens_create_identity_without_future_verified_path: bool = False
    anonymous_fallback_for_production_auth_requests: bool = False
    privilege_expansion_rejected: bool = True
    workspace_substitution_rejected: bool = True
    raw_claims_retained: bool = False
    request_identity_plan_fingerprint: str | None = None

    @model_validator(mode="after")
    def required_mappings_exist(self) -> Self:
        required = {
            "issuer",
            "audience",
            "subject",
            "actor_id",
            "workspace_id",
            "roles",
            "permissions",
            "security_scopes",
            "trace_id",
            "correlation_id",
            "assertion_id",
            "assertion_fingerprint",
            "authentication_time",
            "expiry_time",
        }
        if {item.claim_code for item in self.claim_mappings} != required:
            raise ValueError("RequestIdentity plan must define exact verified mappings")
        return self


class V02ReplayLedgerCapacityPlan(V02StrictModel):
    estimated_daily_assertions: int
    retention_days: int
    cleanup_policy: str


class V02ReplayLedgerAvailabilityPlan(V02StrictModel):
    high_availability_design: str
    restore_objective: str
    recovery_point_objective: str
    recovery_time_objective: str


class V02ReplayLedgerBackupRestorePlan(V02StrictModel):
    backup_frequency: str
    restore_validation: str
    evidence_requirement: str


class V02ReplayLedgerMigrationPlan(V02StrictModel):
    migration_sequence: tuple[str, ...]
    rollback_boundary: str
    evidence_requirement: str


class V02ReplayLedgerProvisioningPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "replay_plan_fingerprint"

    schema_version: str = V02_REPLAY_PROVISIONING_SCHEMA_VERSION
    backend_class_code: str
    schema_fingerprint: str
    unique_key_design: str
    transaction_isolation_requirement: str
    encryption_at_rest_requirement: str
    encryption_in_transit_requirement: str
    retention_policy: str
    cleanup_policy: str
    capacity_plan: V02ReplayLedgerCapacityPlan
    availability_plan: V02ReplayLedgerAvailabilityPlan
    backup_restore_plan: V02ReplayLedgerBackupRestorePlan
    migration_plan: V02ReplayLedgerMigrationPlan
    monitoring_requirements: tuple[str, ...]
    fail_closed_behavior: str
    provisioning_evidence_requirements: tuple[str, ...]
    live_replay_ledger_enabled: bool = False
    maximum_live_replay_ledger_writes: int = 0
    production_database_provisioning_enabled: bool = False
    maximum_production_database_operations: int = 0
    replay_plan_fingerprint: str | None = None


class V02IdentityProviderClaimMapping(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "claim_mapping_fingerprint"

    provider_claim_code: str
    request_identity_field_code: str
    required: bool = True
    raw_value_retained: bool = False
    claim_mapping_fingerprint: str | None = None


class V02IdentityProviderTrustPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "trust_plan_fingerprint"

    issuer_fingerprint: str
    metadata_location_fingerprint: str
    audience_fingerprint: str
    public_key_source_policy_fingerprint: str
    authentication_flow_design_fingerprint: str
    logout_design_fingerprint: str
    failure_behavior: str
    trust_plan_fingerprint: str | None = None


class V02IdentityProviderAdapterManifest(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "identity_provider_manifest_fingerprint"

    schema_version: str = V02_IDENTITY_PROVIDER_MANIFEST_SCHEMA_VERSION
    provider_code: str
    protocol_kind: V02IdentityProviderProtocolKind
    claim_mappings: tuple[V02IdentityProviderClaimMapping, ...]
    trust_plan: V02IdentityProviderTrustPlan
    connect_available: bool = False
    authorize_available: bool = False
    exchange_code_available: bool = False
    refresh_available: bool = False
    fetch_metadata_available: bool = False
    fetch_keys_available: bool = False
    load_client_secret_available: bool = False
    create_authorization_header_available: bool = False
    external_identity_provider_call_enabled: bool = False
    maximum_external_identity_provider_calls: int = 0
    identity_provider_manifest_fingerprint: str | None = None

    def validate_manifest(self) -> bool:
        return True

    def validate_claim_mapping(self, mapping: V02IdentityProviderClaimMapping) -> bool:
        return mapping.raw_value_retained is False

    def project_disabled_request_plan(self) -> dict[str, Any]:
        return {
            "provider_code": self.provider_code,
            "external_identity_provider_call_enabled": False,
            "credential_effect": False,
            "token_effect": False,
        }

    def validate_disabled_response_fixture(self, fixture: dict[str, Any]) -> bool:
        _reject_protected_material(fixture)
        return fixture.get("external_identity_provider_call_enabled") is False


class V02PublicKeyRotationPlan(V02StrictModel):
    rotation_cadence: str
    overlap_window: str
    dual_control_required: bool = True
    emergency_rollover: str


class V02PublicKeyRevocationPlan(V02StrictModel):
    revocation_propagation: str
    stale_key_rejection: str
    audit_requirement: str


class V02PublicKeyCompromiseResponsePlan(V02StrictModel):
    compromise_detection: str
    response_sequence: tuple[str, ...]
    evidence_requirement: str


class V02PublicKeyLifecyclePolicy(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "policy_fingerprint"

    schema_version: str = V02_KEY_LIFECYCLE_SCHEMA_VERSION
    policy_id: str
    key_status_lifecycle: tuple[str, ...]
    activation_window: str
    rotation_plan: V02PublicKeyRotationPlan
    revocation_plan: V02PublicKeyRevocationPlan
    compromise_response_plan: V02PublicKeyCompromiseResponsePlan
    audit_requirements: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    rollback_boundary: str
    private_key_material_present: bool = False
    public_key_bytes_present: bool = False
    live_key_rotation_enabled: bool = False
    maximum_live_key_rotations: int = 0
    policy_fingerprint: str | None = None


class V02ProtectedMaterialClass(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "class_fingerprint"

    material_class_code: str
    classification_level: str
    allowed_handling_locations: tuple[str, ...]
    logging_policy: str
    evidence_policy: str
    retention_policy: str
    redaction_required: bool = True
    encryption_required: bool = True
    destruction_required: bool = True
    incident_response_required: bool = True
    protected_value_stored: bool = False
    class_fingerprint: str | None = None


class V02ProtectedMaterialLifecyclePolicy(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "policy_fingerprint"

    schema_version: str = V02_PROTECTED_MATERIAL_SCHEMA_VERSION
    policy_id: str
    lifecycle_kind: V02LifecyclePolicyKind = V02LifecyclePolicyKind.protected_material
    classes: tuple[V02ProtectedMaterialClass, ...]
    redaction_default: bool = True
    protected_value_stored: bool = False
    policy_fingerprint: str | None = None


class V02CredentialLifecyclePolicy(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "policy_fingerprint"

    schema_version: str = V02_CREDENTIAL_LIFECYCLE_SCHEMA_VERSION
    policy_id: str
    lifecycle_kind: V02LifecyclePolicyKind = V02LifecyclePolicyKind.credential
    credential_kind_code: str
    owner_role_code: str
    intended_storage_class_code: str
    generation_authority: str
    rotation_cadence: str
    expiry_policy: str
    revocation_policy: str
    compromise_response: str
    break_glass_policy: str
    dual_control_required: bool = True
    audit_required: bool = True
    credentials_generated: int = 0
    credentials_read: int = 0
    credentials_persisted: int = 0
    policy_fingerprint: str | None = None


class V02TokenLifecyclePolicy(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "policy_fingerprint"

    schema_version: str = V02_TOKEN_LIFECYCLE_SCHEMA_VERSION
    policy_id: str
    lifecycle_kind: V02LifecyclePolicyKind = V02LifecyclePolicyKind.token
    token_kind_code: str
    intended_issuer: str
    intended_audience: str
    maximum_ttl_seconds: int
    refresh_policy: str
    rotation_policy: str
    revocation_policy: str
    binding_requirements: tuple[str, ...]
    replay_requirements: tuple[str, ...]
    storage_prohibited: bool = True
    evidence_requirements: tuple[str, ...]
    tokens_generated: int = 0
    tokens_read: int = 0
    tokens_persisted: int = 0
    session_tokens_issued: int = 0
    access_tokens_issued: int = 0
    refresh_tokens_issued: int = 0
    policy_fingerprint: str | None = None


class V02SessionLifecyclePolicy(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "policy_fingerprint"

    schema_version: str = V02_SESSION_LIFECYCLE_SCHEMA_VERSION
    policy_id: str
    lifecycle_kind: V02LifecyclePolicyKind = V02LifecyclePolicyKind.session
    session_kind_code: str
    creation_preconditions: tuple[str, ...]
    maximum_duration_seconds: int
    idle_timeout_seconds: int
    concurrency_limit: int
    binding_requirements: tuple[str, ...]
    revocation_conditions: tuple[str, ...]
    logout_behavior: str
    cleanup_requirements: tuple[str, ...]
    audit_requirements: tuple[str, ...]
    session_tokens_issued: int = 0
    policy_fingerprint: str | None = None


class V02DeploymentArtifactComponent(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "component_fingerprint"

    component_name: str
    component_kind_code: str
    expected_digest_algorithm: str = "sha256"
    component_fingerprint: str | None = None


class V02DeploymentArtifactManifest(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "manifest_fingerprint"

    schema_version: str = V02_DEPLOYMENT_MANIFEST_SCHEMA_VERSION
    manifest_id: str
    source_commit: str
    source_tree_fingerprint: str
    target_platform_code: str
    architecture_code: str
    artifact_kind_code: str
    expected_artifact_name: str
    expected_digest_algorithm: str
    dependency_manifest_fingerprints: tuple[str, ...]
    build_configuration_fingerprint: str
    container_configuration_fingerprint: str
    runtime_entrypoint_fingerprint: str
    required_environment_class_codes: tuple[str, ...]
    artifact_evidence_requirements: tuple[str, ...]
    components: tuple[V02DeploymentArtifactComponent, ...]
    artifact_bytes_present: bool = False
    artifact_built: bool = False
    artifact_pushed: bool = False
    release_candidate: bool = False
    manifest_fingerprint: str | None = None


class V02SbomComponent(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "component_fingerprint"

    component_name: str
    component_version: str
    component_type: str
    dependency_scope: str
    supplier_code: str
    licence_identifier: str
    component_fingerprint: str | None = None


class V02SoftwareBillOfMaterialsProjection(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "sbom_projection_fingerprint"

    schema_version: str = V02_SBOM_SCHEMA_VERSION
    projection_id: str
    components: tuple[V02SbomComponent, ...]
    private_registry_credentials_present: bool = False
    evidence_maturity: V02EvidenceMaturity = V02EvidenceMaturity.deterministic_simulation
    sbom_projection_fingerprint: str | None = None


class V02ArtifactProvenanceRecord(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "provenance_fingerprint"

    schema_version: str = V02_ARTIFACT_PROVENANCE_SCHEMA_VERSION
    provenance_id: str
    source_commit: str
    predecessor_fingerprint: str = ZERO_FINGERPRINT
    actor_role_code: str
    evidence_fingerprints: tuple[str, ...]
    artifact_bytes_present: bool = False
    provenance_fingerprint: str | None = None


class V02ReproducibleBuildEvidenceProjection(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "projection_fingerprint"

    schema_version: str = V02_REPRODUCIBLE_BUILD_SCHEMA_VERSION
    projection_id: str
    evidence_maturity: V02EvidenceMaturity = V02EvidenceMaturity.deterministic_simulation
    planning_fingerprint: str
    actual_build_executed: bool = False
    actual_artifact_created: bool = False
    reproducible_build_claimed_passed: bool = False
    projection_fingerprint: str | None = None


class V02RollbackStep(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "step_fingerprint"

    step_id: str
    sequence: int
    dependency_step_ids: tuple[str, ...] = ()
    precondition_codes: tuple[str, ...]
    health_check_references: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    command_present: bool = False
    step_fingerprint: str | None = None


class V02RollbackPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "rollback_plan_fingerprint"

    schema_version: str = V02_ROLLBACK_SCHEMA_VERSION
    plan_id: str
    rollback_trigger: str
    artifact_version_lineage: tuple[str, ...]
    configuration_compatibility: str
    database_compatibility_assumptions: str
    pre_rollback_checks: tuple[str, ...]
    steps: tuple[V02RollbackStep, ...]
    post_rollback_checks: tuple[str, ...]
    health_validation: tuple[str, ...]
    abort_conditions: tuple[str, ...]
    operator_approvals: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    rollback_execution_enabled: bool = False
    maximum_rollback_executions: int = 0
    rollback_plan_fingerprint: str | None = None


class V02RollbackDrillPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "drill_plan_fingerprint"

    schema_version: str = V02_ROLLBACK_DRILL_SCHEMA_VERSION
    drill_id: str
    rollback_plan_ids: tuple[str, ...]
    validation_steps: tuple[str, ...]
    execute_commands: bool = False
    mutate_database: bool = False
    replace_artifact: bool = False
    change_configuration: bool = False
    restart_service: bool = False
    deploy: bool = False
    drill_plan_fingerprint: str | None = None


class V02RollbackDrillSimulationResult(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "drill_result_fingerprint"

    schema_version: str = V02_ROLLBACK_DRILL_SCHEMA_VERSION
    drill_id: str
    rollback_plan_ids: tuple[str, ...]
    dependencies_valid: bool
    preconditions_valid: bool
    health_checks_referenced: bool
    evidence_requirements_valid: bool
    commands_executed: int = 0
    database_mutations: int = 0
    deployments: int = 0
    drill_result_fingerprint: str | None = None


class V02ProductionObservabilitySignalDefinition(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "signal_fingerprint"

    signal_id: str
    signal_kind: V02ObservabilitySignalKind
    source_component: str
    safe_attributes: tuple[str, ...]
    prohibited_attributes: tuple[str, ...]
    severity: str
    expected_rate: str
    alert_threshold: str
    redaction_policy: str
    retention_class: str
    operator_action: str
    evidence_requirement: str
    signal_fingerprint: str | None = None


class V02ProductionObservabilitySchema(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "observability_schema_fingerprint"

    schema_version: str = V02_OBSERVABILITY_SCHEMA_VERSION
    signals: tuple[V02ProductionObservabilitySignalDefinition, ...]
    production_observability_export_enabled: bool = False
    external_log_export_enabled: bool = False
    external_metric_export_enabled: bool = False
    external_trace_export_enabled: bool = False
    observability_schema_fingerprint: str | None = None


class V02ProductionHealthReadinessCheck(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "check_fingerprint"

    check_id: str
    component: str
    criticality: str
    interval_design: str
    timeout_design: str
    success_criteria: str
    failure_behavior: str
    readiness_effect: str
    liveness_effect: str
    operator_response: str
    evidence_requirement: str
    check_fingerprint: str | None = None


class V02ProductionHealthReadinessSchema(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "health_readiness_schema_fingerprint"

    schema_version: str = V02_HEALTH_READINESS_SCHEMA_VERSION
    checks: tuple[V02ProductionHealthReadinessCheck, ...]
    health_readiness_schema_fingerprint: str | None = None


class V02ProductionThreatControl(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "control_fingerprint"

    control_id: str
    control_summary: str
    evidence_requirement: str
    control_fingerprint: str | None = None


class V02ProductionThreatScenario(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "scenario_fingerprint"

    scenario_id: str
    category: V02ThreatCategory
    affected_assets: tuple[str, ...]
    preconditions: tuple[str, ...]
    attack_or_failure_code: str
    existing_controls: tuple[str, ...]
    required_controls: tuple[str, ...]
    residual_risk: str
    evidence_maturity: V02EvidenceMaturity
    release_gate_ids: tuple[str, ...]
    scenario_fingerprint: str | None = None


class V02ProductionThreatModel(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "threat_model_fingerprint"

    schema_version: str = V02_THREAT_MODEL_SCHEMA_VERSION
    scenarios: tuple[V02ProductionThreatScenario, ...]
    controls: tuple[V02ProductionThreatControl, ...]
    exploit_code_present: bool = False
    operational_secrets_present: bool = False
    threat_model_fingerprint: str | None = None


class V02RuntimeReleaseGuardDecision(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "runtime_guard_fingerprint"

    schema_version: str = V02_RUNTIME_GUARD_SCHEMA_VERSION
    outcome: V02RuntimeGuardOutcome
    qualification_decision: V02QualificationFoundationDecision
    release_hold: bool = True
    staging_evidence_required: bool = True
    production_evidence_required: bool = True
    v02_release_ready: bool = False
    v02_release_candidate_created: bool = False
    runtime_guard_fingerprint: str | None = None


class V02ReleaseGate(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "gate_fingerprint"

    gate_id: str
    gate_name: str
    outcome: V02ReleaseGateOutcome
    evidence_maturity: V02EvidenceMaturity
    evidence_fingerprints: tuple[str, ...]
    staging_evidence_required: bool
    production_evidence_required: bool
    release_ready_effect: bool = False
    gate_fingerprint: str | None = None


class V02ReleaseGateMatrix(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "release_gate_matrix_fingerprint"

    schema_version: str = V02_RELEASE_GATE_SCHEMA_VERSION
    gates: tuple[V02ReleaseGate, ...]
    v02_release_ready: bool = False
    v02_release_candidate_created: bool = False
    release_gate_matrix_fingerprint: str | None = None

    @model_validator(mode="after")
    def release_gates_are_exact(self) -> Self:
        if tuple(gate.gate_id for gate in self.gates) != CANONICAL_RELEASE_GATE_IDS:
            raise ValueError("release gate matrix must contain exactly 24 gates")
        if any(gate.release_ready_effect for gate in self.gates):
            raise ValueError("AION-239 gates cannot make v0.2 release-ready")
        return self


class V02StagingQualificationEnvironmentProfile(V02StrictModel):
    profile_id: str
    network_isolation_assumptions: tuple[str, ...]
    identity_provider_fixture_strategy: str


class V02StagingAcceptanceCriterion(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "criterion_fingerprint"

    criterion_id: str
    criterion_summary: str
    evidence_requirement: str
    staging_evidence_required: bool = True
    criterion_fingerprint: str | None = None


class V02StagingQualificationPlan(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "staging_plan_fingerprint"

    schema_version: str = V02_STAGING_PLAN_SCHEMA_VERSION
    plan_id: str
    environment_profile: V02StagingQualificationEnvironmentProfile
    credential_token_prerequisites: tuple[str, ...]
    replay_ledger_prerequisites: tuple[str, ...]
    artifact_transfer_prerequisites: tuple[str, ...]
    deployment_order: tuple[str, ...]
    health_validation: tuple[str, ...]
    observability_validation: tuple[str, ...]
    rollback_drill: str
    security_tests: tuple[str, ...]
    evidence_capture: tuple[str, ...]
    cleanup: tuple[str, ...]
    operator_approvals: tuple[str, ...]
    acceptance_criteria: tuple[V02StagingAcceptanceCriterion, ...]
    staging_runtime_authorized: bool = False
    staging_deployment_enabled: bool = False
    maximum_staging_deployments: int = 0
    staging_plan_fingerprint: str | None = None


class V02QualificationIntegrityAudit(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "integrity_fingerprint"

    schema_version: str = V02_QUALIFICATION_INTEGRITY_SCHEMA_VERSION
    integrity_status: V02IntegrityStatus
    checked_fingerprints: tuple[str, ...]
    redaction_passed: bool = True
    zero_effects_passed: bool = True
    exact_replay_passed: bool = True
    changed_replay_rejected: bool = True
    integrity_fingerprint: str | None = None


class V02QualificationEvidenceRecord(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "evidence_fingerprint"

    schema_version: str = V02_QUALIFICATION_EVIDENCE_SCHEMA_VERSION
    evidence_id: str
    evidence_maturity: V02EvidenceMaturity
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False
    evidence_payload_fingerprint: str
    evidence_fingerprint: str | None = None


class V02QualificationRunResult(V02FingerprintedModel):
    fingerprint_field: ClassVar[str] = "run_fingerprint"

    schema_version: str = V02_QUALIFICATION_RUN_SCHEMA_VERSION
    run_id: str
    pilot_id: str = PILOT_ID
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    program_id: str = PROGRAM_ID
    mode: Literal["deterministic-local-simulation"] = "deterministic-local-simulation"
    component_binding_fingerprint: str
    authorization_envelope_fingerprint: str
    qualification_candidate_fingerprint: str
    gap_matrix_fingerprint: str
    production_auth_composition_fingerprint: str
    request_identity_plan_fingerprint: str
    replay_provisioning_plan_fingerprint: str
    identity_provider_manifest_fingerprints: tuple[str, ...]
    public_key_lifecycle_policy_fingerprints: tuple[str, ...]
    protected_material_policy_fingerprints: tuple[str, ...]
    credential_policy_fingerprints: tuple[str, ...]
    token_policy_fingerprints: tuple[str, ...]
    session_policy_fingerprints: tuple[str, ...]
    deployment_artifact_manifest_fingerprints: tuple[str, ...]
    sbom_projection_fingerprint: str
    artifact_provenance_chain_head: str
    reproducibility_projection_fingerprints: tuple[str, ...]
    rollback_plan_fingerprints: tuple[str, ...]
    rollback_drill_result_fingerprint: str
    observability_schema_fingerprint: str
    health_readiness_schema_fingerprint: str
    threat_model_fingerprint: str
    runtime_guard_fingerprint: str
    release_gate_matrix_fingerprint: str
    staging_plan_fingerprint: str
    qualification_decision: V02QualificationFoundationDecision
    qualification_sessions_started: int = 1
    qualification_sessions_closed: int = 1
    active_qualification_sessions_after_close: int = 0
    qualification_runs_completed: int = 1
    readiness_domains_evaluated: int = 20
    readiness_gaps_evaluated: int = 20
    identity_provider_manifests_validated: int = 1
    public_key_lifecycle_policies_validated: int = 3
    protected_material_classes_validated: int = 16
    credential_lifecycle_policies_validated: int = 4
    token_lifecycle_policies_validated: int = 4
    session_lifecycle_policies_validated: int = 3
    replay_provisioning_plans_validated: int = 1
    deployment_artifact_manifests_validated: int = 1
    sbom_components_projected: int = 12
    artifact_provenance_records_validated: int = 4
    reproducibility_projections_validated: int = 2
    rollback_plans_validated: int = 2
    rollback_drill_plans_validated: int = 1
    rollback_drill_simulations: int = 1
    observability_signals_validated: int = 24
    health_readiness_checks_validated: int = 12
    threat_scenarios_validated: int = 40
    release_gates_evaluated: int = 24
    staging_qualification_plans_validated: int = 1
    exact_replays_returned: int = 1
    changed_replays_rejected: int = 1
    release_ready_decisions: int = 0
    release_hold_decisions: int = 1
    staging_evidence_required: bool = True
    production_evidence_required: bool = True
    v02_release_ready: bool = False
    v02_release_candidate_created: bool = False
    temporary_files_retained: int = 0
    integrity_passed: bool = True
    redacted: bool = True
    production_effect: bool = False
    runtime_effect: bool = False
    prohibited_effect_counters: dict[str, int] = Field(default_factory=dict)
    report_fingerprint: str | None = None
    run_fingerprint: str | None = None

    @model_validator(mode="after")
    def qualification_run_is_release_hold(self) -> Self:
        expected = dict(PROHIBITED_EFFECT_COUNTERS)
        if self.prohibited_effect_counters and self.prohibited_effect_counters != expected:
            raise ValueError("prohibited-effect counters must remain zero")
        if not self.prohibited_effect_counters:
            object.__setattr__(self, "prohibited_effect_counters", expected)
        required = (
            V02QualificationFoundationDecision
            .foundation_implemented_release_not_ready_staging_evidence_required
        )
        if self.qualification_decision is not required:
            raise ValueError("AION-239 qualification must return release hold")
        report_payload = self.model_dump(
            mode="json", exclude={"report_fingerprint", "run_fingerprint"}
        )
        expected_report = v02_qualification_fingerprint(report_payload)
        if self.report_fingerprint is None:
            object.__setattr__(self, "report_fingerprint", expected_report)
        elif self.report_fingerprint != expected_report:
            raise ValueError("report_fingerprint must match canonical report payload")
        return self


class InMemoryV02QualificationRepository:
    """Copy-on-write in-memory qualification-session repository."""

    def __init__(self) -> None:
        self._sessions: dict[str, V02QualificationSession] = {}
        self._runs: dict[str, V02QualificationRunResult] = {}
        self._run_request_fingerprints: dict[str, str] = {}

    def snapshot_sessions(self) -> tuple[V02QualificationSession, ...]:
        return tuple(deepcopy(self._sessions[key]) for key in sorted(self._sessions))

    def active_session_count(self) -> int:
        return sum(1 for session in self._sessions.values() if session.active)

    def start_session(self, session: V02QualificationSession) -> None:
        if self.active_session_count() >= 1:
            raise ValueError("maximum one active qualification session is allowed")
        self._sessions = {**self._sessions, session.session_id: deepcopy(session)}

    def close_session(self, session_id: str) -> V02QualificationSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError("unknown qualification session")
        closed = session.close()
        self._sessions = {**self._sessions, session_id: closed}
        return deepcopy(closed)

    def record_run(
        self,
        result: V02QualificationRunResult,
        request_fingerprint: str,
    ) -> None:
        if len(self._runs) >= 20:
            raise ValueError("maximum local qualification runs exceeded")
        self._runs = {**self._runs, result.run_id: deepcopy(result)}
        self._run_request_fingerprints = {
            **self._run_request_fingerprints,
            result.run_id: request_fingerprint,
        }

    def replay_exact_run(
        self,
        run_id: str,
        request_fingerprint: str,
    ) -> V02QualificationRunResult:
        if self._run_request_fingerprints.get(run_id) != request_fingerprint:
            raise ValueError("changed replay rejected")
        return deepcopy(self._runs[run_id])


def _assert_acyclic(graph: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            raise ValueError("circular gap dependencies are not allowed")
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for graph_node in graph:
        visit(graph_node)


def resource_limits() -> V02QualificationResourceLimits:
    return V02QualificationResourceLimits(**{**POSITIVE_RESOURCE_LIMITS, **ZERO_RESOURCE_LIMITS})


def confirmation_fingerprint() -> str:
    return v02_qualification_fingerprint(
        {
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "confirmation": LOCAL_QUALIFICATION_CONFIRMATION_TEXT,
            "program_id": PROGRAM_ID,
        }
    )


def canonical_component_binding(
    current_main_commit: str = AION_238_MERGE_COMMIT,
    binding_timestamp: datetime | None = None,
) -> V02ReleaseQualificationComponentBinding:
    return V02ReleaseQualificationComponentBinding(
        current_main_commit=current_main_commit,
        binding_timestamp=binding_timestamp or utc_now(),
        component_fingerprints={
            "secure_runtime": PARENT_EVALUATION_REPORT_FINGERPRINT,
            "model_gateway": v02_qualification_fingerprint("model-gateway-implemented"),
            "capability_runtime": v02_qualification_fingerprint(
                "capability-runtime-implemented"
            ),
            "operator_console": v02_qualification_fingerprint(
                "operator-console-implemented"
            ),
        },
    )


def canonical_authorization_envelope(
    component_binding: V02ReleaseQualificationComponentBinding,
    session_id: str = "AION-239-LOCAL-SESSION-001",
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> V02ReleaseQualificationAuthorizationEnvelope:
    start = created_at or utc_now()
    return V02ReleaseQualificationAuthorizationEnvelope(
        component_binding_fingerprint=component_binding.binding_fingerprint
        or ZERO_FINGERPRINT,
        qualification_session_id=session_id,
        operator_identity_fingerprint=v02_qualification_fingerprint(
            "redacted-aion-239-local-operator"
        ),
        resource_limit_fingerprint=v02_qualification_fingerprint(resource_limits()),
        created_at=start,
        expires_at=expires_at or start + timedelta(minutes=45),
        confirmation_fingerprint=confirmation_fingerprint(),
    )


def canonical_session_plan(
    session_id: str = "AION-239-LOCAL-SESSION-001",
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> V02QualificationSessionPlan:
    start = created_at or utc_now()
    return V02QualificationSessionPlan(
        session_id=session_id,
        created_at=start,
        expires_at=expires_at or start + timedelta(minutes=45),
    )


def canonical_gap_matrix() -> V02ProductionReadinessGapMatrix:
    gaps: list[V02ProductionReadinessGap] = []
    production_domains = {
        V02ReadinessDomain.production_auth_composition,
        V02ReadinessDomain.replay_ledger_provisioning,
        V02ReadinessDomain.identity_provider_adapter,
        V02ReadinessDomain.public_key_lifecycle,
        V02ReadinessDomain.credential_lifecycle,
        V02ReadinessDomain.token_lifecycle,
        V02ReadinessDomain.session_lifecycle,
        V02ReadinessDomain.health_readiness,
    }
    staging_domains = {
        V02ReadinessDomain.deployment_artifact,
        V02ReadinessDomain.reproducible_build,
        V02ReadinessDomain.rollback,
        V02ReadinessDomain.observability,
        V02ReadinessDomain.health_readiness,
        V02ReadinessDomain.release_gate_governance,
        V02ReadinessDomain.staging_qualification,
    }
    for index, domain in enumerate(READINESS_DOMAINS, start=1):
        dependency = () if index == 1 else (f"V02-GAP-{index - 1:03d}",)
        staging = domain in staging_domains
        production = domain in production_domains
        if staging:
            status = V02GapStatus.staging_evidence_required
            maturity = V02EvidenceMaturity.staging_required
        elif production:
            status = V02GapStatus.production_evidence_required
            maturity = V02EvidenceMaturity.production_required
        else:
            status = V02GapStatus.mitigation_designed_evidence_pending
            maturity = V02EvidenceMaturity.design_recorded
        gaps.append(
            V02ProductionReadinessGap(
                gap_id=CANONICAL_GAP_IDS[domain],
                readiness_domain=domain,
                severity=V02GapSeverity.critical if production else V02GapSeverity.major,
                minimum_severity=V02GapSeverity.major,
                current_status=status,
                evidence_maturity=maturity,
                required_evidence_codes=(f"{domain.value}-evidence",),
                dependency_gap_ids=dependency,
                responsible_role_code="release-qualification-reviewer",
                target_task=FORMAL_CLOSEOUT_TASK if index < 23 else "AION-241",
                design_fingerprint=v02_qualification_fingerprint(
                    {"domain": domain.value, "design": "recorded"}
                ),
                current_evidence_fingerprints=(),
                operational_evidence_required=True,
                staging_evidence_required=staging,
                production_evidence_required=production,
            )
        )
    return V02ProductionReadinessGapMatrix(
        gaps=tuple(gaps),
        evidence_requirements=tuple(
            V02GapEvidenceRequirement(
                evidence_code=f"{domain.value}-evidence",
                maturity_required=V02EvidenceMaturity.staging_required
                if domain is V02ReadinessDomain.staging_qualification
                else V02EvidenceMaturity.design_recorded,
                staging_evidence_required=domain
                is V02ReadinessDomain.staging_qualification,
                production_evidence_required=False,
            )
            for domain in READINESS_DOMAINS
        ),
        readiness_domains_represented=READINESS_DOMAINS,
    )


def canonical_production_auth_composition() -> V02ProductionAuthCompositionPlan:
    components = (
        "offline_ed25519_identity_assertion_verification",
        "trusted_public_key_registry",
        "identity_assertion_replay_protection",
        "secure_request_identity_projection",
        "actor_context_construction",
        "policy_evaluation",
        "risk_evaluation",
        "guardrails",
        "approval_evidence",
        "kill_switch",
        "audit_and_observability",
    )
    bindings = tuple(
        V02ProductionAuthComponentBinding(
            component_code=component,
            component_status="implemented_disabled_or_design_bound",
            source_contract_fingerprint=v02_qualification_fingerprint(component),
        )
        for component in components
    )
    return V02ProductionAuthCompositionPlan(
        component_order=components,
        component_bindings=bindings,
        fail_closed_behavior="reject on missing verified claim, replay failure or policy denial",
        issuer_audience_validation="issuer and audience must be verified before projection",
        trust_boundary_transitions=(
            "external assertion to offline verification",
            "verified assertion to RequestIdentity",
            "RequestIdentity to ActorContext",
        ),
        replay_validation_order=("assertion fingerprint", "issuer", "audience", "subject"),
        request_identity_construction_order=(
            "issuer",
            "audience",
            "subject",
            "actor_id",
            "workspace_id",
            "roles",
            "permissions",
        ),
        actor_context_construction_order=(
            "actor_id",
            "workspace_id",
            "roles",
            "permissions",
            "security_scopes",
        ),
        policy_and_approval_precedence=(
            "kill_switch",
            "replay_protection",
            "policy",
            "risk",
            "guardrails",
            "explicit_approval",
        ),
        session_creation_and_expiry="future sessions require verified identity and bounded expiry",
        error_redaction="errors expose reason codes only",
        audit_requirements=("redacted decision", "fingerprint lineage", "operator review"),
        health_requirements=("identity verifier ready", "replay ledger ready", "policy ready"),
        rollback_boundary="design only; rollback execution disabled",
    )


def canonical_request_identity_plan() -> V02VerifiedRequestIdentityIntegrationPlan:
    mapping_codes = (
        "issuer",
        "audience",
        "subject",
        "actor_id",
        "workspace_id",
        "roles",
        "permissions",
        "security_scopes",
        "trace_id",
        "correlation_id",
        "assertion_id",
        "assertion_fingerprint",
        "authentication_time",
        "expiry_time",
    )
    return V02VerifiedRequestIdentityIntegrationPlan(
        claim_mappings=tuple(
            V02ClaimMappingPolicy(
                claim_code=code,
                target_field_code=code,
                closed_allowlist=("operator", "auditor")
                if code in {"roles", "permissions"}
                else (),
            )
            for code in mapping_codes
        ),
        actor_context_projection_policies=tuple(
            V02ActorContextProjectionPolicy(
                projection_code=f"project-{code}",
                source_fields=(code,),
                target_actor_context_field=code,
            )
            for code in (
                "actor_id",
                "workspace_id",
                "roles",
                "permissions",
                "security_scopes",
            )
        ),
    )


def canonical_replay_provisioning_plan() -> V02ReplayLedgerProvisioningPlan:
    return V02ReplayLedgerProvisioningPlan(
        backend_class_code="future-managed-sql-ledger",
        schema_fingerprint=v02_qualification_fingerprint("replay-ledger-schema-v02"),
        unique_key_design="issuer-audience-subject-assertion-fingerprint",
        transaction_isolation_requirement="serializable-or-equivalent",
        encryption_at_rest_requirement="required-before-staging",
        encryption_in_transit_requirement="required-before-staging",
        retention_policy="bounded assertion replay retention",
        cleanup_policy="operator-approved retention expiry cleanup",
        capacity_plan=V02ReplayLedgerCapacityPlan(
            estimated_daily_assertions=100000,
            retention_days=30,
            cleanup_policy="deterministic partition expiry design",
        ),
        availability_plan=V02ReplayLedgerAvailabilityPlan(
            high_availability_design="multi-zone managed datastore design",
            restore_objective="validated restore before staging",
            recovery_point_objective="fifteen-minute design target",
            recovery_time_objective="one-hour design target",
        ),
        backup_restore_plan=V02ReplayLedgerBackupRestorePlan(
            backup_frequency="daily design target",
            restore_validation="deterministic restore rehearsal required",
            evidence_requirement="AION-241 staging drill evidence",
        ),
        migration_plan=V02ReplayLedgerMigrationPlan(
            migration_sequence=("create schema", "backfill none", "validate unique keys"),
            rollback_boundary="no live rollback in AION-239",
            evidence_requirement="future staging migration evidence",
        ),
        monitoring_requirements=("write conflict rate", "availability", "latency"),
        fail_closed_behavior="deny assertion when replay status cannot be proven",
        provisioning_evidence_requirements=("schema review", "restore drill", "capacity test"),
    )


def canonical_identity_provider_manifests() -> tuple[V02IdentityProviderAdapterManifest, ...]:
    mappings = tuple(
        V02IdentityProviderClaimMapping(
            provider_claim_code=code,
            request_identity_field_code=code,
        )
        for code in ("issuer", "audience", "subject", "roles")
    )
    trust = V02IdentityProviderTrustPlan(
        issuer_fingerprint=v02_qualification_fingerprint("issuer-design"),
        metadata_location_fingerprint=v02_qualification_fingerprint("metadata-design"),
        audience_fingerprint=v02_qualification_fingerprint("audience-design"),
        public_key_source_policy_fingerprint=v02_qualification_fingerprint(
            "public-key-source-policy"
        ),
        authentication_flow_design_fingerprint=v02_qualification_fingerprint(
            "authentication-flow-design"
        ),
        logout_design_fingerprint=v02_qualification_fingerprint("logout-design"),
        failure_behavior="fail closed without network calls",
    )
    return (
        V02IdentityProviderAdapterManifest(
            provider_code="future-generic-oidc",
            protocol_kind=V02IdentityProviderProtocolKind.generic_oidc_metadata,
            claim_mappings=mappings,
            trust_plan=trust,
        ),
    )


def canonical_key_policies() -> tuple[V02PublicKeyLifecyclePolicy, ...]:
    return tuple(
        V02PublicKeyLifecyclePolicy(
            policy_id=f"V02-KEY-POLICY-{index:03d}",
            key_status_lifecycle=(
                "planned",
                "active_future",
                "rotating_future",
                "revoked_future",
            ),
            activation_window="future bounded activation window",
            rotation_plan=V02PublicKeyRotationPlan(
                rotation_cadence=f"{index * 30}-day design cadence",
                overlap_window="dual-key overlap design",
                emergency_rollover="operator-approved emergency rollover design",
            ),
            revocation_plan=V02PublicKeyRevocationPlan(
                revocation_propagation="future registry revocation propagation",
                stale_key_rejection="reject stale key fingerprints",
                audit_requirement="redacted revocation audit evidence",
            ),
            compromise_response_plan=V02PublicKeyCompromiseResponsePlan(
                compromise_detection="future anomaly and operator report",
                response_sequence=("freeze trust", "publish revocation", "require re-assertion"),
                evidence_requirement="compromise response drill evidence",
            ),
            audit_requirements=("rotation approval", "revocation proof"),
            evidence_requirements=("key lifecycle design", "future staging key drill"),
            rollback_boundary="no live key rotation in AION-239",
        )
        for index in range(1, 4)
    )


def canonical_protected_material_policy() -> V02ProtectedMaterialLifecyclePolicy:
    classes = tuple(
        V02ProtectedMaterialClass(
            material_class_code=code,
            classification_level="protected",
            allowed_handling_locations=("redacted evidence", "future secured runtime"),
            logging_policy="fingerprints only",
            evidence_policy="redacted metadata only",
            retention_policy="bounded by governance record",
        )
        for code in PROTECTED_MATERIAL_CLASS_CODES
    )
    return V02ProtectedMaterialLifecyclePolicy(
        policy_id="V02-PROTECTED-MATERIAL-POLICY-001",
        classes=classes,
    )


def canonical_credential_policies() -> tuple[V02CredentialLifecyclePolicy, ...]:
    return tuple(
        V02CredentialLifecyclePolicy(
            policy_id=f"V02-CREDENTIAL-POLICY-{index:03d}",
            credential_kind_code=code,
            owner_role_code="security-operator",
            intended_storage_class_code="future-managed-secret-store",
            generation_authority="future dual-control ceremony",
            rotation_cadence="future bounded rotation design",
            expiry_policy="mandatory expiry before production use",
            revocation_policy="operator-approved revocation",
            compromise_response="freeze and revoke future credential",
            break_glass_policy="requires separate authorization",
        )
        for index, code in enumerate(
            ("idp-client", "signing-key-access", "database-access", "registry-access"),
            start=1,
        )
    )


def canonical_token_policies() -> tuple[V02TokenLifecyclePolicy, ...]:
    return tuple(
        V02TokenLifecyclePolicy(
            policy_id=f"V02-TOKEN-POLICY-{index:03d}",
            token_kind_code=code,
            intended_issuer="future-verified-idp",
            intended_audience="future-aion-runtime",
            maximum_ttl_seconds=900,
            refresh_policy="future refresh requires explicit approval",
            rotation_policy="rotate by issuer policy",
            revocation_policy="fail closed on revocation uncertainty",
            binding_requirements=("issuer", "audience", "subject", "workspace"),
            replay_requirements=("assertion fingerprint", "session binding"),
            evidence_requirements=("staging token fixture evidence",),
        )
        for index, code in enumerate(
            ("identity-assertion", "access", "refresh", "session"),
            start=1,
        )
    )


def canonical_session_policies() -> tuple[V02SessionLifecyclePolicy, ...]:
    return tuple(
        V02SessionLifecyclePolicy(
            policy_id=f"V02-SESSION-POLICY-{index:03d}",
            session_kind_code=code,
            creation_preconditions=("verified identity", "replay check", "policy allow"),
            maximum_duration_seconds=3600,
            idle_timeout_seconds=900,
            concurrency_limit=2,
            binding_requirements=("actor", "workspace", "trace"),
            revocation_conditions=("identity revoked", "role removed", "kill switch"),
            logout_behavior="future explicit logout invalidates server session",
            cleanup_requirements=("remove references", "retain redacted audit"),
            audit_requirements=("session created", "session closed", "session revoked"),
        )
        for index, code in enumerate(("operator", "auditor", "break-glass-review"), start=1)
    )


def canonical_deployment_manifests() -> tuple[V02DeploymentArtifactManifest, ...]:
    return (
        V02DeploymentArtifactManifest(
            manifest_id="V02-ARTIFACT-MANIFEST-001",
            source_commit=AION_238_MERGE_COMMIT,
            source_tree_fingerprint=v02_qualification_fingerprint("source-tree"),
            target_platform_code="future-staging-linux",
            architecture_code="amd64",
            artifact_kind_code="container-image-projection",
            expected_artifact_name="aion-brain-v02-candidate-projection",
            expected_digest_algorithm="sha256",
            dependency_manifest_fingerprints=(
                v02_qualification_fingerprint("brain-api-pyproject"),
            ),
            build_configuration_fingerprint=v02_qualification_fingerprint("build-config"),
            container_configuration_fingerprint=v02_qualification_fingerprint(
                "container-config"
            ),
            runtime_entrypoint_fingerprint=v02_qualification_fingerprint("entrypoint"),
            required_environment_class_codes=("staging", "release-candidate"),
            artifact_evidence_requirements=("future build provenance", "future scan evidence"),
            components=(
                V02DeploymentArtifactComponent(
                    component_name="brain-api",
                    component_kind_code="service",
                ),
            ),
        ),
    )


def canonical_sbom_projection(component_count: int = 12) -> V02SoftwareBillOfMaterialsProjection:
    return V02SoftwareBillOfMaterialsProjection(
        projection_id="V02-SBOM-PROJECTION-001",
        components=tuple(
            V02SbomComponent(
                component_name=f"aion-component-{index:02d}",
                component_version="design-projection",
                component_type="python-module",
                dependency_scope="runtime-design",
                supplier_code="aion-local",
                licence_identifier="unknown-pending-review",
            )
            for index in range(1, component_count + 1)
        ),
    )


def canonical_provenance_records(count: int = 4) -> tuple[V02ArtifactProvenanceRecord, ...]:
    records: list[V02ArtifactProvenanceRecord] = []
    predecessor = ZERO_FINGERPRINT
    for index in range(1, count + 1):
        record = V02ArtifactProvenanceRecord(
            provenance_id=f"V02-PROVENANCE-{index:03d}",
            source_commit=AION_238_MERGE_COMMIT,
            predecessor_fingerprint=predecessor,
            actor_role_code="release-qualification-runner",
            evidence_fingerprints=(v02_qualification_fingerprint(f"evidence-{index}"),),
        )
        records.append(record)
        predecessor = record.provenance_fingerprint or ZERO_FINGERPRINT
    return tuple(records)


def canonical_reproducibility_projections() -> tuple[
    V02ReproducibleBuildEvidenceProjection, ...
]:
    return tuple(
        V02ReproducibleBuildEvidenceProjection(
            projection_id=f"V02-REPRODUCIBLE-BUILD-{index:03d}",
            planning_fingerprint=v02_qualification_fingerprint(f"build-plan-{index}"),
        )
        for index in range(1, 3)
    )


def canonical_rollback_plans() -> tuple[V02RollbackPlan, ...]:
    plans: list[V02RollbackPlan] = []
    for index in range(1, 3):
        steps = tuple(
            V02RollbackStep(
                step_id=f"V02-ROLLBACK-{index:03d}-STEP-{step:03d}",
                sequence=step,
                dependency_step_ids=()
                if step == 1
                else (f"V02-ROLLBACK-{index:03d}-STEP-{step - 1:03d}",),
                precondition_codes=("operator-approval", "health-baseline"),
                health_check_references=("V02-HEALTH-001",),
                evidence_requirements=("staging drill evidence",),
            )
            for step in range(1, 4)
        )
        plans.append(
            V02RollbackPlan(
                plan_id=f"V02-ROLLBACK-PLAN-{index:03d}",
                rollback_trigger="failed health readiness gate",
                artifact_version_lineage=("previous", "candidate"),
                configuration_compatibility="requires explicit compatibility evidence",
                database_compatibility_assumptions="no database mutation in AION-239",
                pre_rollback_checks=("operator approval", "health snapshot"),
                steps=steps,
                post_rollback_checks=("health check", "audit check"),
                health_validation=("V02-HEALTH-001",),
                abort_conditions=("missing approval", "unknown artifact lineage"),
                operator_approvals=("release manager", "security reviewer"),
                evidence_requirements=("future staging rollback drill",),
            )
        )
    return tuple(plans)


def canonical_rollback_drill_plan(plans: tuple[V02RollbackPlan, ...]) -> V02RollbackDrillPlan:
    return V02RollbackDrillPlan(
        drill_id="V02-ROLLBACK-DRILL-001",
        rollback_plan_ids=tuple(plan.plan_id for plan in plans),
        validation_steps=(
            "validate step ordering",
            "validate dependencies",
            "validate health references",
            "validate evidence requirements",
        ),
    )


def canonical_observability_schema(count: int = 24) -> V02ProductionObservabilitySchema:
    kinds = tuple(V02ObservabilitySignalKind)
    return V02ProductionObservabilitySchema(
        signals=tuple(
            V02ProductionObservabilitySignalDefinition(
                signal_id=f"V02-OBS-{index:03d}",
                signal_kind=kinds[(index - 1) % len(kinds)],
                source_component=f"component-{index % 8}",
                safe_attributes=("event_id", "fingerprint", "reason_code"),
                prohibited_attributes=("raw_claim", "secret_value", "token_value"),
                severity="info" if index % 3 else "warning",
                expected_rate="bounded by staging load profile",
                alert_threshold="future operator threshold",
                redaction_policy="redacted metadata only",
                retention_class="governed",
                operator_action="review evidence",
                evidence_requirement="future observability capture",
            )
            for index in range(1, count + 1)
        )
    )


def canonical_health_readiness_schema(count: int = 12) -> V02ProductionHealthReadinessSchema:
    return V02ProductionHealthReadinessSchema(
        checks=tuple(
            V02ProductionHealthReadinessCheck(
                check_id=f"V02-HEALTH-{index:03d}",
                component=f"component-{index % 6}",
                criticality="critical" if index % 2 else "major",
                interval_design="future bounded interval",
                timeout_design="future bounded timeout",
                success_criteria="safe readiness response",
                failure_behavior="fail closed",
                readiness_effect="not ready on failure",
                liveness_effect="operator review required",
                operator_response="inspect redacted evidence",
                evidence_requirement="future health evidence",
            )
            for index in range(1, count + 1)
        )
    )


def canonical_threat_model(count: int = 40) -> V02ProductionThreatModel:
    names = (
        "identity-provider-spoofing",
        "issuer-substitution",
        "audience-substitution",
        "claim-escalation",
        "public-key-compromise",
        "stale-key-acceptance",
        "replay-ledger-outage",
        "replay-ledger-collision",
        "credential-leakage",
        "token-theft",
        "refresh-token-replay",
        "session-fixation",
        "session-revocation-failure",
        "protected-material-logging",
        "audit-redaction-failure",
        "sbom-tampering",
        "dependency-substitution",
        "artifact-substitution",
        "provenance-forgery",
        "build-non-reproducibility",
        "rollback-failure",
        "rollback-data-incompatibility",
        "health-check-bypass",
        "observability-blind-spot",
        "release-gate-bypass",
        "staging-to-production-drift",
        "configuration-drift",
        "secret-injection-failure",
        "public-listener-exposure",
        "external-egress-activation",
        "production-write-activation",
        "release-tag-mutation",
        "release-publication-without-authorization",
    )
    categories = tuple(V02ThreatCategory)
    scenarios = []
    for index in range(1, count + 1):
        scenarios.append(
            V02ProductionThreatScenario(
                scenario_id=f"V02-THREAT-{index:03d}",
                category=categories[(index - 1) % len(categories)],
                affected_assets=("identity", "release", "evidence"),
                preconditions=("future production integration exists",),
                attack_or_failure_code=names[(index - 1) % len(names)],
                existing_controls=("disabled runtime", "no release authority"),
                required_controls=("staging evidence", "operator review"),
                residual_risk="requires future evidence before release",
                evidence_maturity=V02EvidenceMaturity.design_recorded,
                release_gate_ids=(CANONICAL_RELEASE_GATE_IDS[(index - 1) % 24],),
            )
        )
    return V02ProductionThreatModel(
        scenarios=tuple(scenarios),
        controls=tuple(
            V02ProductionThreatControl(
                control_id=f"V02-CONTROL-{index:03d}",
                control_summary="fail-closed disabled qualification boundary",
                evidence_requirement="operator review evidence",
            )
            for index in range(1, 9)
        ),
    )


def canonical_release_gate_matrix() -> V02ReleaseGateMatrix:
    names = (
        "SRI program complete",
        "qualification authorization exact",
        "source-tree integrity",
        "production-auth composition design",
        "RequestIdentity integration design",
        "replay-ledger provisioning design",
        "IdP adapter design",
        "public-key lifecycle design",
        "protected-material design",
        "credential lifecycle design",
        "token lifecycle design",
        "session lifecycle design",
        "deployment-artifact manifest",
        "SBOM projection",
        "provenance design",
        "reproducibility design",
        "rollback design",
        "observability design",
        "health-readiness design",
        "threat-model design",
        "runtime-guard design",
        "staging-qualification plan",
        "staging execution evidence",
        "release-candidate authorization",
    )
    gates = []
    for index, gate_id in enumerate(CANONICAL_RELEASE_GATE_IDS, start=1):
        if index == 23:
            outcome = V02ReleaseGateOutcome.requires_staging_evidence
            maturity = V02EvidenceMaturity.staging_required
            staging_required = True
            production_required = False
        elif index == 24:
            outcome = V02ReleaseGateOutcome.blocked
            maturity = V02EvidenceMaturity.production_required
            staging_required = True
            production_required = True
        elif index in {1, 2, 3}:
            outcome = V02ReleaseGateOutcome.pass_verified_local
            maturity = V02EvidenceMaturity.verified_local
            staging_required = False
            production_required = False
        else:
            outcome = V02ReleaseGateOutcome.pass_design
            maturity = V02EvidenceMaturity.design_recorded
            staging_required = False
            production_required = index in {4, 6, 7, 8, 10, 11, 12}
        gates.append(
            V02ReleaseGate(
                gate_id=gate_id,
                gate_name=names[index - 1],
                outcome=outcome,
                evidence_maturity=maturity,
                evidence_fingerprints=(v02_qualification_fingerprint(gate_id),),
                staging_evidence_required=staging_required,
                production_evidence_required=production_required,
            )
        )
    return V02ReleaseGateMatrix(gates=tuple(gates))


def canonical_staging_plan() -> V02StagingQualificationPlan:
    return V02StagingQualificationPlan(
        plan_id="V02-STAGING-QUALIFICATION-PLAN-001",
        environment_profile=V02StagingQualificationEnvironmentProfile(
            profile_id="future-isolated-staging",
            network_isolation_assumptions=("deny public ingress by default",),
            identity_provider_fixture_strategy=(
                "offline fixture first, future IdP separately authorized"
            ),
        ),
        credential_token_prerequisites=("future dual-control provisioning",),
        replay_ledger_prerequisites=("future managed ledger evidence",),
        artifact_transfer_prerequisites=("future signed artifact manifest",),
        deployment_order=("database plan review", "artifact deploy", "health validate"),
        health_validation=("V02-HEALTH-001", "V02-HEALTH-002"),
        observability_validation=("V02-OBS-001", "V02-OBS-002"),
        rollback_drill="V02-ROLLBACK-DRILL-001",
        security_tests=("identity spoofing", "replay rejection", "redaction"),
        evidence_capture=("health evidence", "rollback evidence", "operator approval"),
        cleanup=("remove fixtures", "close staging session"),
        operator_approvals=("release manager", "security reviewer"),
        acceptance_criteria=tuple(
            V02StagingAcceptanceCriterion(
                criterion_id=f"V02-STAGING-AC-{index:03d}",
                criterion_summary="future staging evidence required",
                evidence_requirement="AION-241 evidence",
            )
            for index in range(1, 4)
        ),
    )


__all__ = [
    name
    for name in globals()
    if name.isupper()
    or name.startswith(("V02", "canonical_", "v02_", "resource_limits"))
    or name
    in {
        "AUTHORIZATION_TRANSACTION_ID",
        "AUTHORIZATION_SCOPE",
        "CANDIDATE_ID",
        "CANONICAL_GAP_IDS",
        "CANONICAL_RELEASE_GATE_IDS",
        "FOUNDATION_DECISION",
        "FOUNDATION_PROGRAM_STATE",
        "FOUNDATION_STATE",
        "FORMAL_CLOSEOUT_TASK",
        "IMPLEMENTATION_TASK",
        "InMemoryV02QualificationRepository",
        "LOCAL_QUALIFICATION_CONFIRMATION_TEXT",
        "PILOT_ID",
        "POSITIVE_RESOURCE_LIMITS",
        "PROGRAM_ID",
        "PROGRAM_NAME",
        "PROHIBITED_EFFECT_COUNTERS",
        "PROTECTED_MATERIAL_CLASS_CODES",
        "READINESS_DOMAINS",
        "ZERO_FINGERPRINT",
        "ZERO_RESOURCE_LIMITS",
        "canonical_json",
        "confirmation_fingerprint",
        "utc_now",
    }
]
