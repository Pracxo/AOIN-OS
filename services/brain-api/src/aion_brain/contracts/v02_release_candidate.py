"""Deterministic local v0.2 release-candidate artifact build contracts."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

V02_RELEASE_CANDIDATE_CONTRACT_SCHEMA_VERSION: Final = "aion-v02-release-candidate/v1"
V02_RELEASE_CANDIDATE_AUTHORIZATION_SCHEMA_VERSION: Final = (
    "aion-v02-release-candidate-authorization/v1"
)
V02_RELEASE_CANDIDATE_COMPONENT_BINDING_SCHEMA_VERSION: Final = (
    "aion-v02-release-candidate-component-binding/v1"
)
V02_RELEASE_CANDIDATE_SESSION_SCHEMA_VERSION: Final = "aion-v02-release-candidate-session/v1"
V02_CANDIDATE_SOURCE_SNAPSHOT_SCHEMA_VERSION: Final = "aion-v02-candidate-source-snapshot/v1"
V02_CANDIDATE_VERSION_SCHEMA_VERSION: Final = "aion-v02-candidate-version/v1"
V02_CANDIDATE_ARTIFACT_PLAN_SCHEMA_VERSION: Final = "aion-v02-candidate-artifact-plan/v1"
V02_CANDIDATE_ARTIFACT_MANIFEST_SCHEMA_VERSION: Final = (
    "aion-v02-candidate-artifact-manifest/v1"
)
V02_CANDIDATE_SBOM_SCHEMA_VERSION: Final = "aion-v02-candidate-sbom/v1"
V02_CANDIDATE_PROVENANCE_SCHEMA_VERSION: Final = "aion-v02-candidate-provenance/v1"
V02_CANDIDATE_CHECKSUM_SCHEMA_VERSION: Final = "aion-v02-candidate-checksum/v1"
V02_CANDIDATE_SIGNATURE_SCHEMA_VERSION: Final = "aion-v02-candidate-signature/v1"
V02_CANDIDATE_REPRODUCIBILITY_SCHEMA_VERSION: Final = (
    "aion-v02-candidate-reproducibility/v1"
)
V02_CANDIDATE_COMPATIBILITY_SCHEMA_VERSION: Final = "aion-v02-candidate-compatibility/v1"
V02_CANDIDATE_MIGRATION_SCHEMA_VERSION: Final = "aion-v02-candidate-migration/v1"
V02_CANDIDATE_RETENTION_SCHEMA_VERSION: Final = "aion-v02-candidate-retention/v1"
V02_CANDIDATE_INTEGRITY_SCHEMA_VERSION: Final = "aion-v02-candidate-integrity/v1"
V02_CANDIDATE_EVIDENCE_SCHEMA_VERSION: Final = "aion-v02-candidate-evidence/v1"

PROGRAM_ID: Final = "AION-V02-RELEASE-QUALIFICATION-001"
AUTHORIZATION_TRANSACTION_ID: Final = "AION-242-V02RQ-0003"
APPROVAL_RECORD_ID: Final = "AION-242-V02RQ-0003"
IMPLEMENTATION_TASK: Final = "AION-243"
FORMAL_CLOSEOUT_TASK: Final = "AION-244"
FINAL_PLANNED_TASK: Final = "AION-244"
CANDIDATE_LABEL: Final = "aion-v0.2.0-rc.1"
PYTHON_PACKAGE_VERSION: Final = "0.2.0rc1"
LOCAL_CONFIRMATION_TEXT: Final = "BUILD_DETERMINISTIC_LOCAL_V02_RELEASE_CANDIDATE"
ZERO_FINGERPRINT: Final = "0000000000000000000000000000000000000000000000000000000000000000"
LOCAL_IMAGE_TAG: Final = "aoinos-brain-api:aion-v0.2.0-rc.1"
COMPARISON_IMAGE_TAG: Final = "aoinos-brain-api:aion-v0.2.0-rc.1-compare"
FROZEN_BASE_IMAGE_TAG: Final = "aoinos-brain-api:aion241-base-9f6b899f84ef"
FROZEN_BASE_IMAGE_ID: Final = (
    "sha256:d55ed37f90d85ca0fc5973e6d3cdd849353e0549a7df95d39864506712b342ea"
)
AUTHORIZED_SOURCE_COMMIT_PLACEHOLDER = ZERO_FINGERPRINT[:40]

APPROVED_CAPABILITIES: tuple[str, ...] = (
    "deterministic_source_archive_approved",
    "brain_api_oci_archive_approved",
    "brain_api_artifact_manifest_approved",
    "sdk_wheel_approved",
    "sdk_sdist_approved",
    "operator_console_bundle_approved",
    "candidate_version_manifest_approved",
    "candidate_content_manifest_approved",
    "candidate_bundle_manifest_approved",
    "candidate_sbom_approved",
    "artifact_provenance_approved",
    "sha256_checksum_manifest_approved",
    "qualification_detached_signatures_approved",
    "qualification_public_key_record_approved",
    "reproducibility_comparison_approved",
    "compatibility_matrix_approved",
    "migration_manifest_approved",
    "release_notes_draft_approved",
    "candidate_integrity_report_approved",
    "candidate_evidence_bundle_approved",
    "one_local_candidate_bundle_retention_approved",
    "one_local_candidate_image_retention_approved",
    "offline_uninstalled_runner_approved",
)

PROHIBITED_CAPABILITIES: tuple[str, ...] = (
    "registry_login_enabled",
    "registry_pull_enabled",
    "registry_push_enabled",
    "public_network_enabled",
    "dns_resolution_enabled",
    "public_package_upload_enabled",
    "production_credentials_enabled",
    "production_tokens_enabled",
    "production_deployment_enabled",
    "production_runtime_authorized",
    "git_tag_creation_enabled",
    "github_release_creation_enabled",
    "release_candidate_publication_enabled",
    "release_candidate_promotion_enabled",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
)

POSITIVE_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_release_candidate_sessions": 1,
    "maximum_candidate_source_snapshots": 2,
    "maximum_candidate_builds": 2,
    "maximum_candidate_source_archives": 2,
    "maximum_candidate_oci_images": 2,
    "maximum_sdk_wheels": 2,
    "maximum_sdk_sdists": 2,
    "maximum_operator_console_bundles": 2,
    "maximum_retained_candidate_bundles": 1,
    "maximum_retained_candidate_images": 1,
    "maximum_sbom_components": 20000,
    "maximum_provenance_records": 10000,
    "maximum_checksum_records": 20000,
    "maximum_qualification_signatures": 20,
    "maximum_compatibility_records": 1000,
    "maximum_migration_records": 1000,
    "maximum_release_note_records": 1000,
    "maximum_evidence_records": 30000,
    "maximum_evidence_bytes": 209715200,
    "maximum_candidate_bundle_bytes": 5368709120,
    "maximum_temporary_root_bytes": 10737418240,
    "maximum_allowlisted_docker_invocations": 150,
    "maximum_concurrent_build_processes": 2,
}

ZERO_RESOURCE_LIMITS: tuple[str, ...] = (
    "maximum_registry_logins",
    "maximum_registry_pulls",
    "maximum_registry_pushes",
    "maximum_public_network_calls",
    "maximum_dns_resolutions",
    "maximum_external_identity_provider_calls",
    "maximum_production_credentials_used",
    "maximum_production_tokens_used",
    "maximum_production_database_operations",
    "maximum_production_deployments",
    "maximum_public_package_uploads",
    "maximum_git_tags_created",
    "maximum_github_releases_created",
    "maximum_v02_releases_created",
)

REQUIRED_SOURCE_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/v02_release_candidate.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/__init__.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/authorization.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/component_binding.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/source_snapshot.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/version_manifest.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/artifact_plan.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/artifact_manifest.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/sbom.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/provenance.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/checksums.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/signature.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/reproducibility.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/compatibility.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/retention.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/integrity.py",
    "services/brain-api/src/aion_brain/v02_release_candidate/evidence.py",
    "scripts/v02-release-candidate-local-run.py",
)

SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:/-]{1,240}$")
LOWER_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
IMAGE_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_PROTECTED_MARKERS = (
    "-----begin",
    "authorization header",
    "bearer ",
    "client_secret",
    "password=",
    "api_key",
    "apikey",
    "private_key",
    "private key",
    "connection string",
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
    "password",
    "private_key",
    "secret",
    "token",
}


def resource_limits() -> dict[str, int]:
    """Return the exact AION-243 authorization resource limits."""

    return {**POSITIVE_RESOURCE_LIMITS, **dict.fromkeys(ZERO_RESOURCE_LIMITS, 0)}


def approved_capabilities() -> dict[str, bool]:
    return dict.fromkeys(APPROVED_CAPABILITIES, True)


def prohibited_capabilities() -> dict[str, bool]:
    return dict.fromkeys(PROHIBITED_CAPABILITIES, False)


def v02_release_candidate_fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json", exclude_none=True)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _reject_protected_payload(value: Any, *, key: str = "") -> None:
    if isinstance(value, Mapping):
        for item_key, item_value in value.items():
            lowered_key = str(item_key).lower()
            if lowered_key in _PROHIBITED_KEYS:
                raise ValueError(f"protected evidence key is prohibited: {item_key}")
            _reject_protected_payload(item_value, key=lowered_key)
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for item in value:
            _reject_protected_payload(item, key=key)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _PROTECTED_MARKERS):
            raise ValueError(f"protected evidence value is prohibited: {key}")


def _validate_relative_path(value: str) -> str:
    if value.startswith("/") or value.startswith("~"):
        raise ValueError("candidate evidence paths must be relative")
    if ".." in value.split("/"):
        raise ValueError("candidate evidence paths must not traverse parents")
    return value


class V02CandidateBaseModel(BaseModel):
    """Strict immutable base model for committed candidate evidence."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

    @field_validator("*", mode="before")
    @classmethod
    def strings_must_be_bounded(cls, value: Any) -> Any:
        if isinstance(value, str) and len(value) > 4096:
            raise ValueError("candidate contract strings are bounded")
        return value

    @model_validator(mode="after")
    def payload_must_be_safe(self) -> Self:
        for name, value in self.__dict__.items():
            if isinstance(value, datetime):
                if value.tzinfo is None or value.utcoffset() is None:
                    raise ValueError(f"{name} must be timezone-aware")
                if value.utcoffset() != timedelta(0):
                    raise ValueError(f"{name} must be UTC")
            if isinstance(value, str):
                if "fingerprint" in name or name.endswith("_sha256"):
                    if not LOWER_SHA256_PATTERN.fullmatch(value):
                        raise ValueError(f"{name} must be a lowercase SHA-256 fingerprint")
                if name.endswith("_commit") and not GIT_OBJECT_PATTERN.fullmatch(value):
                    raise ValueError(f"{name} must be a Git object ID")
                if name.endswith("_image_id") and not IMAGE_ID_PATTERN.fullmatch(value):
                    raise ValueError(f"{name} must be a Docker image ID")
                if name.endswith("_path") or name == "relative_path":
                    _validate_relative_path(value)
        _reject_protected_payload(self.model_dump(mode="json", exclude_none=True))
        return self


class V02ReleaseCandidateAuthorizationEnvelope(V02CandidateBaseModel):
    schema_version: Literal[
        "aion-v02-release-candidate-authorization/v1"
    ] = V02_RELEASE_CANDIDATE_AUTHORIZATION_SCHEMA_VERSION
    program_id: Literal["AION-V02-RELEASE-QUALIFICATION-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-242-V02RQ-0003"] = (
        AUTHORIZATION_TRANSACTION_ID
    )
    approval_record_id: Literal["AION-242-V02RQ-0003"] = APPROVAL_RECORD_ID
    implementation_task: Literal["AION-243"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-244"] = FORMAL_CLOSEOUT_TASK
    final_planned_task: Literal["AION-244"] = FINAL_PLANNED_TASK
    candidate_label: Literal["aion-v0.2.0-rc.1"] = CANDIDATE_LABEL
    python_package_version: Literal["0.2.0rc1"] = PYTHON_PACKAGE_VERSION
    authorization_active: bool = True
    authorization_consumed: bool = False
    authorization_expired: bool = False
    authorization_reusable: bool = False
    approved_capabilities: dict[str, bool] = Field(default_factory=approved_capabilities)
    prohibited_capabilities: dict[str, bool] = Field(default_factory=prohibited_capabilities)
    resource_limits: dict[str, int] = Field(default_factory=resource_limits)

    @model_validator(mode="after")
    def authorization_must_match_aion_242(self) -> Self:
        if self.approved_capabilities != approved_capabilities():
            raise ValueError("approved capabilities must match AION-242 authorization")
        if self.prohibited_capabilities != prohibited_capabilities():
            raise ValueError("prohibited capabilities must match AION-242 authorization")
        if self.resource_limits != resource_limits():
            raise ValueError("resource limits must match AION-242 authorization")
        return self


class V02ReleaseCandidateComponentBinding(V02CandidateBaseModel):
    schema_version: Literal[
        "aion-v02-release-candidate-component-binding/v1"
    ] = V02_RELEASE_CANDIDATE_COMPONENT_BINDING_SCHEMA_VERSION
    candidate_label: str = CANDIDATE_LABEL
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    component_id: str
    source_path: str
    source_commit: str
    component_fingerprint: str = ZERO_FINGERPRINT
    production_effect: bool = False
    publication_effect: bool = False


class V02ReleaseCandidateSessionPlan(V02CandidateBaseModel):
    schema_version: Literal[
        "aion-v02-release-candidate-session/v1"
    ] = V02_RELEASE_CANDIDATE_SESSION_SCHEMA_VERSION
    session_id: str
    candidate_label: str = CANDIDATE_LABEL
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    created_at: datetime
    expires_at: datetime
    session_plan_fingerprint: str = ZERO_FINGERPRINT


class V02ReleaseCandidateSession(V02CandidateBaseModel):
    schema_version: Literal[
        "aion-v02-release-candidate-session/v1"
    ] = V02_RELEASE_CANDIDATE_SESSION_SCHEMA_VERSION
    session_id: str
    candidate_label: str = CANDIDATE_LABEL
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None
    session_plan_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateSourceSnapshotPlan(V02CandidateBaseModel):
    schema_version: Literal[
        "aion-v02-candidate-source-snapshot/v1"
    ] = V02_CANDIDATE_SOURCE_SNAPSHOT_SCHEMA_VERSION
    candidate_label: str = CANDIDATE_LABEL
    source_commit: str
    read_only_git_archive: bool = True
    source_mutation_allowed: bool = False
    maximum_source_archives: int = 2


class V02CandidateSourceSnapshotManifest(V02CandidateBaseModel):
    schema_version: Literal[
        "aion-v02-candidate-source-snapshot/v1"
    ] = V02_CANDIDATE_SOURCE_SNAPSHOT_SCHEMA_VERSION
    candidate_label: str = CANDIDATE_LABEL
    source_commit: str
    git_tree_sha: str
    source_tree_fingerprint: str
    source_archive_path: str
    source_archive_fingerprint: str
    source_archive_bytes: int = Field(ge=1)
    source_archive_file_count: int = Field(ge=1)
    source_date_epoch: int = Field(ge=0)
    deterministic_archive: bool = True


class V02CandidateVersionManifest(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-version/v1"] = (
        V02_CANDIDATE_VERSION_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    brain_api_package_version: Literal["0.2.0rc1"] = PYTHON_PACKAGE_VERSION
    sdk_package_version: Literal["0.2.0rc1"] = PYTHON_PACKAGE_VERSION
    dependency_changes: int = 0
    migration_changes: int = 0
    git_tag_created: bool = False
    github_release_created: bool = False
    version_manifest_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateArtifactPlan(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-artifact-plan/v1"] = (
        V02_CANDIDATE_ARTIFACT_PLAN_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    source_commit: str
    artifact_kinds: tuple[str, ...]
    network_mode: Literal["none"] = "none"
    pull_policy: Literal["false"] = "false"
    registry_login: bool = False
    registry_pull: bool = False
    registry_push: bool = False
    package_upload: bool = False


class V02CandidateArtifactRecord(V02CandidateBaseModel):
    artifact_id: str
    artifact_kind: str
    relative_path: str
    byte_count: int = Field(ge=0)
    sha256: str
    required: bool = True
    source_commit: str


class V02CandidateArtifactManifest(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-artifact-manifest/v1"] = (
        V02_CANDIDATE_ARTIFACT_MANIFEST_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    source_commit: str
    artifacts: tuple[V02CandidateArtifactRecord, ...]
    production: bool = False
    publication: bool = False
    manifest_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateSbomComponent(V02CandidateBaseModel):
    component_id: str
    name: str
    version: str
    component_type: str
    supplier: str = "local"
    license_declared: str = "NOASSERTION"
    component_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateSbomDocument(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-sbom/v1"] = (
        V02_CANDIDATE_SBOM_SCHEMA_VERSION
    )
    sbom_kind: Literal["local_v02_release_candidate_spdx_projection"] = (
        "local_v02_release_candidate_spdx_projection"
    )
    candidate_label: str = CANDIDATE_LABEL
    spdx_version: Literal["SPDX-2.3"] = "SPDX-2.3"
    components: tuple[V02CandidateSbomComponent, ...]
    vulnerability_scan_completed: bool = False
    registry_called: bool = False
    sbom_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateProvenanceRecord(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-provenance/v1"] = (
        V02_CANDIDATE_PROVENANCE_SCHEMA_VERSION
    )
    provenance_id: str
    candidate_label: str = CANDIDATE_LABEL
    source_commit: str
    artifact_fingerprint: str
    builder_identity: str
    network_mode: Literal["none"] = "none"
    pull_policy: Literal["false"] = "false"
    production: bool = False
    publication: bool = False
    created_at: datetime


class V02CandidateProvenanceChain(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-provenance/v1"] = (
        V02_CANDIDATE_PROVENANCE_SCHEMA_VERSION
    )
    records: tuple[V02CandidateProvenanceRecord, ...]
    chain_head: str


class V02CandidateChecksumRecord(V02CandidateBaseModel):
    relative_path: str
    sha256: str
    byte_count: int = Field(ge=0)


class V02CandidateChecksumManifest(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-checksum/v1"] = (
        V02_CANDIDATE_CHECKSUM_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    records: tuple[V02CandidateChecksumRecord, ...]
    checksum_manifest_fingerprint: str = ZERO_FINGERPRINT


class V02QualificationPublicKeyRecord(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-signature/v1"] = (
        V02_CANDIDATE_SIGNATURE_SCHEMA_VERSION
    )
    algorithm: Literal["Ed25519"] = "Ed25519"
    public_key_encoding: Literal["base64url"] = "base64url"
    public_key: str
    public_key_fingerprint: str
    created_at: datetime
    qualification_only: bool = True
    production_signing_key: bool = False


class V02QualificationSignatureRecord(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-signature/v1"] = (
        V02_CANDIDATE_SIGNATURE_SCHEMA_VERSION
    )
    signed_artifact_path: str
    signature_path: str
    signature_fingerprint: str
    public_key_fingerprint: str
    verified: bool = True


class V02CandidateReproducibilityComparison(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-reproducibility/v1"] = (
        V02_CANDIDATE_REPRODUCIBILITY_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    source_archive_reproducible: bool
    sdk_wheel_reproducible: bool
    sdk_sdist_reproducible: bool
    operator_console_bundle_reproducible: bool
    brain_api_normalized_invariants_passed: bool
    byte_for_byte_oci_reproducibility_confirmed: bool
    reproducibility_invariants_passed: bool
    comparison_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateCompatibilityRecord(V02CandidateBaseModel):
    check_id: str
    status: Literal["pass", "fail"]
    details: str


class V02CandidateCompatibilityMatrix(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-compatibility/v1"] = (
        V02_CANDIDATE_COMPATIBILITY_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    records: tuple[V02CandidateCompatibilityRecord, ...]
    all_required_checks_passed: bool
    compatibility_matrix_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateMigrationRecord(V02CandidateBaseModel):
    migration_id: str
    revision: str
    fingerprint: str
    candidate_delta_added: bool = False


class V02CandidateMigrationManifest(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-migration/v1"] = (
        V02_CANDIDATE_MIGRATION_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    records: tuple[V02CandidateMigrationRecord, ...]
    candidate_delta_migrations_added: int = 0
    production_migration_executed: bool = False
    migration_heads: tuple[str, ...] = ()
    staging_migration_evidence_inherited_from: Literal["AION-241"] = "AION-241"
    operator_review_required_for_final_production_migration_approval: bool = True
    migration_manifest_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateReleaseNotesRecord(V02CandidateBaseModel):
    candidate_label: str = CANDIDATE_LABEL
    draft: bool = True
    relative_path: str
    fingerprint: str
    v02_released: bool = False


class V02CandidateRetentionPlan(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-retention/v1"] = (
        V02_CANDIDATE_RETENTION_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    candidate_locator_id: str = CANDIDATE_LABEL
    candidate_root_policy: Literal[
        "user-home/.aion/release-candidates/<candidate-label>"
    ] = "user-home/.aion/release-candidates/<candidate-label>"
    maximum_retained_candidate_bundles: int = 1
    maximum_retained_candidate_images: int = 1


class V02CandidateRetentionResult(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-retention/v1"] = (
        V02_CANDIDATE_RETENTION_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    candidate_bundle_retained: bool
    candidate_bundle_count: int
    candidate_local_image_retained: bool
    candidate_local_image_count: int
    temporary_build_directories_retained: int = 0
    comparison_images_retained: int = 0
    private_qualification_keys_retained: int = 0


class V02CandidateIntegrityFinding(V02CandidateBaseModel):
    finding_id: str
    severity: Literal["info", "warning", "error"]
    message: str


class V02CandidateIntegrityReport(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-integrity/v1"] = (
        V02_CANDIDATE_INTEGRITY_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    checksums_valid: bool
    signatures_valid: bool
    local_candidate_image_valid: bool
    unknown_files: tuple[str, ...] = ()
    findings: tuple[V02CandidateIntegrityFinding, ...] = ()
    integrity_passed: bool
    integrity_report_fingerprint: str = ZERO_FINGERPRINT


class V02CandidateEvidenceBundle(V02CandidateBaseModel):
    schema_version: Literal["aion-v02-candidate-evidence/v1"] = (
        V02_CANDIDATE_EVIDENCE_SCHEMA_VERSION
    )
    candidate_label: str = CANDIDATE_LABEL
    authorization_id: str = AUTHORIZATION_TRANSACTION_ID
    source_snapshot: V02CandidateSourceSnapshotManifest
    version_manifest: V02CandidateVersionManifest
    artifact_manifest: V02CandidateArtifactManifest
    sbom: V02CandidateSbomDocument
    provenance_chain: V02CandidateProvenanceChain
    checksum_manifest: V02CandidateChecksumManifest
    signatures: tuple[V02QualificationSignatureRecord, ...]
    reproducibility: V02CandidateReproducibilityComparison
    compatibility: V02CandidateCompatibilityMatrix
    migration: V02CandidateMigrationManifest
    retention: V02CandidateRetentionResult
    integrity: V02CandidateIntegrityReport
    evidence_bundle_fingerprint: str = ZERO_FINGERPRINT


class InMemoryV02ReleaseCandidateRepository:
    """Effect-free in-memory session and evidence repository for tests."""

    def __init__(self) -> None:
        self._sessions: dict[str, V02ReleaseCandidateSession] = {}
        self._evidence: dict[str, V02CandidateEvidenceBundle] = {}
        self._request_fingerprints: dict[str, str] = {}

    def start_session(
        self, session: V02ReleaseCandidateSession
    ) -> V02ReleaseCandidateSession:
        if any(item.active for item in self._sessions.values()):
            raise ValueError("only one release-candidate session may be active")
        self._sessions[session.session_id] = session
        return session

    def close_session(self, session_id: str) -> V02ReleaseCandidateSession:
        session = self._sessions[session_id]
        closed = session.model_copy(update={"active": False, "closed_at": datetime.now(UTC)})
        self._sessions[session_id] = closed
        return closed

    def store_evidence(
        self, evidence: V02CandidateEvidenceBundle, request_fingerprint: str
    ) -> V02CandidateEvidenceBundle:
        self._evidence[evidence.candidate_label] = evidence
        self._request_fingerprints[evidence.candidate_label] = request_fingerprint
        return evidence

    def evidence(self, candidate_label: str = CANDIDATE_LABEL) -> V02CandidateEvidenceBundle:
        return self._evidence[candidate_label]

    def request_fingerprint(self, candidate_label: str = CANDIDATE_LABEL) -> str:
        return self._request_fingerprints[candidate_label]


def canonical_authorization_envelope() -> V02ReleaseCandidateAuthorizationEnvelope:
    return V02ReleaseCandidateAuthorizationEnvelope()


def canonical_component_binding(
    *,
    source_commit: str = AUTHORIZED_SOURCE_COMMIT_PLACEHOLDER,
) -> V02ReleaseCandidateComponentBinding:
    return V02ReleaseCandidateComponentBinding(
        component_id="aion-v02-release-candidate-core",
        source_path="services/brain-api/src/aion_brain/contracts/v02_release_candidate.py",
        source_commit=source_commit,
    )


def canonical_session_plan(
    session_id: str = "aion-243-release-candidate-session",
    *,
    now: datetime | None = None,
) -> V02ReleaseCandidateSessionPlan:
    created = now or datetime.now(UTC)
    plan = V02ReleaseCandidateSessionPlan(
        session_id=session_id,
        created_at=created,
        expires_at=created + timedelta(hours=3),
    )
    return plan.model_copy(
        update={"session_plan_fingerprint": v02_release_candidate_fingerprint(plan)}
    )


def canonical_version_manifest() -> V02CandidateVersionManifest:
    manifest = V02CandidateVersionManifest()
    return manifest.model_copy(
        update={"version_manifest_fingerprint": v02_release_candidate_fingerprint(manifest)}
    )


def canonical_artifact_plan(
    source_commit: str = AUTHORIZED_SOURCE_COMMIT_PLACEHOLDER,
) -> V02CandidateArtifactPlan:
    return V02CandidateArtifactPlan(
        source_commit=source_commit,
        artifact_kinds=(
            "source_archive",
            "brain_api_oci_archive",
            "sdk_wheel",
            "sdk_sdist",
            "operator_console_bundle",
            "sbom",
            "provenance",
            "checksums",
            "qualification_signatures",
            "compatibility_matrix",
            "migration_manifest",
            "release_notes_draft",
            "integrity_report",
            "evidence_bundle",
        ),
    )


__all__ = [
    name
    for name, value in globals().items()
    if name.startswith("V02")
    or name.startswith("AION")
    or name.startswith("PROGRAM")
    or name.startswith("AUTHORIZATION")
    or name.startswith("APPROVAL")
    or name.startswith("IMPLEMENTATION")
    or name.startswith("FORMAL")
    or name.startswith("FINAL")
    or name.startswith("CANDIDATE")
    or name.startswith("PYTHON")
    or name.startswith("LOCAL")
    or name.startswith("FROZEN")
    or name.startswith("ZERO")
    or name.startswith("APPROVED")
    or name.startswith("PROHIBITED")
    or name.startswith("POSITIVE")
    or name.startswith("ZERO_RESOURCE")
    or name.startswith("REQUIRED")
    or name == "InMemoryV02ReleaseCandidateRepository"
    or name.startswith("canonical_")
    or name in {"resource_limits", "approved_capabilities", "prohibited_capabilities"}
    or name in {"v02_release_candidate_fingerprint", "canonical_json_bytes"}
]
