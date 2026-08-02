"""Controlled isolated v0.2 staging-qualification contracts."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

V02_STAGING_CONTRACT_SCHEMA_VERSION = "aion-v02-staging-qualification/v1"
V02_STAGING_AUTHORIZATION_SCHEMA_VERSION = (
    "aion-v02-staging-qualification-authorization/v1"
)
V02_STAGING_COMPONENT_BINDING_SCHEMA_VERSION = "aion-v02-staging-component-binding/v1"
V02_STAGING_SESSION_SCHEMA_VERSION = "aion-v02-staging-session/v1"
V02_SOURCE_SNAPSHOT_SCHEMA_VERSION = "aion-v02-staging-source-snapshot/v1"
V02_BUILD_PLAN_SCHEMA_VERSION = "aion-v02-staging-build-plan/v1"
V02_ARTIFACT_MANIFEST_SCHEMA_VERSION = "aion-v02-staging-artifact-manifest/v1"
V02_SBOM_SCHEMA_VERSION = "aion-v02-staging-sbom/v1"
V02_PROVENANCE_SCHEMA_VERSION = "aion-v02-staging-provenance/v1"
V02_ENVIRONMENT_PROFILE_SCHEMA_VERSION = "aion-v02-staging-environment-profile/v1"
V02_IDENTITY_FIXTURE_SCHEMA_VERSION = "aion-v02-staging-identity-fixture/v1"
V02_REPLAY_FIXTURE_SCHEMA_VERSION = "aion-v02-staging-replay-fixture/v1"
V02_DEPLOYMENT_PLAN_SCHEMA_VERSION = "aion-v02-staging-deployment-plan/v1"
V02_HEALTH_READINESS_SCHEMA_VERSION = "aion-v02-staging-health-readiness/v1"
V02_OBSERVABILITY_SCHEMA_VERSION = "aion-v02-staging-observability/v1"
V02_SECURITY_VALIDATION_SCHEMA_VERSION = "aion-v02-staging-security-validation/v1"
V02_ROLLBACK_SCHEMA_VERSION = "aion-v02-staging-rollback/v1"
V02_CLEANUP_SCHEMA_VERSION = "aion-v02-staging-cleanup/v1"
V02_INTEGRITY_SCHEMA_VERSION = "aion-v02-staging-integrity/v1"
V02_EVIDENCE_SCHEMA_VERSION = "aion-v02-staging-evidence/v1"

PROGRAM_ID = "AION-V02-RELEASE-QUALIFICATION-001"
PROGRAM_NAME = "AION v0.2 Release Qualification Program"
AUTHORIZATION_TRANSACTION_ID = "AION-240-V02RQ-0002"
APPROVAL_RECORD_ID = "AION-240-V02RQ-0002"
PARENT_AUTHORIZATION_TRANSACTION_ID = "AION-238-V02RQ-0001"
PARENT_EVALUATION_ID = "AION-V02RQPE-001"
PARENT_EVALUATION_BASE_COMMIT = "45b50d79edc6080e2e64e0566dc17ead9bcf0090"
PARENT_EVALUATION_REPORT_FINGERPRINT = (
    "6a9c94362fc9258db33ec41914080834b4af2811ac4b1d934ee43113779c72f4"
)
PARENT_EVALUATION_DECISION = (
    "DISABLED_V02_PRODUCTION_READINESS_QUALIFICATION_FOUNDATION_OPERATOR_"
    "EVALUATION_PASS_RECOMMEND_CONTROLLED_ISOLATED_STAGING_ARTIFACT_AND_"
    "ROLLBACK_DRILL_QUALIFICATION_AUTHORIZATION"
)
PARENT_IMPLEMENTATION_TASK = "AION-239"
PARENT_IMPLEMENTATION_PRS = (158,)
PARENT_IMPLEMENTATION_FEATURE_COMMITS = (
    "a1d5d1ee2b0d991f3074c796d664105225b51856",
    "fa789d5c43709d606bb088a69451b7a43cf32a17",
)
PARENT_IMPLEMENTATION_MERGE_COMMITS = ("154d58f182871ce18abad860f3bb76e5a006ebad",)
PARENT_IMPLEMENTATION_MAIN_COMMIT = "154d58f182871ce18abad860f3bb76e5a006ebad"
AION_240_BRANCH = "phase/v02-release-qualification-foundation-evaluation-staging-authorization"
AION_240_HARNESS_COMMIT = "45b50d79edc6080e2e64e0566dc17ead9bcf0090"
AION_240_CLOSEOUT_COMMIT = "ab76a9fe4814e9a36a612cc768b343fd6117dcaa"
AION_240_MERGE_COMMIT = "9f6b899f84ef8d9a53598871dbbd5b0cb3bacb38"
AION_240_MERGED_AT = "2026-08-01T23:23:06Z"
IMPLEMENTATION_TASK = "AION-241"
FORMAL_CLOSEOUT_TASK = "AION-242"
FINAL_PLANNED_TASK = "AION-244"
CANDIDATE_ID = "controlled-isolated-local-staging-artifact-and-rollback-drill-core"
WORKSTREAM = "v02-controlled-staging-qualification"
PILOT_ID = "AION-241-controlled-isolated-local-staging-artifact-and-rollback-drill-pilot"
AUTHORIZATION_SCOPE = (
    "controlled-isolated-local-staging-source-snapshot-offline-container-build-"
    "local-artifact-sbom-provenance-ephemeral-auth-replay-fixtures-loopback-health-"
    "observability-security-validation-rollback-drill-cleanup-no-public-egress-no-"
    "production-no-release-core"
)
LOCAL_CONFIRMATION_TEXT = "RUN_CONTROLLED_ISOLATED_STAGING_QUALIFICATION"
LOOPBACK_HOST = "127.0.0.1"
ZERO_FINGERPRINT = "0000000000000000000000000000000000000000000000000000000000000000"
STAGING_STATE = "implemented_isolated_local_pilot_complete_pending_AION-242_closeout"
PROGRAM_STATE = (
    "controlled_isolated_staging_qualification_implemented_pilot_complete_pending_closeout"
)

SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,180}$")
LOWER_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
IMAGE_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
IMAGE_REF_PATTERN = re.compile(r"^[A-Za-z0-9./:_-]{1,240}$")
_PROTECTED_MARKERS = (
    "-----begin",
    "authorization header",
    "bearer ",
    "client_secret",
    "client secret",
    "password=",
    "api_key",
    "apikey",
    "private_key",
    "private key",
    "connection string",
    "raw identity assertion",
    "raw identity claim",
    "raw prompt",
    "raw model output",
    "raw log",
    "cookie",
    "token=",
    "sk-",
    "ghp_",
    "xoxb-",
)
_PROHIBITED_KEYS = {
    "authorization_header",
    "client_secret",
    "connection_string",
    "credential",
    "credential_value",
    "database_password",
    "password",
    "private_key",
    "raw_docker_environment",
    "raw_identity_assertion",
    "raw_logs",
    "raw_model_output",
    "raw_prompt",
    "secret",
    "secret_value",
    "signed_assertion",
    "token",
    "token_value",
}

APPROVED_CAPABILITIES: tuple[str, ...] = (
    "staging_qualification_contract_approved",
    "staging_qualification_authorization_envelope_approved",
    "qualification_foundation_component_composition_approved",
    "immutable_source_snapshot_approved",
    "read_only_git_archive_approved",
    "offline_local_container_build_approved",
    "local_staging_artifact_creation_approved",
    "local_artifact_digest_approved",
    "local_sbom_generation_approved",
    "local_artifact_provenance_approved",
    "local_reproducibility_comparison_approved",
    "isolated_internal_container_network_approved",
    "loopback_only_staging_exposure_approved",
    "ephemeral_offline_identity_fixture_approved",
    "ephemeral_in_memory_signing_key_approved",
    "ephemeral_replay_ledger_fixture_approved",
    "staging_runtime_session_approved",
    "local_health_readiness_validation_approved",
    "local_observability_capture_approved",
    "local_security_control_validation_approved",
    "identity_spoofing_negative_test_approved",
    "replay_rejection_negative_test_approved",
    "protected_material_redaction_test_approved",
    "staging_configuration_drift_detection_approved",
    "controlled_degradation_injection_approved",
    "staging_rollback_drill_approved",
    "post_rollback_health_validation_approved",
    "staging_evidence_bundle_approved",
    "complete_container_cleanup_approved",
    "complete_network_cleanup_approved",
    "complete_volume_cleanup_approved",
    "complete_image_cleanup_approved",
    "complete_temporary_root_cleanup_approved",
    "uninstalled_runner_allowlisted_docker_cli_approved",
    "uninstalled_runner_shell_false_subprocess_approved",
    "documentation_and_static_evidence_approved",
)

PROHIBITED_CAPABILITIES: tuple[str, ...] = (
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "public_listener_enabled",
    "non_loopback_listener_enabled",
    "registry_login_enabled",
    "registry_pull_enabled",
    "registry_push_enabled",
    "external_container_registry_enabled",
    "cloud_api_call_enabled",
    "external_identity_provider_call_enabled",
    "production_identity_provider_enabled",
    "production_credential_generation_enabled",
    "production_credential_read_enabled",
    "production_credential_persistence_enabled",
    "production_token_generation_enabled",
    "production_token_issuance_enabled",
    "production_token_persistence_enabled",
    "production_authorization_header_creation_enabled",
    "production_key_rotation_enabled",
    "production_replay_ledger_enabled",
    "production_database_provisioning_enabled",
    "production_database_operation_enabled",
    "production_observability_export_enabled",
    "external_log_export_enabled",
    "external_metric_export_enabled",
    "external_trace_export_enabled",
    "arbitrary_shell_execution_enabled",
    "arbitrary_subprocess_execution_enabled",
    "arbitrary_docker_command_enabled",
    "kubernetes_command_enabled",
    "terraform_command_enabled",
    "cloud_deployment_enabled",
    "production_deployment_enabled",
    "production_rollback_enabled",
    "production_canary_enabled",
    "actual_model_provider_call_enabled",
    "external_connector_execution_enabled",
    "external_tool_execution_enabled",
    "production_write_execution_enabled",
    "production_memory_write_enabled",
    "production_policy_mutation_enabled",
    "actual_belief_mutation_enabled",
    "source_rewrite_enabled",
    "runtime_git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "release_candidate_creation_enabled",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
    "production_runtime_authorized",
    "production_exposure",
)

POSITIVE_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_staging_qualification_sessions": 1,
    "maximum_source_snapshots": 2,
    "maximum_git_archive_operations": 2,
    "maximum_local_container_builds": 2,
    "maximum_local_staging_artifacts": 2,
    "maximum_local_container_images": 3,
    "maximum_active_staging_stacks": 1,
    "maximum_staging_deployments": 2,
    "maximum_staging_rollbacks": 1,
    "maximum_internal_container_networks": 1,
    "maximum_local_container_volumes": 4,
    "maximum_running_staging_containers": 6,
    "maximum_loopback_listeners": 4,
    "maximum_ephemeral_identity_keypairs": 1,
    "maximum_ephemeral_replay_ledgers": 1,
    "maximum_staging_session_seconds": 10800,
    "maximum_build_seconds": 3600,
    "maximum_deployment_seconds": 1800,
    "maximum_rollback_seconds": 1800,
    "maximum_build_context_bytes": 1073741824,
    "maximum_staging_artifact_bytes": 2147483648,
    "maximum_temporary_root_bytes": 5368709120,
    "maximum_sbom_components": 20000,
    "maximum_artifact_provenance_records": 5000,
    "maximum_health_readiness_checks": 500,
    "maximum_security_validation_scenarios": 200,
    "maximum_staging_http_requests": 5000,
    "maximum_local_observability_records": 10000,
    "maximum_evidence_records": 20000,
    "maximum_evidence_bytes": 104857600,
    "maximum_allowlisted_docker_cli_invocations": 100,
    "maximum_concurrent_runner_processes": 2,
}

ZERO_RESOURCE_LIMITS: tuple[str, ...] = (
    "maximum_public_network_calls",
    "maximum_external_network_egress_calls",
    "maximum_dns_resolutions",
    "maximum_public_listeners",
    "maximum_non_loopback_listeners",
    "maximum_registry_logins",
    "maximum_registry_pulls",
    "maximum_registry_pushes",
    "maximum_cloud_api_calls",
    "maximum_external_identity_provider_calls",
    "maximum_production_credentials_generated",
    "maximum_production_credentials_read",
    "maximum_production_credentials_persisted",
    "maximum_production_tokens_generated",
    "maximum_production_tokens_issued",
    "maximum_production_tokens_persisted",
    "maximum_production_authorization_headers_created",
    "maximum_production_key_rotations",
    "maximum_production_replay_ledger_writes",
    "maximum_production_database_operations",
    "maximum_external_log_exports",
    "maximum_external_metric_exports",
    "maximum_external_trace_exports",
    "maximum_kubernetes_commands",
    "maximum_terraform_commands",
    "maximum_cloud_deployments",
    "maximum_production_deployments",
    "maximum_production_rollbacks",
    "maximum_release_candidates_created",
    "maximum_v02_tags_created",
    "maximum_v02_releases_created",
)

PILOT_COUNTERS: dict[str, int | bool] = {
    "staging_qualification_sessions_started": 1,
    "staging_qualification_sessions_closed": 1,
    "active_qualification_sessions_after_close": 0,
    "source_snapshots_created": 1,
    "git_archive_operations": 1,
    "offline_local_builds_completed": 2,
    "registry_logins": 0,
    "registry_pulls": 0,
    "registry_pushes": 0,
    "local_staging_artifacts_created": 2,
    "release_candidates_created": 0,
    "sbom_projections_created": 1,
    "reproducibility_comparisons_completed": 1,
    "reproducibility_invariants_passed": True,
    "isolated_networks_created": 1,
    "isolated_networks_removed": 1,
    "staging_deployments_completed": 1,
    "public_listeners_created": 0,
    "non_loopback_listeners_created": 0,
    "ephemeral_identity_keypairs_created": 1,
    "ephemeral_identity_keypairs_persisted": 0,
    "ephemeral_replay_ledgers_created": 1,
    "ephemeral_replay_ledgers_persisted": 0,
    "identity_spoofing_tests_passed": 1,
    "controlled_degradations_injected": 1,
    "health_failures_detected": 1,
    "staging_rollbacks_completed": 1,
    "post_rollback_health_recovered": True,
    "external_log_exports": 0,
    "external_metric_exports": 0,
    "external_trace_exports": 0,
    "active_containers_after_cleanup": 0,
    "active_volumes_after_cleanup": 0,
    "active_networks_after_cleanup": 0,
    "run_owned_images_after_cleanup": 0,
    "temporary_files_retained": 0,
    "public_network_calls": 0,
    "external_network_egress_calls": 0,
    "dns_resolutions": 0,
    "external_identity_provider_calls": 0,
    "production_credentials_generated": 0,
    "production_credentials_read": 0,
    "production_credentials_persisted": 0,
    "production_tokens_generated": 0,
    "production_tokens_issued": 0,
    "production_tokens_persisted": 0,
    "production_replay_ledger_writes": 0,
    "production_database_operations": 0,
    "production_deployments": 0,
    "production_rollbacks": 0,
    "v02_tags_created": 0,
    "v02_releases_created": 0,
}

PROHIBITED_EFFECT_COUNTERS: dict[str, int] = {
    "public_network_calls": 0,
    "external_network_egress_calls": 0,
    "dns_resolutions": 0,
    "external_identity_provider_calls": 0,
    "production_credentials_generated": 0,
    "production_credentials_read": 0,
    "production_credentials_persisted": 0,
    "production_tokens_generated": 0,
    "production_tokens_issued": 0,
    "production_tokens_persisted": 0,
    "production_authorization_headers_created": 0,
    "production_key_rotations": 0,
    "production_replay_ledger_writes": 0,
    "production_database_operations": 0,
    "production_deployments": 0,
    "production_rollbacks": 0,
    "registry_logins": 0,
    "registry_pulls": 0,
    "registry_pushes": 0,
    "external_log_exports": 0,
    "external_metric_exports": 0,
    "external_trace_exports": 0,
    "release_candidates_created": 0,
    "v02_tags_created": 0,
    "v02_releases_created": 0,
}

REQUIRED_SOURCE_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/__init__.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/authorization.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/component_binding.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/source_snapshot.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/build_plan.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/artifact_manifest.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/sbom.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/provenance.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/environment_profile.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/identity_fixture.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/replay_fixture.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/deployment_plan.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/health_readiness.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/observability.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/security_validation.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/rollback.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/cleanup.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/integrity.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/evidence.py",
)

PROHIBITED_SOURCE_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/v02_staging_qualification/network_client.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/registry.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/cloud.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/kubernetes.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/terraform.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/production_deployment.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/production_database.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/credential_store.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/token_store.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/release_candidate.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/release_publisher.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/background_worker.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/scheduler.py",
    "services/brain-api/src/aion_brain/api/v02_staging_qualification.py",
)

REQUIRED_DEPENDENCY_IMAGES: tuple[str, ...] = (
    "pgvector/pgvector:pg16",
    "redis:7-alpine",
    "nats:2-alpine",
    "openpolicyagent/opa:latest",
)


class V02StagingQualificationMode(StrEnum):
    controlled_local_docker = "controlled_local_docker"
    operator_invoked_local = "operator_invoked_local"


class V02StagingSessionStatus(StrEnum):
    drafted = "drafted"
    authorized = "authorized"
    preflight = "preflight"
    snapshot_created = "snapshot_created"
    build_complete = "build_complete"
    deployed = "deployed"
    validating = "validating"
    degraded = "degraded"
    rolling_back = "rolling_back"
    recovered = "recovered"
    cleaning = "cleaning"
    closed = "closed"
    blocked = "blocked"
    failed = "failed"


class V02StagingBuildStatus(StrEnum):
    planned = "planned"
    building = "building"
    complete = "complete"
    compared = "compared"
    blocked = "blocked"
    failed = "failed"


class V02StagingDeploymentStatus(StrEnum):
    planned = "planned"
    starting = "starting"
    healthy = "healthy"
    degraded = "degraded"
    recovered = "recovered"
    stopped = "stopped"
    removed = "removed"
    failed = "failed"


class V02StagingRollbackStatus(StrEnum):
    planned = "planned"
    degradation_detected = "degradation_detected"
    executing = "executing"
    recovered = "recovered"
    complete = "complete"
    failed = "failed"


class V02StagingCleanupStatus(StrEnum):
    pending = "pending"
    executing = "executing"
    complete = "complete"
    incomplete = "incomplete"
    failed = "failed"


class V02StagingSecurityResult(StrEnum):
    passed = "passed"
    blocked = "blocked"
    failed = "failed"


class V02StagingIntegrityStatus(StrEnum):
    passed = "passed"
    failed = "failed"


class V02EvidenceMaturity(StrEnum):
    planned = "planned"
    implemented = "implemented"
    pilot_verified = "pilot_verified"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def canonical_json(payload: Any) -> str:
    """Serialize payload as deterministic JSON."""
    return json.dumps(
        _canonical_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def v02_staging_fingerprint(payload: Any) -> str:
    """Return the SHA-256 fingerprint of a canonical payload."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _canonical_ready(value.model_dump(mode="json"))
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _canonical_ready(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_canonical_ready(item) for item in value]
    return value


def _validate_identifier(value: str) -> str:
    if not SAFE_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError("identifier must be bounded safe ASCII")
    return value


def _validate_sha256(value: str) -> str:
    if not LOWER_SHA256_PATTERN.fullmatch(value):
        raise ValueError("fingerprint must be lowercase SHA-256")
    return value


def _validate_git_object(value: str) -> str:
    if not GIT_OBJECT_PATTERN.fullmatch(value):
        raise ValueError("Git object ID must be lowercase hex")
    return value


def _validate_image_id(value: str) -> str:
    if not IMAGE_ID_PATTERN.fullmatch(value):
        raise ValueError("image ID must be a sha256 fingerprint")
    return value


def _validate_image_ref(value: str) -> str:
    if not IMAGE_REF_PATTERN.fullmatch(value):
        raise ValueError("image reference must be bounded safe ASCII")
    if value.startswith(("http:", "https:", "ssh:", "tcp:")):
        raise ValueError("image reference must not be a remote endpoint")
    return value


def _assert_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC)


def _assert_no_protected_material(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for raw_key, nested in value.items():
            key = str(raw_key)
            if key.lower() in _PROHIBITED_KEYS and nested not in (None, False, 0, "", ()):
                raise ValueError(f"protected material is not allowed at {path}.{key}")
            _assert_no_protected_material(nested, f"{path}.{key}")
        return
    if isinstance(value, tuple | list):
        for index, nested in enumerate(value):
            _assert_no_protected_material(nested, f"{path}.{index}")
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("numeric evidence values must be finite")
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _PROTECTED_MARKERS):
            raise ValueError(f"protected material marker is not allowed at {path}")


class V02StagingStrictModel(BaseModel):
    """Strict base model for all staging qualification records."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def protected_material_absent(self) -> Self:
        _assert_no_protected_material(self.model_dump(mode="json"))
        return self


class V02StagingFrozenModel(V02StagingStrictModel):
    """Immutable strict base model."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class V02StagingFingerprintedModel(V02StagingFrozenModel):
    """Immutable model that carries a deterministic fingerprint."""

    fingerprint_field: ClassVar[str]

    @model_validator(mode="after")
    def set_fingerprint(self) -> Self:
        field_name = self.fingerprint_field
        payload = self.model_dump(mode="json", exclude={field_name})
        expected = v02_staging_fingerprint(payload)
        current = getattr(self, field_name)
        if current is None:
            object.__setattr__(self, field_name, expected)
        elif current != expected:
            raise ValueError(f"{field_name} must match canonical payload")
        return self


class V02StagingResourceLimits(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "resource_limit_fingerprint"

    schema_version: str = V02_STAGING_CONTRACT_SCHEMA_VERSION
    limits: dict[str, int] = Field(default_factory=dict)
    resource_limit_fingerprint: str | None = None

    @model_validator(mode="after")
    def limits_are_exact(self) -> Self:
        expected = {**POSITIVE_RESOURCE_LIMITS, **dict.fromkeys(ZERO_RESOURCE_LIMITS, 0)}
        if not self.limits:
            object.__setattr__(self, "limits", expected)
        elif self.limits != expected:
            raise ValueError("AION-241 resource limits must be exact")
        return self


class V02StagingQualificationComponentBinding(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "component_binding_fingerprint"

    schema_version: str = V02_STAGING_COMPONENT_BINDING_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    parent_authorization_transaction_id: str = PARENT_AUTHORIZATION_TRANSACTION_ID
    parent_evaluation_id: str = PARENT_EVALUATION_ID
    parent_evaluation_base_commit: str = PARENT_EVALUATION_BASE_COMMIT
    parent_evaluation_report_fingerprint: str = PARENT_EVALUATION_REPORT_FINGERPRINT
    parent_implementation_task: str = PARENT_IMPLEMENTATION_TASK
    parent_implementation_prs: tuple[int, ...] = PARENT_IMPLEMENTATION_PRS
    parent_implementation_feature_commits: tuple[str, ...] = PARENT_IMPLEMENTATION_FEATURE_COMMITS
    parent_implementation_merge_commits: tuple[str, ...] = PARENT_IMPLEMENTATION_MERGE_COMMITS
    parent_implementation_main_commit: str = PARENT_IMPLEMENTATION_MAIN_COMMIT
    aion_240_harness_commit: str = AION_240_HARNESS_COMMIT
    aion_240_closeout_commit: str = AION_240_CLOSEOUT_COMMIT
    aion_240_merge_commit: str = AION_240_MERGE_COMMIT
    current_source_commit: str
    current_git_tree_sha: str
    source_tree_fingerprint: str
    docker_context_fingerprint: str
    docker_server_fingerprint: str
    base_image_tag: str
    base_image_id: str
    base_image_fingerprint: str
    dependency_image_fingerprints: dict[str, str]
    resource_limit_fingerprint: str
    operator_confirmation_fingerprint: str
    binding_timestamp: datetime = Field(default_factory=utc_now)
    read_only: bool = True
    redacted: bool = True
    production_effect: bool = False
    release_effect: bool = False
    component_binding_fingerprint: str | None = None

    @field_validator(
        "parent_evaluation_base_commit",
        "parent_implementation_main_commit",
        "aion_240_harness_commit",
        "aion_240_closeout_commit",
        "aion_240_merge_commit",
        "current_source_commit",
        "current_git_tree_sha",
    )
    @classmethod
    def valid_commit(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator(
        "parent_evaluation_report_fingerprint",
        "source_tree_fingerprint",
        "docker_context_fingerprint",
        "docker_server_fingerprint",
        "base_image_fingerprint",
        "resource_limit_fingerprint",
        "operator_confirmation_fingerprint",
    )
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @field_validator("base_image_id")
    @classmethod
    def valid_base_image_id(cls, value: str) -> str:
        return _validate_image_id(value)

    @field_validator("base_image_tag")
    @classmethod
    def valid_base_image_tag(cls, value: str) -> str:
        return _validate_image_ref(value)

    @field_validator("binding_timestamp")
    @classmethod
    def valid_timestamp(cls, value: datetime) -> datetime:
        return _assert_utc(value)

    @model_validator(mode="after")
    def binding_is_exact(self) -> Self:
        required = {
            "program_id": PROGRAM_ID,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "parent_authorization_transaction_id": PARENT_AUTHORIZATION_TRANSACTION_ID,
            "parent_evaluation_id": PARENT_EVALUATION_ID,
            "parent_implementation_task": PARENT_IMPLEMENTATION_TASK,
        }
        for key, expected in required.items():
            if getattr(self, key) != expected:
                raise ValueError(f"component binding mismatch: {key}")
        if self.parent_implementation_prs != PARENT_IMPLEMENTATION_PRS:
            raise ValueError("component binding PR lineage mismatch")
        if self.parent_implementation_feature_commits != PARENT_IMPLEMENTATION_FEATURE_COMMITS:
            raise ValueError("component binding feature lineage mismatch")
        if self.parent_implementation_merge_commits != PARENT_IMPLEMENTATION_MERGE_COMMITS:
            raise ValueError("component binding merge lineage mismatch")
        if not self.dependency_image_fingerprints:
            raise ValueError("dependency image fingerprints are required")
        if not all(key in self.dependency_image_fingerprints for key in REQUIRED_DEPENDENCY_IMAGES):
            raise ValueError("all dependency-image fingerprints must be present")
        if not self.read_only or not self.redacted or self.production_effect or self.release_effect:
            raise ValueError("component binding must be read-only, redacted and effect-free")
        return self


class V02StagingQualificationAuthorizationEnvelope(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "authorization_fingerprint"

    schema_version: str = V02_STAGING_AUTHORIZATION_SCHEMA_VERSION
    program_id: str = PROGRAM_ID
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: str = APPROVAL_RECORD_ID
    candidate_id: str = CANDIDATE_ID
    workstream: str = WORKSTREAM
    implementation_task: str = IMPLEMENTATION_TASK
    formal_closeout_task: str = FORMAL_CLOSEOUT_TASK
    final_planned_task: str = FINAL_PLANNED_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    qualification_session_id: str
    component_binding_fingerprint: str
    resource_limit_fingerprint: str
    operator_confirmation_fingerprint: str
    approved_capabilities: dict[str, bool]
    prohibited_capabilities: dict[str, bool]
    authorization_active: bool = True
    authorization_consumed: bool = False
    authorization_expired: bool = False
    authorization_reusable: bool = False
    operator_invoked: bool = True
    local_docker_context: bool = True
    offline_build: bool = True
    internal_network_only: bool = True
    loopback_exposure_only: bool = True
    production_credentials: bool = False
    production_tokens: bool = False
    production_database: bool = False
    production_deployment: bool = False
    release_candidate: bool = False
    release_effect: bool = False
    authorization_fingerprint: str | None = None

    @field_validator(
        "component_binding_fingerprint",
        "resource_limit_fingerprint",
        "operator_confirmation_fingerprint",
    )
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @field_validator("qualification_session_id")
    @classmethod
    def valid_session_id(cls, value: str) -> str:
        return _validate_identifier(value)

    @model_validator(mode="after")
    def authorization_is_exact(self) -> Self:
        expected_approved = dict.fromkeys(APPROVED_CAPABILITIES, True)
        expected_prohibited = dict.fromkeys(PROHIBITED_CAPABILITIES, False)
        if self.approved_capabilities != expected_approved:
            raise ValueError("approved AION-241 capabilities must be exact")
        if self.prohibited_capabilities != expected_prohibited:
            raise ValueError("prohibited AION-241 capabilities must remain false")
        if not (
            self.authorization_active
            and not self.authorization_consumed
            and not self.authorization_expired
            and not self.authorization_reusable
        ):
            raise ValueError("AION-240-V02RQ-0002 must remain active and non-reusable")
        if not (
            self.operator_invoked
            and self.local_docker_context
            and self.offline_build
            and self.internal_network_only
            and self.loopback_exposure_only
        ):
            raise ValueError("controlled local staging authorization flags are incomplete")
        if any(
            (
                self.production_credentials,
                self.production_tokens,
                self.production_database,
                self.production_deployment,
                self.release_candidate,
                self.release_effect,
            )
        ):
            raise ValueError("authorization envelope must not allow production or release effects")
        return self


class V02StagingQualificationSessionPlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "session_plan_fingerprint"

    schema_version: str = V02_STAGING_SESSION_SCHEMA_VERSION
    session_id: str
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    mode: V02StagingQualificationMode = V02StagingQualificationMode.controlled_local_docker
    status: V02StagingSessionStatus = V02StagingSessionStatus.authorized
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    local_confirmation_text_fingerprint: str
    maximum_session_seconds: int = 10800
    session_plan_fingerprint: str | None = None

    @field_validator("session_id")
    @classmethod
    def valid_session_id(cls, value: str) -> str:
        return _validate_identifier(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def valid_timestamp(cls, value: datetime) -> datetime:
        return _assert_utc(value)

    @field_validator("local_confirmation_text_fingerprint")
    @classmethod
    def valid_confirmation_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def session_window_is_bounded(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("session expiry must be after creation")
        if (self.expires_at - self.created_at).total_seconds() > self.maximum_session_seconds:
            raise ValueError("staging qualification session exceeds three hours")
        return self


class V02StagingQualificationSession(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "session_fingerprint"

    schema_version: str = V02_STAGING_SESSION_SCHEMA_VERSION
    session_id: str
    session_plan_fingerprint: str
    status: V02StagingSessionStatus = V02StagingSessionStatus.preflight
    active: bool = True
    opened_at: datetime = Field(default_factory=utc_now)
    closed_at: datetime | None = None
    staging_resources_active: bool = False
    session_fingerprint: str | None = None

    @field_validator("session_id")
    @classmethod
    def valid_session_id(cls, value: str) -> str:
        return _validate_identifier(value)

    @field_validator("session_plan_fingerprint")
    @classmethod
    def valid_session_plan_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @field_validator("opened_at", "closed_at")
    @classmethod
    def valid_timestamp(cls, value: datetime | None) -> datetime | None:
        return _assert_utc(value) if value is not None else None

    def close(self, closed_at: datetime | None = None) -> V02StagingQualificationSession:
        return self.model_copy(
            update={
                "status": V02StagingSessionStatus.closed,
                "active": False,
                "closed_at": closed_at or utc_now(),
                "staging_resources_active": False,
                "session_fingerprint": None,
            }
        )


class V02StagingSourceFileRecord(V02StagingFrozenModel):
    relative_path: str
    byte_count: int
    sha256: str

    @field_validator("relative_path")
    @classmethod
    def safe_relative_path(cls, value: str) -> str:
        if value.startswith("/") or ".." in value.split("/"):
            raise ValueError("source paths must be relative and traversal-free")
        return value

    @field_validator("sha256")
    @classmethod
    def valid_sha256(cls, value: str) -> str:
        return _validate_sha256(value)


class V02StagingSourceSnapshotPlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "snapshot_plan_fingerprint"

    schema_version: str = V02_SOURCE_SNAPSHOT_SCHEMA_VERSION
    source_commit: str
    git_tree_sha: str
    archive_operation_count: int = 1
    read_only_git_archive: bool = True
    working_tree_clean_required: bool = True
    source_mutation_allowed: bool = False
    snapshot_plan_fingerprint: str | None = None

    @field_validator("source_commit")
    @classmethod
    def valid_commit(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator("git_tree_sha")
    @classmethod
    def valid_tree(cls, value: str) -> str:
        return _validate_git_object(value)

    @model_validator(mode="after")
    def snapshot_is_read_only(self) -> Self:
        if self.archive_operation_count > 2 or not self.read_only_git_archive:
            raise ValueError("source snapshot must use bounded read-only Git archive")
        if self.source_mutation_allowed:
            raise ValueError("source mutation is not allowed")
        return self


class V02StagingSourceSnapshotManifest(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "source_tree_fingerprint"

    schema_version: str = V02_SOURCE_SNAPSHOT_SCHEMA_VERSION
    source_commit: str
    git_tree_sha: str
    git_archive_fingerprint: str
    extracted_file_count: int
    total_byte_count: int
    file_manifest_fingerprint: str
    file_records: tuple[V02StagingSourceFileRecord, ...]
    source_snapshot_read_only: bool = True
    source_tree_fingerprint: str | None = None

    @field_validator("source_commit", "git_tree_sha")
    @classmethod
    def valid_git_object(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator("git_archive_fingerprint", "file_manifest_fingerprint")
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def snapshot_counts_match(self) -> Self:
        if self.extracted_file_count != len(self.file_records):
            raise ValueError("source snapshot file count mismatch")
        if self.total_byte_count != sum(record.byte_count for record in self.file_records):
            raise ValueError("source snapshot byte count mismatch")
        if not self.source_snapshot_read_only:
            raise ValueError("source snapshot must be read-only")
        return self


class V02StagingDockerContextProjection(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "docker_context_fingerprint"

    schema_version: str = V02_ENVIRONMENT_PROFILE_SCHEMA_VERSION
    context_name: str
    endpoint_kind: Literal["local_unix_socket"]
    docker_host_set: bool = False
    server_os: Literal["linux"] = "linux"
    server_architecture: Literal["arm64", "aarch64"] = "arm64"
    buildx_available: bool = True
    compose_v2_available: bool = True
    remote_context: bool = False
    docker_context_fingerprint: str | None = None

    @model_validator(mode="after")
    def docker_context_is_local(self) -> Self:
        if self.docker_host_set or self.remote_context:
            raise ValueError("remote Docker context is not allowed")
        if not (self.buildx_available and self.compose_v2_available):
            raise ValueError("Docker Buildx and Compose v2 are required")
        return self


class V02StagingLocalImageRecord(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "image_fingerprint"

    schema_version: str = V02_ARTIFACT_MANIFEST_SCHEMA_VERSION
    image_tag: str
    image_id: str
    os: Literal["linux"] = "linux"
    architecture: Literal["arm64", "aarch64"] = "arm64"
    source_revision: str | None = None
    stable_local_tag: bool = True
    probe_passed: bool = True
    image_fingerprint: str | None = None

    @field_validator("image_tag")
    @classmethod
    def valid_image_tag(cls, value: str) -> str:
        return _validate_image_ref(value)

    @field_validator("image_id")
    @classmethod
    def valid_image_id(cls, value: str) -> str:
        return _validate_image_id(value)

    @field_validator("source_revision")
    @classmethod
    def valid_source_revision(cls, value: str | None) -> str | None:
        return _validate_git_object(value) if value is not None else None

    @model_validator(mode="after")
    def image_is_usable(self) -> Self:
        if not self.stable_local_tag or not self.probe_passed:
            raise ValueError("selected image must have a stable local tag and pass probes")
        return self


class V02StagingLocalImageInventory(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "inventory_fingerprint"

    schema_version: str = V02_ARTIFACT_MANIFEST_SCHEMA_VERSION
    base_image: V02StagingLocalImageRecord
    dependency_images: dict[str, V02StagingLocalImageRecord]
    registry_logins: int = 0
    registry_pulls: int = 0
    registry_pushes: int = 0
    inventory_fingerprint: str | None = None

    @model_validator(mode="after")
    def inventory_is_local(self) -> Self:
        if set(self.dependency_images) != set(REQUIRED_DEPENDENCY_IMAGES):
            raise ValueError("local dependency image inventory must be exact")
        if self.registry_logins or self.registry_pulls or self.registry_pushes:
            raise ValueError("registry operations are not allowed")
        return self


class V02StagingBuildPlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "build_plan_fingerprint"

    schema_version: str = V02_BUILD_PLAN_SCHEMA_VERSION
    build_plan_id: str
    source_commit: str
    source_tree_fingerprint: str
    base_image_tag: str
    base_image_id: str
    generated_dockerfile_fingerprint: str
    build_context_fingerprint: str
    build_count: int = 2
    pull_policy: Literal["false"] = "false"
    network_mode: Literal["none"] = "none"
    package_downloads: int = 0
    registry_logins: int = 0
    registry_pulls: int = 0
    registry_pushes: int = 0
    release_candidate: bool = False
    production: bool = False
    build_plan_fingerprint: str | None = None

    @field_validator("source_commit")
    @classmethod
    def valid_commit(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator(
        "source_tree_fingerprint",
        "generated_dockerfile_fingerprint",
        "build_context_fingerprint",
    )
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @field_validator("base_image_tag")
    @classmethod
    def valid_base_image_tag(cls, value: str) -> str:
        return _validate_image_ref(value)

    @field_validator("base_image_id")
    @classmethod
    def valid_base_image_id(cls, value: str) -> str:
        return _validate_image_id(value)

    @model_validator(mode="after")
    def build_is_offline(self) -> Self:
        if self.build_count != 2:
            raise ValueError("AION-241 must complete exactly two offline builds")
        if any(
            (
                self.package_downloads,
                self.registry_logins,
                self.registry_pulls,
                self.registry_pushes,
            )
        ):
            raise ValueError("offline build plan must have zero registry and package activity")
        if self.release_candidate or self.production:
            raise ValueError("staging artifact is not production or a release candidate")
        return self


class V02StagingArtifactComponent(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "component_fingerprint"

    component_name: str
    component_kind: str
    image_id: str | None = None
    source_fingerprint: str
    component_fingerprint: str | None = None

    @field_validator("component_name", "component_kind")
    @classmethod
    def valid_identifier(cls, value: str) -> str:
        return _validate_identifier(value)

    @field_validator("image_id")
    @classmethod
    def valid_image_id(cls, value: str | None) -> str | None:
        return _validate_image_id(value) if value is not None else None

    @field_validator("source_fingerprint")
    @classmethod
    def valid_source_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)


class V02StagingArtifactManifest(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "artifact_manifest_fingerprint"

    schema_version: str = V02_ARTIFACT_MANIFEST_SCHEMA_VERSION
    manifest_id: str
    source_commit: str
    source_tree_fingerprint: str
    base_image_id: str
    staging_image_id: str
    artifact_kind: Literal["local_staging_container_image"] = "local_staging_container_image"
    release_candidate: bool = False
    production: bool = False
    components: tuple[V02StagingArtifactComponent, ...]
    artifact_manifest_fingerprint: str | None = None

    @field_validator("source_commit")
    @classmethod
    def valid_commit(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator("source_tree_fingerprint")
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @field_validator("base_image_id", "staging_image_id")
    @classmethod
    def valid_image_id(cls, value: str) -> str:
        return _validate_image_id(value)

    @model_validator(mode="after")
    def artifact_is_staging_only(self) -> Self:
        if not self.components:
            raise ValueError("artifact manifest requires components")
        if self.release_candidate or self.production:
            raise ValueError("artifact manifest must remain staging-only")
        return self


class V02StagingSbomComponent(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "component_fingerprint"

    name: str
    normalized_name: str
    version: str
    scope: str = "installed_distribution"
    source_classification: str = "local_staging_projection"
    component_fingerprint: str | None = None

    @field_validator("name", "normalized_name", "scope", "source_classification")
    @classmethod
    def valid_identifier(cls, value: str) -> str:
        return _validate_identifier(value)


class V02StagingSoftwareBillOfMaterials(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "sbom_fingerprint"

    schema_version: str = V02_SBOM_SCHEMA_VERSION
    sbom_kind: Literal[
        "local_staging_installed_distribution_projection"
    ] = "local_staging_installed_distribution_projection"
    source_tree_fingerprint: str
    base_image_fingerprint: str
    component_count: int
    components: tuple[V02StagingSbomComponent, ...]
    vulnerability_scan_performed: bool = False
    registry_called: bool = False
    final_release_sbom: bool = False
    sbom_fingerprint: str | None = None

    @field_validator("source_tree_fingerprint", "base_image_fingerprint")
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def sbom_is_projection(self) -> Self:
        if self.component_count != len(self.components):
            raise ValueError("SBOM component count mismatch")
        if self.component_count <= 0 or self.component_count > 20000:
            raise ValueError("SBOM component count outside AION-241 bounds")
        if self.vulnerability_scan_performed or self.registry_called or self.final_release_sbom:
            raise ValueError("AION-241 SBOM is a local projection only")
        return self


class V02StagingArtifactProvenanceRecord(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "provenance_fingerprint"

    schema_version: str = V02_PROVENANCE_SCHEMA_VERSION
    provenance_id: str
    source_commit: str
    source_tree_fingerprint: str
    git_archive_fingerprint: str
    base_image_id: str
    dependency_image_fingerprints: dict[str, str]
    generated_dockerfile_fingerprint: str
    build_context_fingerprint: str
    network_mode: Literal["none"] = "none"
    pull_policy: Literal["false"] = "false"
    staging_image_id: str
    normalized_image_config_fingerprint: str
    rootfs_layer_fingerprints: tuple[str, ...]
    sbom_fingerprint: str
    production: bool = False
    release_candidate: bool = False
    provenance_fingerprint: str | None = None

    @field_validator("source_commit")
    @classmethod
    def valid_commit(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator(
        "source_tree_fingerprint",
        "git_archive_fingerprint",
        "generated_dockerfile_fingerprint",
        "build_context_fingerprint",
        "normalized_image_config_fingerprint",
        "sbom_fingerprint",
    )
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @field_validator("base_image_id", "staging_image_id")
    @classmethod
    def valid_image_id(cls, value: str) -> str:
        return _validate_image_id(value)

    @model_validator(mode="after")
    def provenance_is_staging_only(self) -> Self:
        if set(self.dependency_image_fingerprints) != set(REQUIRED_DEPENDENCY_IMAGES):
            raise ValueError("provenance must bind every local dependency image")
        if not self.rootfs_layer_fingerprints:
            raise ValueError("provenance must include rootfs layer fingerprints")
        if self.production or self.release_candidate:
            raise ValueError("provenance must not claim production or release-candidate state")
        return self


class V02StagingReproducibilityComparison(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "comparison_fingerprint"

    schema_version: str = V02_PROVENANCE_SCHEMA_VERSION
    source_commit: str
    source_tree_fingerprint: str
    base_image_id: str
    generated_dockerfile_fingerprint: str
    build_context_fingerprint: str
    first_image_id: str
    second_image_id: str
    invariant_checks: dict[str, bool]
    reproducibility_invariants_passed: bool
    byte_for_byte_reproducibility_confirmed: bool
    comparison_fingerprint: str | None = None

    @field_validator("source_commit")
    @classmethod
    def valid_commit(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator(
        "source_tree_fingerprint",
        "generated_dockerfile_fingerprint",
        "build_context_fingerprint",
    )
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @field_validator("base_image_id", "first_image_id", "second_image_id")
    @classmethod
    def valid_image_id(cls, value: str) -> str:
        return _validate_image_id(value)

    @model_validator(mode="after")
    def invariants_must_pass(self) -> Self:
        if not self.invariant_checks or not all(self.invariant_checks.values()):
            raise ValueError("all reproducibility invariants must pass")
        if not self.reproducibility_invariants_passed:
            raise ValueError("reproducibility invariants must pass")
        return self


class V02StagingEnvironmentProfile(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "environment_profile_fingerprint"

    schema_version: str = V02_ENVIRONMENT_PROFILE_SCHEMA_VERSION
    profile_id: str
    project_name_fingerprint: str
    internal_network: bool = True
    attachable_network: bool = False
    enable_ipv6: bool = False
    loopback_host: str = LOOPBACK_HOST
    ephemeral_port_used: bool = True
    actual_port_retained: bool = False
    public_network_access_enabled: bool = False
    external_network_egress_enabled: bool = False
    dns_resolution_enabled: bool = False
    dependency_host_ports: int = 0
    production_environment: bool = False
    production_credentials: bool = False
    production_tokens: bool = False
    production_database: bool = False
    environment_profile_fingerprint: str | None = None

    @field_validator("project_name_fingerprint")
    @classmethod
    def valid_project_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def environment_is_isolated(self) -> Self:
        if not self.internal_network or self.attachable_network or self.enable_ipv6:
            raise ValueError("staging network must be internal, non-attachable and IPv4-only")
        if self.loopback_host != LOOPBACK_HOST or not self.ephemeral_port_used:
            raise ValueError("Brain API exposure must be loopback-only on an ephemeral port")
        if (
            self.actual_port_retained
            or self.public_network_access_enabled
            or self.external_network_egress_enabled
            or self.dns_resolution_enabled
            or self.dependency_host_ports
            or self.production_environment
            or self.production_credentials
            or self.production_tokens
            or self.production_database
        ):
            raise ValueError("staging environment contains prohibited exposure")
        return self


class V02StagingIdentityFixturePlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "identity_fixture_plan_fingerprint"

    schema_version: str = V02_IDENTITY_FIXTURE_SCHEMA_VERSION
    fixture_id: str
    keypair_count: int = 1
    private_key_persisted: int = 0
    external_identity_provider_calls: int = 0
    synthetic_actor: bool = True
    synthetic_workspace: bool = True
    local_issuer: bool = True
    local_audience: bool = True
    identity_fixture_plan_fingerprint: str | None = None

    @model_validator(mode="after")
    def identity_fixture_is_offline(self) -> Self:
        if self.keypair_count != 1 or self.private_key_persisted != 0:
            raise ValueError("identity fixture requires one in-memory keypair")
        if self.external_identity_provider_calls != 0:
            raise ValueError("identity fixture must not call external identity providers")
        return self


class V02StagingIdentityFixtureResult(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "identity_fixture_fingerprint"

    schema_version: str = V02_IDENTITY_FIXTURE_SCHEMA_VERSION
    fixture_id: str
    assertion_fingerprint: str
    public_key_fingerprint: str
    signed_assertion_retained: bool = False
    private_key_persisted: int = 0
    verification_passed: bool = True
    production_identity: bool = False
    external_identity_provider_calls: int = 0
    identity_fixture_fingerprint: str | None = None

    @field_validator("assertion_fingerprint", "public_key_fingerprint")
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def identity_result_is_redacted(self) -> Self:
        if self.signed_assertion_retained or self.private_key_persisted:
            raise ValueError("identity fixture may not retain assertion or private key")
        if not self.verification_passed or self.production_identity:
            raise ValueError("identity fixture must verify offline and stay non-production")
        return self


class V02StagingReplayFixturePlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "replay_fixture_plan_fingerprint"

    schema_version: str = V02_REPLAY_FIXTURE_SCHEMA_VERSION
    fixture_id: str
    in_memory_repository: bool = True
    exact_replay_allowed: bool = True
    second_use_rejected: bool = True
    changed_replay_rejected: bool = True
    persistent_files: int = 0
    database_writes: int = 0
    replay_fixture_plan_fingerprint: str | None = None

    @model_validator(mode="after")
    def replay_plan_is_ephemeral(self) -> Self:
        if not (
            self.in_memory_repository
            and self.second_use_rejected
            and self.changed_replay_rejected
        ):
            raise ValueError("replay fixture must be in-memory and reject replay changes")
        if self.persistent_files or self.database_writes:
            raise ValueError("replay fixture must not persist data")
        return self


class V02StagingReplayFixtureResult(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "replay_fixture_fingerprint"

    schema_version: str = V02_REPLAY_FIXTURE_SCHEMA_VERSION
    fixture_id: str
    assertion_fingerprint: str
    first_verification_accepted: bool = True
    second_use_rejected: bool = True
    changed_replay_rejected: bool = True
    persistent_files: int = 0
    database_writes: int = 0
    replay_record_retained: bool = False
    replay_fixture_fingerprint: str | None = None

    @field_validator("assertion_fingerprint")
    @classmethod
    def valid_assertion_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def replay_result_is_ephemeral(self) -> Self:
        if not (
            self.first_verification_accepted
            and self.second_use_rejected
            and self.changed_replay_rejected
        ):
            raise ValueError("replay fixture validation did not pass")
        if self.persistent_files or self.database_writes or self.replay_record_retained:
            raise ValueError("replay fixture result retained prohibited data")
        return self


class V02StagingDeploymentPlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "deployment_plan_fingerprint"

    schema_version: str = V02_DEPLOYMENT_PLAN_SCHEMA_VERSION
    deployment_id: str
    project_name_fingerprint: str
    service_names: tuple[str, ...]
    service_count: int = 5
    internal_network: bool = True
    loopback_host: str = LOOPBACK_HOST
    dependency_host_ports: int = 0
    pull_policy: Literal["never"] = "never"
    no_build: bool = True
    deployment_plan_fingerprint: str | None = None

    @field_validator("project_name_fingerprint")
    @classmethod
    def valid_project_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def deployment_is_exact(self) -> Self:
        if set(self.service_names) != {"brain-api", "postgres", "redis", "nats", "opa"}:
            raise ValueError("staging deployment must contain exactly five services")
        if self.service_count != len(self.service_names):
            raise ValueError("service count mismatch")
        if not self.internal_network or self.loopback_host != LOOPBACK_HOST:
            raise ValueError("deployment must use an internal network and loopback binding")
        if self.dependency_host_ports != 0:
            raise ValueError("dependency services must not publish host ports")
        return self


class V02StagingDeploymentResult(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "deployment_result_fingerprint"

    schema_version: str = V02_DEPLOYMENT_PLAN_SCHEMA_VERSION
    deployment_id: str
    status: V02StagingDeploymentStatus = V02StagingDeploymentStatus.healthy
    service_count: int = 5
    peak_container_count: int
    loopback_listener_created: bool = True
    public_listeners_created: int = 0
    non_loopback_listeners_created: int = 0
    dependency_host_ports: int = 0
    actual_port_retained: bool = False
    deployment_result_fingerprint: str | None = None

    @model_validator(mode="after")
    def deployment_result_is_safe(self) -> Self:
        if self.peak_container_count > 6:
            raise ValueError("peak staging container count exceeded")
        if not self.loopback_listener_created or self.public_listeners_created:
            raise ValueError("deployment did not remain loopback-only")
        if (
            self.non_loopback_listeners_created
            or self.dependency_host_ports
            or self.actual_port_retained
        ):
            raise ValueError("deployment result retained prohibited host exposure")
        return self


class V02StagingHealthCheck(V02StagingFrozenModel):
    check_id: str
    route: str
    status: Literal["ok", "alive", "ready", "degraded"]
    response_fingerprint: str

    @field_validator("response_fingerprint")
    @classmethod
    def valid_response_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)


class V02StagingHealthReadinessReport(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "health_readiness_report_fingerprint"

    schema_version: str = V02_HEALTH_READINESS_SCHEMA_VERSION
    health_checks: tuple[V02StagingHealthCheck, ...]
    readiness_checks: dict[str, Literal["ok", "fail"]]
    health_checks_passed: int
    readiness_checks_passed: int
    all_dependencies_ready: bool
    health_readiness_report_fingerprint: str | None = None

    @model_validator(mode="after")
    def health_is_ready(self) -> Self:
        if self.health_checks_passed < 3 or self.readiness_checks_passed < 2:
            raise ValueError("health and readiness check counts are below AION-241 bounds")
        required = {"postgres", "redis", "nats", "opa"}
        if set(self.readiness_checks) != required:
            raise ValueError("readiness dependency set mismatch")
        if not all(value == "ok" for value in self.readiness_checks.values()):
            raise ValueError("all readiness dependencies must be ok")
        if not self.all_dependencies_ready:
            raise ValueError("health readiness report must be ready")
        return self


class V02StagingSecurityScenario(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "scenario_fingerprint"

    scenario_id: str
    result: V02StagingSecurityResult
    evidence_fingerprint: str
    scenario_fingerprint: str | None = None

    @field_validator("scenario_id")
    @classmethod
    def valid_scenario_id(cls, value: str) -> str:
        return _validate_identifier(value)

    @field_validator("evidence_fingerprint")
    @classmethod
    def valid_evidence_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)


class V02StagingSecurityFinding(V02StagingFrozenModel):
    finding_id: str
    scenario_id: str
    result: V02StagingSecurityResult
    protected_material_redacted: bool = True


class V02StagingSecurityValidationReport(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "security_validation_report_fingerprint"

    schema_version: str = V02_SECURITY_VALIDATION_SCHEMA_VERSION
    scenarios: tuple[V02StagingSecurityScenario, ...]
    findings: tuple[V02StagingSecurityFinding, ...]
    security_tests_passed: int
    identity_spoofing_rejected: bool = True
    replay_rejected: bool = True
    changed_replay_rejected: bool = True
    protected_material_redacted: bool = True
    configuration_drift_detected: bool = True
    read_only_runtime_boundary: bool = True
    no_production_activation: bool = True
    security_validation_report_fingerprint: str | None = None

    @model_validator(mode="after")
    def security_report_passes(self) -> Self:
        if len(self.scenarios) < 8 or self.security_tests_passed < 8:
            raise ValueError("AION-241 requires at least eight security scenarios")
        if not all(
            scenario.result is V02StagingSecurityResult.passed for scenario in self.scenarios
        ):
            raise ValueError("all staging security scenarios must pass")
        if not (
            self.identity_spoofing_rejected
            and self.replay_rejected
            and self.changed_replay_rejected
            and self.protected_material_redacted
            and self.configuration_drift_detected
            and self.read_only_runtime_boundary
            and self.no_production_activation
        ):
            raise ValueError("staging security validation has a failed hard gate")
        return self


class V02StagingObservabilityEvent(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "event_fingerprint"

    event_id: str
    event_kind: str
    count: int
    event_fingerprint: str | None = None

    @field_validator("event_id", "event_kind")
    @classmethod
    def valid_identifier(cls, value: str) -> str:
        return _validate_identifier(value)


class V02StagingLocalLogProjection(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "log_projection_fingerprint"

    raw_logs_retained: bool = False
    protected_material_found: bool = False
    log_line_count: int
    safe_log_fingerprint: str
    log_projection_fingerprint: str | None = None

    @field_validator("safe_log_fingerprint")
    @classmethod
    def valid_safe_log_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def logs_are_redacted(self) -> Self:
        if self.raw_logs_retained or self.protected_material_found:
            raise ValueError("raw logs and protected material must not be retained")
        return self


class V02StagingObservabilitySnapshot(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "observability_snapshot_fingerprint"

    schema_version: str = V02_OBSERVABILITY_SCHEMA_VERSION
    events: tuple[V02StagingObservabilityEvent, ...]
    log_projection: V02StagingLocalLogProjection
    local_observability_records_created: int
    external_log_exports: int = 0
    external_metric_exports: int = 0
    external_trace_exports: int = 0
    observability_snapshot_fingerprint: str | None = None

    @model_validator(mode="after")
    def observability_is_local(self) -> Self:
        if not self.events or self.local_observability_records_created < 1:
            raise ValueError("local observability snapshot requires at least one event")
        if self.external_log_exports or self.external_metric_exports or self.external_trace_exports:
            raise ValueError("external observability export is not allowed")
        return self


class V02StagingDegradationPlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "degradation_plan_fingerprint"

    schema_version: str = V02_ROLLBACK_SCHEMA_VERSION
    target_service: Literal["redis"] = "redis"
    bounded_to_run_owned_project: bool = True
    unrelated_container_count: int = 0
    degradation_plan_fingerprint: str | None = None


class V02StagingRollbackStep(V02StagingFrozenModel):
    step_id: str
    action: Literal["stop_redis", "start_redis", "verify_ready"]
    run_owned_resource_only: bool = True


class V02StagingRollbackPlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "rollback_plan_fingerprint"

    schema_version: str = V02_ROLLBACK_SCHEMA_VERSION
    rollback_id: str
    degradation_target: Literal["redis"] = "redis"
    steps: tuple[V02StagingRollbackStep, ...]
    production_rollback: bool = False
    rollback_plan_fingerprint: str | None = None

    @model_validator(mode="after")
    def rollback_plan_is_local(self) -> Self:
        if self.production_rollback:
            raise ValueError("AION-241 rollback is not a production rollback")
        if tuple(step.action for step in self.steps) != (
            "stop_redis",
            "start_redis",
            "verify_ready",
        ):
            raise ValueError("rollback plan must use the bounded Redis degradation sequence")
        return self


class V02StagingRollbackResult(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "rollback_result_fingerprint"

    schema_version: str = V02_ROLLBACK_SCHEMA_VERSION
    rollback_id: str
    status: V02StagingRollbackStatus = V02StagingRollbackStatus.complete
    degradation_detected: bool = True
    readiness_degraded: bool = True
    rollback_count: int = 1
    post_rollback_health_recovered: bool = True
    source_fingerprint_unchanged: bool = True
    artifact_fingerprint_unchanged: bool = True
    production_effect: bool = False
    rollback_result_fingerprint: str | None = None

    @model_validator(mode="after")
    def rollback_result_is_successful(self) -> Self:
        if self.status is not V02StagingRollbackStatus.complete:
            raise ValueError("rollback result must complete")
        if not (
            self.degradation_detected
            and self.readiness_degraded
            and self.post_rollback_health_recovered
            and self.source_fingerprint_unchanged
            and self.artifact_fingerprint_unchanged
        ):
            raise ValueError("rollback result did not pass AION-241 hard gates")
        if self.rollback_count != 1 or self.production_effect:
            raise ValueError("rollback must occur exactly once with no production effect")
        return self


class V02StagingCleanupStep(V02StagingFrozenModel):
    step_id: str
    target_kind: str
    completed: bool = True


class V02StagingCleanupPlan(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "cleanup_plan_fingerprint"

    schema_version: str = V02_CLEANUP_SCHEMA_VERSION
    cleanup_id: str
    steps: tuple[V02StagingCleanupStep, ...]
    preserves_pre_existing_resources: bool = True
    cleanup_plan_fingerprint: str | None = None

    @model_validator(mode="after")
    def cleanup_plan_is_complete(self) -> Self:
        if len(self.steps) < 8 or not all(step.completed for step in self.steps):
            raise ValueError("cleanup plan must include completed bounded steps")
        if not self.preserves_pre_existing_resources:
            raise ValueError("cleanup plan must preserve pre-existing resources")
        return self


class V02StagingCleanupResult(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "cleanup_result_fingerprint"

    schema_version: str = V02_CLEANUP_SCHEMA_VERSION
    cleanup_id: str
    status: V02StagingCleanupStatus = V02StagingCleanupStatus.complete
    containers_removed: int
    volumes_removed: int
    network_removed: bool
    images_removed: int
    temporary_files_removed: bool
    active_run_owned_containers: int = 0
    active_run_owned_volumes: int = 0
    active_run_owned_networks: int = 0
    active_run_owned_images: int = 0
    temporary_files_retained: int = 0
    pre_existing_resources_changed: int = 0
    cleanup_result_fingerprint: str | None = None

    @model_validator(mode="after")
    def cleanup_result_is_complete(self) -> Self:
        if self.status is not V02StagingCleanupStatus.complete:
            raise ValueError("cleanup result must complete")
        if not self.network_removed or not self.temporary_files_removed:
            raise ValueError("network and temporary files must be removed")
        if any(
            (
                self.active_run_owned_containers,
                self.active_run_owned_volumes,
                self.active_run_owned_networks,
                self.active_run_owned_images,
                self.temporary_files_retained,
                self.pre_existing_resources_changed,
            )
        ):
            raise ValueError("cleanup result has retained or changed resources")
        return self


class V02StagingIntegrityAudit(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "integrity_fingerprint"

    schema_version: str = V02_INTEGRITY_SCHEMA_VERSION
    integrity_status: V02StagingIntegrityStatus
    checked_fingerprints: tuple[str, ...]
    redaction_passed: bool = True
    zero_effects_passed: bool = True
    cleanup_passed: bool = True
    replay_passed: bool = True
    production_effect: bool = False
    release_effect: bool = False
    integrity_fingerprint: str | None = None

    @field_validator("checked_fingerprints")
    @classmethod
    def valid_checked_fingerprints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            _validate_sha256(item)
        return value

    @model_validator(mode="after")
    def integrity_passes(self) -> Self:
        if self.integrity_status is not V02StagingIntegrityStatus.passed:
            raise ValueError("integrity audit must pass")
        if not (
            self.redaction_passed
            and self.zero_effects_passed
            and self.cleanup_passed
            and self.replay_passed
        ):
            raise ValueError("integrity audit failed a hard gate")
        if self.production_effect or self.release_effect:
            raise ValueError("integrity audit must be effect-free")
        return self


class V02StagingEvidenceRecord(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "evidence_fingerprint"

    schema_version: str = V02_EVIDENCE_SCHEMA_VERSION
    evidence_id: str
    evidence_maturity: V02EvidenceMaturity
    evidence_payload_fingerprint: str
    redacted: bool = True
    production_effect: bool = False
    release_effect: bool = False
    evidence_fingerprint: str | None = None

    @field_validator("evidence_payload_fingerprint")
    @classmethod
    def valid_payload_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)


class V02StagingQualificationEvidenceBundle(V02StagingFingerprintedModel):
    fingerprint_field: ClassVar[str] = "report_fingerprint"

    schema_version: str = V02_EVIDENCE_SCHEMA_VERSION
    pilot_id: str = PILOT_ID
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    program_id: str = PROGRAM_ID
    mode: Literal["controlled-local-docker"] = "controlled-local-docker"
    implementation_commit: str
    source_snapshot_commit: str
    source_tree_fingerprint: str
    git_archive_fingerprint: str
    docker_context_fingerprint: str
    docker_server_fingerprint: str
    docker_server_architecture: Literal["arm64", "aarch64"]
    base_image_fingerprint: str
    dependency_image_fingerprints: dict[str, str]
    build_plan_fingerprint: str
    generated_dockerfile_fingerprint: str
    build_context_fingerprint: str
    staging_artifact_fingerprints: tuple[str, ...]
    deployed_staging_image_fingerprint: str
    sbom_fingerprint: str
    sbom_component_count: int
    artifact_provenance_chain_head: str
    artifact_provenance_records_created: int
    reproducibility_comparison_fingerprint: str
    reproducibility_invariants_passed: bool = True
    byte_for_byte_reproducibility_confirmed: bool
    environment_profile_fingerprint: str
    compose_plan_fingerprint: str
    internal_network_fingerprint: str
    ephemeral_port_used: bool = True
    actual_port_retained: bool = False
    identity_fixture_fingerprint: str
    replay_fixture_fingerprint: str
    health_readiness_report_fingerprint: str
    security_validation_report_fingerprint: str
    observability_snapshot_fingerprint: str
    rollback_plan_fingerprint: str
    rollback_result_fingerprint: str
    cleanup_result_fingerprint: str
    pilot_counters: dict[str, int | bool]
    prohibited_effect_counters: dict[str, int] = Field(default_factory=dict)
    integrity_passed: bool = True
    temporary_files_retained: int = 0
    redacted: bool = True
    production_effect: bool = False
    release_effect: bool = False
    v02_release_ready: bool = False
    v02_tag_created: bool = False
    v02_release_created: bool = False
    report_fingerprint: str | None = None

    @field_validator("implementation_commit", "source_snapshot_commit")
    @classmethod
    def valid_commit(cls, value: str) -> str:
        return _validate_git_object(value)

    @field_validator(
        "source_tree_fingerprint",
        "git_archive_fingerprint",
        "docker_context_fingerprint",
        "docker_server_fingerprint",
        "base_image_fingerprint",
        "build_plan_fingerprint",
        "generated_dockerfile_fingerprint",
        "build_context_fingerprint",
        "deployed_staging_image_fingerprint",
        "sbom_fingerprint",
        "artifact_provenance_chain_head",
        "reproducibility_comparison_fingerprint",
        "environment_profile_fingerprint",
        "compose_plan_fingerprint",
        "internal_network_fingerprint",
        "identity_fixture_fingerprint",
        "replay_fixture_fingerprint",
        "health_readiness_report_fingerprint",
        "security_validation_report_fingerprint",
        "observability_snapshot_fingerprint",
        "rollback_plan_fingerprint",
        "rollback_result_fingerprint",
        "cleanup_result_fingerprint",
    )
    @classmethod
    def valid_fingerprint(cls, value: str) -> str:
        return _validate_sha256(value)

    @model_validator(mode="after")
    def evidence_bundle_passes(self) -> Self:
        if (
            self.prohibited_effect_counters
            and self.prohibited_effect_counters != PROHIBITED_EFFECT_COUNTERS
        ):
            raise ValueError("prohibited-effect counters must remain zero")
        if not self.prohibited_effect_counters:
            object.__setattr__(
                self,
                "prohibited_effect_counters",
                dict(PROHIBITED_EFFECT_COUNTERS),
            )
        for key, expected in PILOT_COUNTERS.items():
            if self.pilot_counters.get(key) != expected:
                raise ValueError(f"pilot counter mismatch: {key}")
        required_minimums = {
            "running_staging_containers_peak": 1,
            "loopback_listeners_created": 1,
            "health_checks_passed": 3,
            "readiness_checks_passed": 2,
            "security_tests_passed": 8,
            "replay_rejection_tests_passed": 1,
            "protected_material_redaction_tests_passed": 1,
            "configuration_drift_tests_passed": 1,
            "local_observability_records_created": 1,
            "artifact_provenance_records_created": 2,
        }
        for key, minimum in required_minimums.items():
            value = self.pilot_counters.get(key)
            if not isinstance(value, int) or value < minimum:
                raise ValueError(f"pilot counter below minimum: {key}")
        if self.pilot_counters.get("running_staging_containers_peak", 0) > 6:
            raise ValueError("running staging container peak exceeded")
        if not (
            self.integrity_passed
            and self.reproducibility_invariants_passed
            and self.ephemeral_port_used
            and not self.actual_port_retained
            and self.redacted
            and not self.production_effect
            and not self.release_effect
            and not self.v02_release_ready
            and not self.v02_tag_created
            and not self.v02_release_created
        ):
            raise ValueError("pilot evidence violates staging or release boundary")
        return self


class InMemoryV02StagingQualificationRepository:
    """Copy-on-write repository for one local staging qualification session."""

    def __init__(self) -> None:
        self._sessions: dict[str, V02StagingQualificationSession] = {}
        self._evidence: dict[str, V02StagingQualificationEvidenceBundle] = {}
        self._request_fingerprints: dict[str, str] = {}

    def snapshot_sessions(self) -> tuple[V02StagingQualificationSession, ...]:
        return tuple(deepcopy(self._sessions[key]) for key in sorted(self._sessions))

    def active_session_count(self) -> int:
        return sum(1 for session in self._sessions.values() if session.active)

    def start_session(self, session: V02StagingQualificationSession) -> None:
        if self.active_session_count() >= 1:
            raise ValueError("maximum one active staging qualification session is allowed")
        self._sessions = {**self._sessions, session.session_id: deepcopy(session)}

    def close_session(self, session_id: str) -> V02StagingQualificationSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError("unknown staging qualification session")
        closed = session.close()
        self._sessions = {**self._sessions, session_id: closed}
        return deepcopy(closed)

    def record_evidence(
        self,
        bundle: V02StagingQualificationEvidenceBundle,
        request_fingerprint: str,
    ) -> None:
        self._evidence = {**self._evidence, bundle.pilot_id: deepcopy(bundle)}
        self._request_fingerprints = {
            **self._request_fingerprints,
            bundle.pilot_id: request_fingerprint,
        }

    def replay_exact_qualification(
        self,
        pilot_id: str,
        request_fingerprint: str,
    ) -> V02StagingQualificationEvidenceBundle:
        if self._request_fingerprints.get(pilot_id) != request_fingerprint:
            raise ValueError("changed staging qualification replay rejected")
        return deepcopy(self._evidence[pilot_id])


def resource_limits() -> V02StagingResourceLimits:
    return V02StagingResourceLimits()


def confirmation_fingerprint() -> str:
    return v02_staging_fingerprint(
        {
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "confirmation": LOCAL_CONFIRMATION_TEXT,
            "program_id": PROGRAM_ID,
        }
    )


def canonical_component_binding(
    *,
    current_source_commit: str = AION_240_MERGE_COMMIT,
    current_git_tree_sha: str | None = None,
    source_tree_fingerprint: str | None = None,
    docker_context_fingerprint: str | None = None,
    docker_server_fingerprint: str | None = None,
    base_image_tag: str = "aoinos-brain-api:aion241-base-9f6b899f84ef",
    base_image_id: str = "sha256:d55ed37f90d85ca0fc5973e6d3cdd849353e0549a7df95d39864506712b342ea",
    dependency_image_fingerprints: Mapping[str, str] | None = None,
) -> V02StagingQualificationComponentBinding:
    source_fp = source_tree_fingerprint or v02_staging_fingerprint("source-tree")
    docker_context_fp = docker_context_fingerprint or v02_staging_fingerprint("docker-context")
    docker_server_fp = docker_server_fingerprint or v02_staging_fingerprint("docker-server")
    dependencies = dict(
        dependency_image_fingerprints
        or {image: v02_staging_fingerprint(image) for image in REQUIRED_DEPENDENCY_IMAGES}
    )
    return V02StagingQualificationComponentBinding(
        current_source_commit=current_source_commit,
        current_git_tree_sha=current_git_tree_sha or v02_staging_fingerprint("git-tree"),
        source_tree_fingerprint=source_fp,
        docker_context_fingerprint=docker_context_fp,
        docker_server_fingerprint=docker_server_fp,
        base_image_tag=base_image_tag,
        base_image_id=base_image_id,
        base_image_fingerprint=v02_staging_fingerprint(base_image_id),
        dependency_image_fingerprints=dependencies,
        resource_limit_fingerprint=resource_limits().resource_limit_fingerprint or "",
        operator_confirmation_fingerprint=confirmation_fingerprint(),
    )


def canonical_authorization_envelope(
    component_binding: V02StagingQualificationComponentBinding,
    session_id: str = "aion-241-controlled-staging-session",
) -> V02StagingQualificationAuthorizationEnvelope:
    return V02StagingQualificationAuthorizationEnvelope(
        qualification_session_id=session_id,
        component_binding_fingerprint=component_binding.component_binding_fingerprint or "",
        resource_limit_fingerprint=resource_limits().resource_limit_fingerprint or "",
        operator_confirmation_fingerprint=confirmation_fingerprint(),
        approved_capabilities=dict.fromkeys(APPROVED_CAPABILITIES, True),
        prohibited_capabilities=dict.fromkeys(PROHIBITED_CAPABILITIES, False),
    )


def canonical_session_plan(
    session_id: str = "aion-241-controlled-staging-session",
    *,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> V02StagingQualificationSessionPlan:
    created = created_at or utc_now()
    return V02StagingQualificationSessionPlan(
        session_id=session_id,
        created_at=created,
        expires_at=expires_at or created + timedelta(hours=3),
        local_confirmation_text_fingerprint=confirmation_fingerprint(),
    )


def canonical_docker_context_projection() -> V02StagingDockerContextProjection:
    return V02StagingDockerContextProjection(
        context_name="desktop-linux",
        endpoint_kind="local_unix_socket",
        server_architecture="arm64",
    )


def canonical_local_image_inventory(
    *,
    base_image_tag: str = "aoinos-brain-api:aion241-base-9f6b899f84ef",
    base_image_id: str = "sha256:d55ed37f90d85ca0fc5973e6d3cdd849353e0549a7df95d39864506712b342ea",
) -> V02StagingLocalImageInventory:
    dependency_images = {
        image: V02StagingLocalImageRecord(
            image_tag=image,
            image_id=f"sha256:{v02_staging_fingerprint(image)}",
        )
        for image in REQUIRED_DEPENDENCY_IMAGES
    }
    return V02StagingLocalImageInventory(
        base_image=V02StagingLocalImageRecord(
            image_tag=base_image_tag,
            image_id=base_image_id,
            source_revision=AION_240_MERGE_COMMIT,
        ),
        dependency_images=dependency_images,
    )


def canonical_source_snapshot_manifest(
    source_commit: str = AION_240_MERGE_COMMIT,
) -> V02StagingSourceSnapshotManifest:
    records = (
        V02StagingSourceFileRecord(
            relative_path=path,
            byte_count=len(path.encode("utf-8")),
            sha256=v02_staging_fingerprint(path),
        )
        for path in REQUIRED_SOURCE_SCOPE
    )
    file_records = tuple(records)
    return V02StagingSourceSnapshotManifest(
        source_commit=source_commit,
        git_tree_sha=v02_staging_fingerprint("git-tree"),
        git_archive_fingerprint=v02_staging_fingerprint("git-archive"),
        extracted_file_count=len(file_records),
        total_byte_count=sum(record.byte_count for record in file_records),
        file_manifest_fingerprint=v02_staging_fingerprint([r.model_dump() for r in file_records]),
        file_records=file_records,
    )


def canonical_build_plan(
    snapshot: V02StagingSourceSnapshotManifest,
    inventory: V02StagingLocalImageInventory,
) -> V02StagingBuildPlan:
    return V02StagingBuildPlan(
        build_plan_id="AION-241-offline-local-build-plan",
        source_commit=snapshot.source_commit,
        source_tree_fingerprint=snapshot.source_tree_fingerprint or "",
        base_image_tag=inventory.base_image.image_tag,
        base_image_id=inventory.base_image.image_id,
        generated_dockerfile_fingerprint=v02_staging_fingerprint("generated-Dockerfile"),
        build_context_fingerprint=v02_staging_fingerprint("build-context"),
    )


def canonical_artifact_manifest(
    snapshot: V02StagingSourceSnapshotManifest,
    inventory: V02StagingLocalImageInventory,
) -> V02StagingArtifactManifest:
    staging_image_id = f"sha256:{v02_staging_fingerprint('staging-image')}"
    component = V02StagingArtifactComponent(
        component_name="brain-api",
        component_kind="local-staging-image",
        image_id=staging_image_id,
        source_fingerprint=snapshot.source_tree_fingerprint or "",
    )
    return V02StagingArtifactManifest(
        manifest_id="AION-241-staging-artifact-manifest",
        source_commit=snapshot.source_commit,
        source_tree_fingerprint=snapshot.source_tree_fingerprint or "",
        base_image_id=inventory.base_image.image_id,
        staging_image_id=staging_image_id,
        components=(component,),
    )


def canonical_sbom(
    snapshot: V02StagingSourceSnapshotManifest,
    inventory: V02StagingLocalImageInventory,
) -> V02StagingSoftwareBillOfMaterials:
    names = ("aion-brain-api", "fastapi", "pydantic", "sqlalchemy", "cryptography")
    components = tuple(
        V02StagingSbomComponent(
            name=name,
            normalized_name=name.replace("_", "-").lower(),
            version="0.0.0",
        )
        for name in names
    )
    return V02StagingSoftwareBillOfMaterials(
        source_tree_fingerprint=snapshot.source_tree_fingerprint or "",
        base_image_fingerprint=inventory.base_image.image_fingerprint or "",
        component_count=len(components),
        components=components,
    )


def canonical_provenance(
    snapshot: V02StagingSourceSnapshotManifest,
    inventory: V02StagingLocalImageInventory,
    sbom: V02StagingSoftwareBillOfMaterials,
) -> V02StagingArtifactProvenanceRecord:
    return V02StagingArtifactProvenanceRecord(
        provenance_id="AION-241-staging-provenance",
        source_commit=snapshot.source_commit,
        source_tree_fingerprint=snapshot.source_tree_fingerprint or "",
        git_archive_fingerprint=snapshot.git_archive_fingerprint,
        base_image_id=inventory.base_image.image_id,
        dependency_image_fingerprints={
            key: value.image_fingerprint or "" for key, value in inventory.dependency_images.items()
        },
        generated_dockerfile_fingerprint=v02_staging_fingerprint("generated-Dockerfile"),
        build_context_fingerprint=v02_staging_fingerprint("build-context"),
        staging_image_id=f"sha256:{v02_staging_fingerprint('staging-image')}",
        normalized_image_config_fingerprint=v02_staging_fingerprint("image-config"),
        rootfs_layer_fingerprints=(v02_staging_fingerprint("rootfs-layer"),),
        sbom_fingerprint=sbom.sbom_fingerprint or "",
    )


def canonical_reproducibility_comparison(
    snapshot: V02StagingSourceSnapshotManifest,
    inventory: V02StagingLocalImageInventory,
) -> V02StagingReproducibilityComparison:
    checks = {
        "source_commit": True,
        "source_tree_fingerprint": True,
        "base_image_id": True,
        "generated_dockerfile_fingerprint": True,
        "build_context_fingerprint": True,
        "normalized_image_configuration": True,
        "rootfs_layers": True,
        "application_source_manifest": True,
        "runtime_command": True,
        "environment_projection": True,
        "sbom_fingerprint": True,
    }
    return V02StagingReproducibilityComparison(
        source_commit=snapshot.source_commit,
        source_tree_fingerprint=snapshot.source_tree_fingerprint or "",
        base_image_id=inventory.base_image.image_id,
        generated_dockerfile_fingerprint=v02_staging_fingerprint("generated-Dockerfile"),
        build_context_fingerprint=v02_staging_fingerprint("build-context"),
        first_image_id=f"sha256:{v02_staging_fingerprint('staging-image-one')}",
        second_image_id=f"sha256:{v02_staging_fingerprint('staging-image-two')}",
        invariant_checks=checks,
        reproducibility_invariants_passed=True,
        byte_for_byte_reproducibility_confirmed=False,
    )


def canonical_environment_profile() -> V02StagingEnvironmentProfile:
    return V02StagingEnvironmentProfile(
        profile_id="AION-241-isolated-local-staging",
        project_name_fingerprint=v02_staging_fingerprint("aion241-project"),
    )


def canonical_identity_fixture_result() -> V02StagingIdentityFixtureResult:
    assertion = v02_staging_fingerprint("identity-assertion")
    return V02StagingIdentityFixtureResult(
        fixture_id="AION-241-identity-fixture",
        assertion_fingerprint=assertion,
        public_key_fingerprint=v02_staging_fingerprint("identity-public-key"),
    )


def canonical_replay_fixture_result(
    assertion_fingerprint: str | None = None,
) -> V02StagingReplayFixtureResult:
    return V02StagingReplayFixtureResult(
        fixture_id="AION-241-replay-fixture",
        assertion_fingerprint=(
            assertion_fingerprint or v02_staging_fingerprint("identity-assertion")
        ),
    )


def canonical_deployment_plan() -> V02StagingDeploymentPlan:
    return V02StagingDeploymentPlan(
        deployment_id="AION-241-local-staging-deployment",
        project_name_fingerprint=v02_staging_fingerprint("aion241-project"),
        service_names=("brain-api", "postgres", "redis", "nats", "opa"),
    )


def canonical_health_readiness_report() -> V02StagingHealthReadinessReport:
    health_inputs: tuple[
        tuple[str, Literal["ok", "alive", "ready", "degraded"]],
        ...,
    ] = (("/health", "ok"), ("/health/live", "alive"), ("/health/ready", "ready"))
    health_checks = tuple(
        V02StagingHealthCheck(
            check_id=f"AION-241-HEALTH-{index}",
            route=route,
            status=status,
            response_fingerprint=v02_staging_fingerprint(route),
        )
        for index, (route, status) in enumerate(
            health_inputs,
            start=1,
        )
    )
    return V02StagingHealthReadinessReport(
        health_checks=health_checks,
        readiness_checks={"postgres": "ok", "redis": "ok", "nats": "ok", "opa": "ok"},
        health_checks_passed=3,
        readiness_checks_passed=4,
        all_dependencies_ready=True,
    )


def canonical_security_validation_report() -> V02StagingSecurityValidationReport:
    scenario_ids = (
        "loopback_binding_only",
        "internal_network_only",
        "no_dependency_host_ports",
        "no_registry_activity",
        "dev_header_identity_spoofing_rejected",
        "offline_signed_identity_verified",
        "replay_rejected",
        "changed_replay_rejected",
        "protected_material_redacted",
        "staging_configuration_drift_detected",
        "read_only_runtime_boundary",
        "no_production_activation",
    )
    scenarios = tuple(
        V02StagingSecurityScenario(
            scenario_id=scenario_id,
            result=V02StagingSecurityResult.passed,
            evidence_fingerprint=v02_staging_fingerprint(scenario_id),
        )
        for scenario_id in scenario_ids
    )
    findings = tuple(
        V02StagingSecurityFinding(
            finding_id=f"AION-241-FINDING-{index:03d}",
            scenario_id=scenario.scenario_id,
            result=scenario.result,
        )
        for index, scenario in enumerate(scenarios, start=1)
    )
    return V02StagingSecurityValidationReport(
        scenarios=scenarios,
        findings=findings,
        security_tests_passed=len(scenarios),
    )


def canonical_observability_snapshot() -> V02StagingObservabilitySnapshot:
    events = tuple(
        V02StagingObservabilityEvent(
            event_id=f"AION-241-OBS-{index:03d}",
            event_kind=kind,
            count=count,
        )
        for index, (kind, count) in enumerate(
            (
                ("health-check-count", 3),
                ("readiness-transition-count", 3),
                ("security-finding-count", 12),
                ("rollback-duration-count", 1),
            ),
            start=1,
        )
    )
    return V02StagingObservabilitySnapshot(
        events=events,
        log_projection=V02StagingLocalLogProjection(
            log_line_count=0,
            safe_log_fingerprint=v02_staging_fingerprint("safe-log-projection"),
        ),
        local_observability_records_created=len(events),
    )


def canonical_rollback_plan() -> V02StagingRollbackPlan:
    return V02StagingRollbackPlan(
        rollback_id="AION-241-staging-rollback",
        steps=(
            V02StagingRollbackStep(step_id="AION-241-RB-001", action="stop_redis"),
            V02StagingRollbackStep(step_id="AION-241-RB-002", action="start_redis"),
            V02StagingRollbackStep(step_id="AION-241-RB-003", action="verify_ready"),
        ),
    )


def canonical_cleanup_result() -> V02StagingCleanupResult:
    return V02StagingCleanupResult(
        cleanup_id="AION-241-staging-cleanup",
        containers_removed=5,
        volumes_removed=0,
        network_removed=True,
        images_removed=2,
        temporary_files_removed=True,
    )


def canonical_integrity_audit(
    bundle: V02StagingQualificationEvidenceBundle,
) -> V02StagingIntegrityAudit:
    return V02StagingIntegrityAudit(
        integrity_status=V02StagingIntegrityStatus.passed,
        checked_fingerprints=(bundle.report_fingerprint or "",),
    )


def canonical_evidence_bundle(
    implementation_commit: str = AION_240_MERGE_COMMIT,
    *,
    byte_for_byte_reproducibility_confirmed: bool = False,
) -> V02StagingQualificationEvidenceBundle:
    snapshot = canonical_source_snapshot_manifest(implementation_commit)
    inventory = canonical_local_image_inventory()
    build_plan = canonical_build_plan(snapshot, inventory)
    artifact = canonical_artifact_manifest(snapshot, inventory)
    sbom = canonical_sbom(snapshot, inventory)
    provenance = canonical_provenance(snapshot, inventory, sbom)
    comparison = canonical_reproducibility_comparison(snapshot, inventory)
    environment = canonical_environment_profile()
    deployment_plan = canonical_deployment_plan()
    identity = canonical_identity_fixture_result()
    replay = canonical_replay_fixture_result(identity.assertion_fingerprint)
    health = canonical_health_readiness_report()
    security = canonical_security_validation_report()
    observability = canonical_observability_snapshot()
    rollback = canonical_rollback_plan()
    rollback_result = V02StagingRollbackResult(rollback_id=rollback.rollback_id)
    cleanup = canonical_cleanup_result()
    counters = {
        **PILOT_COUNTERS,
        "running_staging_containers_peak": 5,
        "loopback_listeners_created": 1,
        "health_checks_passed": 3,
        "readiness_checks_passed": 4,
        "security_tests_passed": security.security_tests_passed,
        "replay_rejection_tests_passed": 1,
        "protected_material_redaction_tests_passed": 1,
        "configuration_drift_tests_passed": 1,
        "local_observability_records_created": observability.local_observability_records_created,
        "artifact_provenance_records_created": 2,
    }
    return V02StagingQualificationEvidenceBundle(
        implementation_commit=implementation_commit,
        source_snapshot_commit=implementation_commit,
        source_tree_fingerprint=snapshot.source_tree_fingerprint or "",
        git_archive_fingerprint=snapshot.git_archive_fingerprint,
        docker_context_fingerprint=canonical_docker_context_projection().docker_context_fingerprint
        or "",
        docker_server_fingerprint=v02_staging_fingerprint("docker-server"),
        docker_server_architecture="arm64",
        base_image_fingerprint=inventory.base_image.image_fingerprint or "",
        dependency_image_fingerprints={
            key: value.image_fingerprint or "" for key, value in inventory.dependency_images.items()
        },
        build_plan_fingerprint=build_plan.build_plan_fingerprint or "",
        generated_dockerfile_fingerprint=build_plan.generated_dockerfile_fingerprint,
        build_context_fingerprint=build_plan.build_context_fingerprint,
        staging_artifact_fingerprints=(artifact.artifact_manifest_fingerprint or "",),
        deployed_staging_image_fingerprint=artifact.artifact_manifest_fingerprint or "",
        sbom_fingerprint=sbom.sbom_fingerprint or "",
        sbom_component_count=sbom.component_count,
        artifact_provenance_chain_head=provenance.provenance_fingerprint or "",
        artifact_provenance_records_created=2,
        reproducibility_comparison_fingerprint=comparison.comparison_fingerprint or "",
        byte_for_byte_reproducibility_confirmed=byte_for_byte_reproducibility_confirmed,
        environment_profile_fingerprint=environment.environment_profile_fingerprint or "",
        compose_plan_fingerprint=deployment_plan.deployment_plan_fingerprint or "",
        internal_network_fingerprint=v02_staging_fingerprint("internal-network"),
        identity_fixture_fingerprint=identity.identity_fixture_fingerprint or "",
        replay_fixture_fingerprint=replay.replay_fixture_fingerprint or "",
        health_readiness_report_fingerprint=health.health_readiness_report_fingerprint or "",
        security_validation_report_fingerprint=security.security_validation_report_fingerprint
        or "",
        observability_snapshot_fingerprint=observability.observability_snapshot_fingerprint or "",
        rollback_plan_fingerprint=rollback.rollback_plan_fingerprint or "",
        rollback_result_fingerprint=rollback_result.rollback_result_fingerprint or "",
        cleanup_result_fingerprint=cleanup.cleanup_result_fingerprint or "",
        pilot_counters=counters,
    )


__all__ = [
    name
    for name in globals()
    if name.isupper()
    or name.startswith(("V02", "InMemoryV02", "canonical_", "v02_", "resource_limits"))
    or name
    in {
        "AUTHORIZATION_SCOPE",
        "AUTHORIZATION_TRANSACTION_ID",
        "CANDIDATE_ID",
        "FORMAL_CLOSEOUT_TASK",
        "IMPLEMENTATION_TASK",
        "LOCAL_CONFIRMATION_TEXT",
        "LOOPBACK_HOST",
        "PILOT_ID",
        "PROGRAM_ID",
        "PROGRAM_NAME",
        "PROHIBITED_EFFECT_COUNTERS",
        "WORKSTREAM",
        "ZERO_FINGERPRINT",
        "canonical_json",
        "confirmation_fingerprint",
        "utc_now",
    }
]
