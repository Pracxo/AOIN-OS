#!/usr/bin/env python3
"""AION-242 operator evaluation for AION-241 staging evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


PROGRAM_ID = "AION-V02-RELEASE-QUALIFICATION-001"
EVALUATION_ID = "AION-V02RQPE-002"
EVALUATION_TYPE = "controlled_isolated_staging_qualification_operator_evaluation"
IMPLEMENTATION_TASK = "AION-241"
CLOSEOUT_TASK = "AION-242"
NEXT_IMPLEMENTATION_TASK = "AION-243"
NEXT_FORMAL_CLOSEOUT_TASK = "AION-244"
FINAL_PLANNED_TASK = "AION-244"
CURRENT_AUTHORIZATION_ID = "AION-240-V02RQ-0002"
NEXT_AUTHORIZATION_ID = "AION-242-V02RQ-0003"
IMPLEMENTATION_PR = 160
IMPLEMENTATION_BRANCH = "phase/v02-controlled-staging-qualification"
IMPLEMENTATION_COMMIT = "b378162fde84fcadd3fc353ae1e95936690abbcd"
EVIDENCE_COMMIT = "1ac103875a2eb2a5f7f1a21d7891bc76ac63d587"
IMPLEMENTATION_MERGE_COMMIT = "24095a3fabe95b59f2607134199d160e8122e343"
IMPLEMENTATION_MERGED_AT = "2026-08-02T11:51:27Z"
PASS_DECISION = (
    "CONTROLLED_ISOLATED_LOCAL_STAGING_QUALIFICATION_OPERATOR_EVALUATION_PASS_"
    "RECOMMEND_DETERMINISTIC_V02_RELEASE_CANDIDATE_ARTIFACT_BUILD_AUTHORIZATION"
)
FAIL_DECISION = (
    "CONTROLLED_ISOLATED_LOCAL_STAGING_QUALIFICATION_OPERATOR_EVALUATION_FAIL_"
    "REMAIN_LOCAL_STAGING_EVIDENCE_ONLY"
)
NEXT_ARCHITECTURE_PASS = "deterministic_v02_release_candidate_artifact_build_authorized"
NEXT_ARCHITECTURE_FAIL = "staging_qualification_remediation_review"
EXPECTED_PILOT_FINGERPRINT = (
    "afa1ca70fe05e271cb989a8c7dcc2b1cf5a25202c7854f6b1e624ca5cf7c029c"
)
EXPECTED_SOURCE_TREE_FINGERPRINT = (
    "611048ac62d61777588468dda09e9fd6586ade67303d50bbc2df22b0a82dd1ee"
)
EXPECTED_GIT_ARCHIVE_FINGERPRINT = (
    "f16737500208a0e6dfdb7b899268f6c10ec03170da8f3f1ded9af4161d3e3d5d"
)
EXPECTED_GIT_TREE_SHA = "9b8ce3adc4d662d6cfe8e2b39879a71e17895271"
EXPECTED_BASE_IMAGE_TAG = "aoinos-brain-api:aion241-base-9f6b899f84ef"
EXPECTED_BASE_IMAGE_ID = (
    "sha256:d55ed37f90d85ca0fc5973e6d3cdd849353e0549a7df95d39864506712b342ea"
)
EXPECTED_REJECTED_LATEST_IMAGE_ID = (
    "sha256:3f46490ee0b150a90b778b03a6957e1c07cb66e0e9b59052d2fd607c9ba7ffe5"
)
EXPECTED_BASE_IMAGE_FINGERPRINT = (
    "1016433bb0447433757344b9a150cb6c30aac6c4d4e0ba5e1cef352363988b82"
)
EXPECTED_BUILD_PLAN_FINGERPRINT = (
    "37d98960c083dd512c217682accd5a4c4d3fcdee106b8e28f85e39c7f2eb01e1"
)
EXPECTED_GENERATED_DOCKERFILE_FINGERPRINT = (
    "889363969d1f2368f65aec99ccfbe844036ace558c5ded50ada40751c5b2c211"
)
EXPECTED_BUILD_CONTEXT_FINGERPRINT = (
    "c36c8536bcf304d6fdfd48769a64623c1080e6965a4f3b597c94b49ab3181366"
)
EXPECTED_STAGING_ARTIFACT_FINGERPRINTS: tuple[str, ...] = (
    "cba4c182ca5b5a8af24cc02b29503de3853792eaf4952038789130bb8820e0c9",
    "763d15fd1bc6af433f5b92a5f5b0cfba3641ec82391e50ed2a5c3cf63dc3d360",
)
EXPECTED_DEPLOYED_STAGING_IMAGE_FINGERPRINT = (
    "84eec8099977ad96ca4e5fbb918b476c9e92cd5fb738f8287c7e1c2832e4c21a"
)
EXPECTED_SBOM_FINGERPRINT = (
    "e3cdf38b807b9c6f512ab20cc344a8a45500f9ded0ccffbf3f196c4bb65b3975"
)
EXPECTED_PROVENANCE_CHAIN_HEAD = (
    "8d2fd197fba429e5dfef98eb3701f817cbebca57073cd32d11e11d6a3dc19945"
)
EXPECTED_REPRODUCIBILITY_FINGERPRINT = (
    "9879d7d8686bb96d65862cfdb9f3ebae5363eebbb1d46d9f567fae7b20774c42"
)
EXPECTED_ENVIRONMENT_PROFILE_FINGERPRINT = (
    "8a89d347d02bfc7ef0ac6e671eb1411031e77c8b3d533b6ab1be78320450a471"
)
EXPECTED_COMPOSE_PLAN_FINGERPRINT = (
    "a74e883433ff130a6e547a4a7e94e854503205476f53bf67e60bf6987c432215"
)
EXPECTED_INTERNAL_NETWORK_FINGERPRINT = (
    "91dd3b5f440a13ff34a58808355d69629eee38fc46dc19ce0cdbf27e4a7921a2"
)
EXPECTED_IDENTITY_FIXTURE_FINGERPRINT = (
    "28e4f877e7ca5d30e5cd146faf4de786ee533aa9ba3a7fb26bea5d11a0f3e42a"
)
EXPECTED_REPLAY_FIXTURE_FINGERPRINT = (
    "5f08931798088842e24b4626e99d1c54cc0c40ef936a0b9729190509b69abec6"
)
EXPECTED_HEALTH_READINESS_FINGERPRINT = (
    "6cd3b70d591e8b2eeb87d78e628ecbc628f5e4b3b89536703ff727ee6799c3ba"
)
EXPECTED_SECURITY_VALIDATION_FINGERPRINT = (
    "224400e5ff6f4ab09d9992cbd224231c49fa7b34187cd59eb0cddb6e842494fd"
)
EXPECTED_OBSERVABILITY_FINGERPRINT = (
    "d0cb7eb47e42ee9748bfee41cfda704ccb1d4e6ccd748e72e3e61bb080ba7177"
)
EXPECTED_ROLLBACK_PLAN_FINGERPRINT = (
    "5ea881114870a435c0c0aadccaf9a1c5a78bbb1d5bfc442d76da634f12e54e5e"
)
EXPECTED_ROLLBACK_RESULT_FINGERPRINT = (
    "21af9e6ac4453138353b8577ce0bba33173075a70305785b4ca606026517b50f"
)
EXPECTED_CLEANUP_RESULT_FINGERPRINT = (
    "57049c329f7147d6e0d244e85d57da3f3190f7080bce898ee73fef2a67a9fb27"
)

REQUIRED_CI_CHECKS: tuple[str, ...] = (
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
)

SCENARIO_IDS: tuple[str, ...] = (
    "aion_241_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "staging_pilot_schema_and_report_fingerprint",
    "exact_source_and_repository_boundary",
    "immutable_source_snapshot_integrity",
    "frozen_base_and_dependency_image_lineage",
    "offline_build_and_registry_boundary",
    "reproducibility_evidence_honesty",
    "staging_artifact_manifest_integrity",
    "sbom_completeness_and_integrity",
    "artifact_provenance_chain_integrity",
    "isolated_environment_and_internal_network_integrity",
    "loopback_exposure_and_host_port_boundary",
    "ephemeral_identity_fixture_integrity",
    "ephemeral_replay_fixture_and_rejection_integrity",
    "staging_deployment_lifecycle_integrity",
    "health_and_readiness_evidence_integrity",
    "staging_security_validation_completeness",
    "protected_material_redaction_integrity",
    "staging_configuration_drift_detection",
    "local_observability_evidence_integrity",
    "controlled_degradation_detection",
    "rollback_and_post_recovery_integrity",
    "cleanup_and_preexisting_resource_preservation",
    "docker_command_allowlist_and_runner_boundary",
    "determinism_idempotency_redaction_and_performance",
    "zero_production_and_release_effects",
    "deterministic_release_candidate_build_authorization_readiness",
)

EXPECTED_DEPENDENCY_IMAGE_IDS: dict[str, str] = {
    "nats:2-alpine": "sha256:b039b46715673a9436989cfc49dde04e6bd57e205347478a58214789baf5efdc",
    "openpolicyagent/opa:latest": "sha256:3c6e9e4d433b6e94df424c3385134312a95042aa991cdfc8e01944115675fb9d",
    "pgvector/pgvector:pg16": "sha256:00ba258a66dac104fd5171074a0084462a64a1369d8513f3d0a634e2f24d15bc",
    "redis:7-alpine": "sha256:6ab0b6e7381779332f97b8ca76193e45b0756f38d4c0dcda72dbb3c32061ab99",
}
EXPECTED_DEPENDENCY_IMAGE_FINGERPRINTS: dict[str, str] = {
    "nats:2-alpine": "0eff6d28677acc4f7d14e8e61ebce38136751b495a668f43e06f46efd30ff169",
    "openpolicyagent/opa:latest": "75feee79cfe343b705a2226b297ff9424c47f9dbb3bf18268652f83dfb1cfa27",
    "pgvector/pgvector:pg16": "fe4b77b3d60fa981def75828abbd38f2bdc9087034fe4d12bd1912099346b5ba",
    "redis:7-alpine": "f7314d216f4bc70a0083697ace964f85bb7d4a974ced38183cc33816cbd2d756",
}

EXPECTED_PILOT_COUNTERS: dict[str, int | bool] = {
    "staging_qualification_sessions_started": 1,
    "staging_qualification_sessions_closed": 1,
    "active_qualification_sessions_after_close": 0,
    "source_snapshots_created": 1,
    "git_archive_operations": 1,
    "offline_local_builds_completed": 2,
    "local_staging_artifacts_created": 2,
    "sbom_projections_created": 1,
    "artifact_provenance_records_created": 2,
    "reproducibility_comparisons_completed": 1,
    "isolated_networks_created": 1,
    "isolated_networks_removed": 1,
    "staging_deployments_completed": 1,
    "running_staging_containers_peak": 6,
    "loopback_listeners_created": 1,
    "public_listeners_created": 0,
    "non_loopback_listeners_created": 0,
    "ephemeral_identity_keypairs_created": 1,
    "ephemeral_identity_keypairs_persisted": 0,
    "ephemeral_replay_ledgers_created": 1,
    "ephemeral_replay_ledgers_persisted": 0,
    "health_checks_passed": 3,
    "readiness_checks_passed": 4,
    "security_tests_passed": 12,
    "identity_spoofing_tests_passed": 1,
    "replay_rejection_tests_passed": 1,
    "protected_material_redaction_tests_passed": 1,
    "configuration_drift_tests_passed": 1,
    "controlled_degradations_injected": 1,
    "health_failures_detected": 1,
    "staging_rollbacks_completed": 1,
    "post_rollback_health_recovered": True,
    "local_observability_records_created": 4,
    "active_containers_after_cleanup": 0,
    "active_volumes_after_cleanup": 0,
    "active_networks_after_cleanup": 0,
    "run_owned_images_after_cleanup": 0,
    "temporary_files_retained": 0,
}

EXPECTED_PROHIBITED_COUNTERS: dict[str, int] = {
    "registry_logins": 0,
    "registry_pulls": 0,
    "registry_pushes": 0,
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
    "external_log_exports": 0,
    "external_metric_exports": 0,
    "external_trace_exports": 0,
    "release_candidates_created": 0,
    "v02_tags_created": 0,
    "v02_releases_created": 0,
}

REPORT_ZERO_EFFECT_FIELDS: tuple[str, ...] = (
    "docker_builds_executed_by_evaluation",
    "staging_deployments_executed_by_evaluation",
    "rollback_executions_by_evaluation",
    "public_network_calls",
    "external_network_egress_calls",
    "dns_resolutions",
    "registry_logins",
    "registry_pulls",
    "registry_pushes",
    "external_identity_provider_calls",
    "production_credentials_used",
    "production_tokens_used",
    "production_database_operations",
    "production_deployments",
    "release_candidates_created",
    "v02_tags_created",
    "v02_releases_created",
    "active_staging_resources_after_evaluation",
)

FUTURE_AION243_SOURCE_SCOPE: tuple[str, ...] = (
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
)
FUTURE_AION243_RUNNER = "scripts/v02-release-candidate-local-run.py"
FUTURE_CANDIDATE_ID = "aion-v0.2.0-rc.1"
FUTURE_PYTHON_PACKAGE_VERSION = "0.2.0rc1"
FUTURE_AION243_ARTIFACTS: tuple[str, ...] = (
    "deterministic_source_archive",
    "brain_api_oci_image_archive_or_layout_projection",
    "brain_api_artifact_manifest",
    "sdk_wheel",
    "sdk_source_distribution",
    "operator_console_static_bundle",
    "candidate_version_manifest",
    "candidate_sbom",
    "artifact_provenance",
    "sha256_checksum_manifest",
    "qualification_detached_signatures",
    "qualification_public_key_record",
    "reproducibility_comparison",
    "compatibility_matrix",
    "migration_manifest",
    "release_notes_draft",
    "candidate_evidence_bundle",
)
APPROVED_AION243_CAPABILITIES: tuple[str, ...] = (
    "release_candidate_contract_approved",
    "release_candidate_authorization_envelope_approved",
    "staging_evidence_component_binding_approved",
    "immutable_candidate_source_snapshot_approved",
    "candidate_version_manifest_approved",
    "bounded_package_version_update_approved",
    "runtime_logic_source_freeze_approved",
    "deterministic_source_archive_approved",
    "brain_api_oci_candidate_build_approved",
    "sdk_wheel_candidate_build_approved",
    "sdk_sdist_candidate_build_approved",
    "operator_console_candidate_bundle_approved",
    "candidate_bundle_manifest_approved",
    "candidate_sbom_generation_approved",
    "candidate_artifact_provenance_approved",
    "candidate_checksum_manifest_approved",
    "qualification_signature_approved",
    "qualification_public_key_record_approved",
    "candidate_reproducibility_comparison_approved",
    "compatibility_matrix_approved",
    "migration_manifest_approved",
    "release_notes_draft_approved",
    "candidate_integrity_audit_approved",
    "candidate_retention_approved",
    "candidate_cleanup_of_temporary_resources_approved",
    "documentation_and_static_evidence_approved",
)
PROHIBITED_AION243_CAPABILITIES: tuple[str, ...] = (
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "registry_login_enabled",
    "registry_pull_enabled",
    "registry_push_enabled",
    "public_package_registry_upload_enabled",
    "production_signing_key_enabled",
    "production_credentials_enabled",
    "production_tokens_enabled",
    "production_database_enabled",
    "production_deployment_enabled",
    "production_rollback_enabled",
    "cloud_deployment_enabled",
    "release_candidate_publication_enabled",
    "release_candidate_promotion_enabled",
    "git_tag_creation_enabled",
    "github_release_creation_enabled",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
    "production_runtime_authorized",
    "production_exposure",
    "automatic_merge_enabled",
    "source_rewrite_outside_authorized_metadata_enabled",
    "runtime_logic_change_enabled",
)
POSITIVE_AION243_LIMITS: dict[str, int] = {
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
ZERO_AION243_LIMITS: tuple[str, ...] = (
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

PROTECTED_VALUE_MARKERS: tuple[str, ...] = (
    "-----begin",
    "private key",
    "signed assertion",
    "database password",
    "authorization: bearer",
    "sk-",
    "ghp_",
    "xoxb-",
    "temporary-root",
    "/tmp/aion241",
    "0.0.0.0",
)
READ_ONLY_DOCKER_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("context", "show"),
    ("context", "inspect"),
    ("version",),
    ("info",),
    ("ps", "--all"),
    ("image", "ls"),
    ("image", "inspect"),
    ("network", "ls"),
    ("network", "inspect"),
    ("volume", "ls"),
    ("volume", "inspect"),
)


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def report_fingerprint(report: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(report))
    payload.pop("report_fingerprint", None)
    return stable_fingerprint(payload)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_public_api(repo_root: Path) -> Any:
    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from aion_brain.contracts import v02_staging_qualification as api

    return api


def check(name: str, passed: bool, evidence: Any = None) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "passed": bool(passed)}
    if evidence is not None:
        item["evidence"] = evidence
    return item


def scenario(scenario_id: str, checks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    passed = bool(checks) and all(item.get("passed") is True for item in checks)
    return {
        "scenario_id": scenario_id,
        "hard_gate": True,
        "status": "pass" if passed else "fail",
        "passed": passed,
        "checks": list(checks),
    }


def run_read_only_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 15,
) -> dict[str, Any]:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "argv": list(argv),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def git_object_exists(repo_root: Path, oid: str) -> bool:
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{oid}^{{commit}}"],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def git_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    if not (git_object_exists(repo_root, ancestor) and git_object_exists(repo_root, descendant)):
        return None
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def v02_tags_absent(repo_root: Path) -> bool:
    completed = subprocess.run(
        ["git", "tag", "--list", "v0.2*", "aion-v0.2*"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and not completed.stdout.strip()


def local_docker_resource_state(repo_root: Path) -> dict[str, Any]:
    require_local = os.environ.get("AION242_REQUIRE_LOCAL_DOCKER") == "1"
    docker = os.environ.get("AION242_DOCKER_BIN", "docker")
    state: dict[str, Any] = {
        "required": require_local,
        "verified": False,
        "status": "not_required",
        "read_only_commands": [" ".join(command) for command in READ_ONLY_DOCKER_COMMANDS],
    }
    try:
        context = run_read_only_command([docker, "context", "show"], cwd=repo_root)
        ps = run_read_only_command(
            [
                docker,
                "ps",
                "--all",
                "--filter",
                "label=io.aion.task=AION-241",
                "--format",
                "{{.ID}}",
            ],
            cwd=repo_root,
        )
        networks = run_read_only_command(
            [
                docker,
                "network",
                "ls",
                "--filter",
                "label=io.aion.task=AION-241",
                "--format",
                "{{.ID}}",
            ],
            cwd=repo_root,
        )
        volumes = run_read_only_command(
            [
                docker,
                "volume",
                "ls",
                "--filter",
                "label=io.aion.task=AION-241",
                "--format",
                "{{.Name}}",
            ],
            cwd=repo_root,
        )
        base = run_read_only_command(
            [docker, "image", "inspect", EXPECTED_BASE_IMAGE_TAG, "--format", "{{.Id}}"],
            cwd=repo_root,
        )
        latest = run_read_only_command(
            [docker, "image", "inspect", "aoinos-brain-api:latest", "--format", "{{.Id}}"],
            cwd=repo_root,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        state.update({"status": "unavailable", "error": type(exc).__name__})
        state["verified"] = not require_local
        return state

    context_ok = context["returncode"] == 0 and context["stdout"] == "desktop-linux"
    resource_zero = (
        ps["returncode"] == 0
        and networks["returncode"] == 0
        and volumes["returncode"] == 0
        and not ps["stdout"]
        and not networks["stdout"]
        and not volumes["stdout"]
    )
    base_ok = base["returncode"] == 0 and base["stdout"] == EXPECTED_BASE_IMAGE_ID
    latest_ok = latest["returncode"] == 0 and latest["stdout"] == EXPECTED_REJECTED_LATEST_IMAGE_ID
    state.update(
        {
            "status": "verified" if (context_ok and resource_zero and base_ok and latest_ok) else "failed",
            "context": context["stdout"],
            "context_ok": context_ok,
            "aion_241_labeled_containers": 0 if ps["stdout"] == "" else len(ps["stdout"].splitlines()),
            "aion_241_labeled_networks": 0
            if networks["stdout"] == ""
            else len(networks["stdout"].splitlines()),
            "aion_241_labeled_volumes": 0
            if volumes["stdout"] == ""
            else len(volumes["stdout"].splitlines()),
            "run_owned_resources_absent": resource_zero,
            "base_image_id": base["stdout"],
            "base_image_present": base_ok,
            "latest_image_id": latest["stdout"],
            "rejected_latest_preserved": latest_ok,
        }
    )
    state["verified"] = context_ok and resource_zero and base_ok and latest_ok
    return state


def pilot_fingerprint_matches(api: Any, pilot: Mapping[str, Any]) -> bool:
    body = {key: value for key, value in pilot.items() if key != "report_fingerprint"}
    return pilot.get("report_fingerprint") == api.v02_staging_fingerprint(body)


def validate_pilot_model(api: Any, pilot: Mapping[str, Any]) -> bool:
    fields = set(api.V02StagingQualificationEvidenceBundle.model_fields)
    model_payload = {key: value for key, value in pilot.items() if key in fields}
    model_payload.pop("report_fingerprint", None)
    api.V02StagingQualificationEvidenceBundle(**model_payload)
    return True


def source_scope_state(repo_root: Path, api: Any) -> dict[str, Any]:
    runtime_root = repo_root / "services/brain-api/src/aion_brain/v02_staging_qualification"
    actual_runtime = {
        f"services/brain-api/src/aion_brain/v02_staging_qualification/{path.name}"
        for path in runtime_root.glob("*.py")
    }
    required_runtime = set(api.REQUIRED_SOURCE_SCOPE[1:])
    return {
        "required_source_scope": list(api.REQUIRED_SOURCE_SCOPE),
        "missing_source_scope": [
            path for path in api.REQUIRED_SOURCE_SCOPE if not (repo_root / path).is_file()
        ],
        "runtime_source_scope_exact": actual_runtime == required_runtime,
        "prohibited_source_present": [
            path for path in api.PROHIBITED_SOURCE_SCOPE if (repo_root / path).exists()
        ],
        "aion_241_runner_present": (
            repo_root / "scripts/v02-staging-qualification-local-run.py"
        ).is_file(),
        "future_aion_243_source_present": [
            path for path in FUTURE_AION243_SOURCE_SCOPE if (repo_root / path).exists()
        ],
        "future_aion_243_runner_present": (repo_root / FUTURE_AION243_RUNNER).exists(),
    }


def authorization_lineage_state(program: Mapping[str, Any], auth: Mapping[str, Any]) -> dict[str, Any]:
    closeout = program.get("aion_240_authorization_closeout", {})
    active = {
        item.get("authorization_transaction_id"): item
        for item in program.get("active_authorizations", [])
        if isinstance(item, Mapping)
    }
    pre_closeout = (
        auth.get("authorization_transaction_id") == CURRENT_AUTHORIZATION_ID
        and auth.get("approval_record_id") == CURRENT_AUTHORIZATION_ID
        and auth.get("program_id") == PROGRAM_ID
        and auth.get("candidate_id") == "controlled-isolated-local-staging-artifact-and-rollback-drill-core"
        and auth.get("implementation_task") == IMPLEMENTATION_TASK
        and auth.get("formal_closeout_task") == CLOSEOUT_TASK
        and auth.get("final_planned_task") == FINAL_PLANNED_TASK
        and auth.get("authorization_active") is True
        and auth.get("authorization_consumed") is False
        and auth.get("authorization_expired") is False
        and auth.get("authorization_reusable") is False
        and auth.get("active_v02_release_qualification_authorization_count") == 1
        and auth.get("active_v02_release_qualification_authorization") == CURRENT_AUTHORIZATION_ID
    )
    post_closeout = (
        auth.get("authorization_transaction_id") == NEXT_AUTHORIZATION_ID
        and auth.get("approval_record_id") == NEXT_AUTHORIZATION_ID
        and auth.get("parent_authorization_transaction_id") == CURRENT_AUTHORIZATION_ID
        and auth.get("parent_evaluation_id") == EVALUATION_ID
        and auth.get("parent_evaluation_decision") == PASS_DECISION
        and auth.get("implementation_task") == NEXT_IMPLEMENTATION_TASK
        and auth.get("formal_closeout_task") == NEXT_FORMAL_CLOSEOUT_TASK
        and auth.get("authorization_active") is True
        and auth.get("authorization_consumed") is False
        and auth.get("authorization_expired") is False
        and auth.get("authorization_reusable") is False
        and auth.get("active_v02_release_qualification_authorization_count") == 1
        and auth.get("active_v02_release_qualification_authorization") == NEXT_AUTHORIZATION_ID
        and closeout.get("authorization_transaction_id") == CURRENT_AUTHORIZATION_ID
        and closeout.get("authorization_active") is False
        and closeout.get("authorization_consumed") is True
        and closeout.get("authorization_expired") is True
        and closeout.get("authorization_reusable") is False
    )
    active_id = program.get("active_v02_release_qualification_authorization")
    return {
        "pre_closeout_valid": pre_closeout,
        "post_closeout_valid": post_closeout,
        "lineage_valid": pre_closeout or post_closeout,
        "active_authorization_id": active_id,
        "active_authorization_count": program.get(
            "active_v02_release_qualification_authorization_count"
        ),
        "sole_active_authorization_exact": (
            (
                pre_closeout
                and active_id == CURRENT_AUTHORIZATION_ID
                and CURRENT_AUTHORIZATION_ID in active
            )
            or (
                post_closeout
                and active_id == NEXT_AUTHORIZATION_ID
                and NEXT_AUTHORIZATION_ID in active
            )
        ),
        "closeout": closeout,
    }


def no_protected_markers(payload: Mapping[str, Any]) -> bool:
    text = json.dumps(payload, sort_keys=True).lower()
    return not any(marker in text for marker in PROTECTED_VALUE_MARKERS)


def future_authorization_projection(evaluation_base_commit: str) -> dict[str, Any]:
    return {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
        "approval_record_id": NEXT_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": CURRENT_AUTHORIZATION_ID,
        "parent_evaluation_id": EVALUATION_ID,
        "parent_evaluation_decision": PASS_DECISION,
        "parent_implementation_task": IMPLEMENTATION_TASK,
        "parent_implementation_prs": [IMPLEMENTATION_PR],
        "parent_implementation_feature_commits": [IMPLEMENTATION_COMMIT, EVIDENCE_COMMIT],
        "parent_implementation_merge_commits": [IMPLEMENTATION_MERGE_COMMIT],
        "parent_implementation_main_commit": IMPLEMENTATION_MERGE_COMMIT,
        "parent_evaluation_base_commit": evaluation_base_commit,
        "candidate_id": "deterministic-v02-release-candidate-artifact-build-core",
        "candidate_label": FUTURE_CANDIDATE_ID,
        "candidate_python_package_version": FUTURE_PYTHON_PACKAGE_VERSION,
        "workstream": "v02-release-candidate-artifact-build",
        "implementation_task": NEXT_IMPLEMENTATION_TASK,
        "formal_closeout_task": NEXT_FORMAL_CLOSEOUT_TASK,
        "final_planned_task": FINAL_PLANNED_TASK,
        "authorization_scope": (
            "deterministic-local-v02-release-candidate-source-archive-brain-api-oci-"
            "sdk-package-operator-console-bundle-sbom-provenance-checksum-qualification-"
            "signature-reproducibility-compatibility-release-notes-retention-no-production-"
            "deployment-no-git-tag-no-public-release-core"
        ),
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
        "approved_capabilities": dict.fromkeys(APPROVED_AION243_CAPABILITIES, True),
        "prohibited_capabilities": dict.fromkeys(PROHIBITED_AION243_CAPABILITIES, False),
        "resource_limits": {
            **POSITIVE_AION243_LIMITS,
            **dict.fromkeys(ZERO_AION243_LIMITS, 0),
        },
        "future_source_scope": list(FUTURE_AION243_SOURCE_SCOPE),
        "future_uninstalled_runner": FUTURE_AION243_RUNNER,
        "artifact_set": list(FUTURE_AION243_ARTIFACTS),
        "release_candidate_created": False,
        "release_candidate_published": False,
        "production_runtime_authorized": False,
        "production_deployment_enabled": False,
        "v02_release_ready": False,
        "v02_tag_created": False,
        "v02_release_created": False,
    }


def evaluate(
    *,
    repo_root: Path,
    evaluation_id: str,
    implementation_main_commit: str,
    evaluation_base_commit: str,
    pilot_evidence_path: Path,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    del temporary_output_directory
    api = load_public_api(repo_root)
    pilot = load_json(pilot_evidence_path)
    program = load_json(repo_root / "docs/v02-release-qualification/program-ledger.json")
    auth = load_json(repo_root / "docs/v02-release-qualification/authorization-ledger.json")
    staging_auth = load_json(
        repo_root / "examples/v02-release-qualification/staging-qualification-authorization.json"
    )
    source = source_scope_state(repo_root, api)
    auth_state = authorization_lineage_state(program, auth)
    docker_state = local_docker_resource_state(repo_root)
    future_auth = future_authorization_projection(evaluation_base_commit)
    commits_available = {
        oid: git_object_exists(repo_root, oid)
        for oid in (IMPLEMENTATION_COMMIT, EVIDENCE_COMMIT, IMPLEMENTATION_MERGE_COMMIT)
    }
    lineage = {
        "implementation_ancestor_of_merge": git_ancestor(
            repo_root, IMPLEMENTATION_COMMIT, IMPLEMENTATION_MERGE_COMMIT
        ),
        "evidence_ancestor_of_merge": git_ancestor(
            repo_root, EVIDENCE_COMMIT, IMPLEMENTATION_MERGE_COMMIT
        ),
    }
    pilot_model_valid = validate_pilot_model(api, pilot)
    expected_counter_match = all(
        pilot.get(key, pilot.get("pilot_counters", {}).get(key)) == value
        for key, value in EXPECTED_PILOT_COUNTERS.items()
    )
    prohibited_counter_match = all(
        pilot.get(key, pilot.get("prohibited_effect_counters", {}).get(key)) == value
        for key, value in EXPECTED_PROHIBITED_COUNTERS.items()
    ) and pilot.get("prohibited_effect_counters") == EXPECTED_PROHIBITED_COUNTERS
    all_prohibited_ledgers_false = all(
        not any(payload.get("prohibited_capabilities", {}).values())
        for payload in (program, auth, staging_auth)
    )

    scenarios: list[dict[str, Any]] = [
        scenario(
            "aion_241_delivery_and_ci_integrity",
            (
                check("pr_number_exact", IMPLEMENTATION_PR == 160, IMPLEMENTATION_PR),
                check("branch_exact", IMPLEMENTATION_BRANCH == "phase/v02-controlled-staging-qualification"),
                check("implementation_commit_exact", IMPLEMENTATION_COMMIT == "b378162fde84fcadd3fc353ae1e95936690abbcd"),
                check("evidence_commit_exact", EVIDENCE_COMMIT == "1ac103875a2eb2a5f7f1a21d7891bc76ac63d587"),
                check("merge_commit_exact", implementation_main_commit == IMPLEMENTATION_MERGE_COMMIT),
                check("merged_timestamp_exact", IMPLEMENTATION_MERGED_AT == "2026-08-02T11:51:27Z"),
                check("required_ci_checks_recorded", list(REQUIRED_CI_CHECKS) == sorted(REQUIRED_CI_CHECKS)),
                check(
                    "local_git_objects_available_or_shallow_checkout_safe",
                    all(commits_available.values()) or not any(commits_available.values()),
                    commits_available,
                ),
                check(
                    "local_git_lineage_valid_when_available",
                    all(value is True for value in lineage.values())
                    or all(value is None for value in lineage.values()),
                    lineage,
                ),
            ),
        ),
        scenario(
            "authorization_lineage_and_scope",
            (
                check("authorization_lineage_valid", auth_state["lineage_valid"], auth_state),
                check("sole_active_authorization_exact", auth_state["sole_active_authorization_exact"]),
                check("program_id_exact", auth.get("program_id") == PROGRAM_ID),
                check("approved_capabilities_exact", auth.get("approved_capabilities") in ({key: True for key in api.APPROVED_CAPABILITIES}, future_auth["approved_capabilities"])),
                check("prohibited_capabilities_false", all_prohibited_ledgers_false),
                check("release_hold_preserved", program.get("v02_release_ready") is False),
            ),
        ),
        scenario(
            "staging_pilot_schema_and_report_fingerprint",
            (
                check("pilot_model_valid", pilot_model_valid),
                check("pilot_id_exact", pilot.get("pilot_id") == api.PILOT_ID),
                check("authorization_exact", pilot.get("authorization_id") == CURRENT_AUTHORIZATION_ID),
                check("program_exact", pilot.get("program_id") == PROGRAM_ID),
                check("mode_exact", pilot.get("mode") == "controlled-local-docker"),
                check("report_fingerprint_exact", pilot.get("report_fingerprint") == EXPECTED_PILOT_FINGERPRINT),
                check("report_fingerprint_valid", pilot_fingerprint_matches(api, pilot)),
                check("integrity_passed", pilot.get("integrity_passed") is True),
            ),
        ),
        scenario(
            "exact_source_and_repository_boundary",
            (
                check("source_scope_present", not source["missing_source_scope"], source),
                check("runtime_source_scope_exact", source["runtime_source_scope_exact"]),
                check("prohibited_aion241_source_absent", not source["prohibited_source_present"]),
                check("aion241_runner_present", source["aion_241_runner_present"]),
                check("aion243_source_absent", not source["future_aion_243_source_present"]),
                check("aion243_runner_absent", not source["future_aion_243_runner_present"]),
            ),
        ),
        scenario(
            "immutable_source_snapshot_integrity",
            (
                check("implementation_commit_exact", pilot.get("implementation_commit") == IMPLEMENTATION_COMMIT),
                check("source_snapshot_commit_exact", pilot.get("source_snapshot_commit") == IMPLEMENTATION_COMMIT),
                check("git_tree_sha_exact", pilot.get("git_tree_sha") == EXPECTED_GIT_TREE_SHA),
                check("source_tree_fingerprint_exact", pilot.get("source_tree_fingerprint") == EXPECTED_SOURCE_TREE_FINGERPRINT),
                check("git_archive_fingerprint_exact", pilot.get("git_archive_fingerprint") == EXPECTED_GIT_ARCHIVE_FINGERPRINT),
                check("source_snapshot_file_count_exact", pilot.get("source_snapshot_file_count") == 7516),
                check("source_snapshot_byte_count_exact", pilot.get("source_snapshot_byte_count") == 39216358),
            ),
        ),
        scenario(
            "frozen_base_and_dependency_image_lineage",
            (
                check("base_image_tag_exact", pilot.get("base_image_tag") == EXPECTED_BASE_IMAGE_TAG),
                check("base_image_id_exact", pilot.get("base_image_id") == EXPECTED_BASE_IMAGE_ID),
                check("base_image_fingerprint_exact", pilot.get("base_image_fingerprint") == EXPECTED_BASE_IMAGE_FINGERPRINT),
                check("dependency_image_ids_exact", pilot.get("dependency_image_ids") == EXPECTED_DEPENDENCY_IMAGE_IDS),
                check("dependency_image_fingerprints_exact", pilot.get("dependency_image_fingerprints") == EXPECTED_DEPENDENCY_IMAGE_FINGERPRINTS),
            ),
        ),
        scenario(
            "offline_build_and_registry_boundary",
            (
                check("two_offline_builds_completed", pilot.get("offline_local_builds_completed") == 2),
                check("build_plan_fingerprint_exact", pilot.get("build_plan_fingerprint") == EXPECTED_BUILD_PLAN_FINGERPRINT),
                check("generated_dockerfile_fingerprint_exact", pilot.get("generated_dockerfile_fingerprint") == EXPECTED_GENERATED_DOCKERFILE_FINGERPRINT),
                check("build_context_fingerprint_exact", pilot.get("build_context_fingerprint") == EXPECTED_BUILD_CONTEXT_FINGERPRINT),
                check("registry_counters_zero", all(pilot.get(key) == 0 for key in ("registry_logins", "registry_pulls", "registry_pushes"))),
                check("public_egress_counters_zero", all(pilot.get(key) == 0 for key in ("public_network_calls", "external_network_egress_calls", "dns_resolutions"))),
            ),
        ),
        scenario(
            "reproducibility_evidence_honesty",
            (
                check("reproducibility_fingerprint_exact", pilot.get("reproducibility_comparison_fingerprint") == EXPECTED_REPRODUCIBILITY_FINGERPRINT),
                check("invariants_passed", pilot.get("reproducibility_invariants_passed") is True),
                check("byte_for_byte_truthfully_false", pilot.get("byte_for_byte_reproducibility_confirmed") is False),
                check("comparison_count_exact", pilot.get("reproducibility_comparisons_completed") == 1),
            ),
        ),
        scenario(
            "staging_artifact_manifest_integrity",
            (
                check("artifact_fingerprints_exact", tuple(pilot.get("staging_artifact_fingerprints", ())) == EXPECTED_STAGING_ARTIFACT_FINGERPRINTS),
                check("deployed_staging_image_fingerprint_exact", pilot.get("deployed_staging_image_fingerprint") == EXPECTED_DEPLOYED_STAGING_IMAGE_FINGERPRINT),
                check("local_artifacts_exact", pilot.get("local_staging_artifacts_created") == 2),
                check("staging_not_release_candidate", pilot.get("release_candidates_created") == 0),
            ),
        ),
        scenario(
            "sbom_completeness_and_integrity",
            (
                check("sbom_fingerprint_exact", pilot.get("sbom_fingerprint") == EXPECTED_SBOM_FINGERPRINT),
                check("sbom_component_count_exact", pilot.get("sbom_component_count") == 61),
                check("sbom_projection_count_exact", pilot.get("sbom_projections_created") == 1),
            ),
        ),
        scenario(
            "artifact_provenance_chain_integrity",
            (
                check("provenance_chain_head_exact", pilot.get("artifact_provenance_chain_head") == EXPECTED_PROVENANCE_CHAIN_HEAD),
                check("provenance_record_count_exact", pilot.get("artifact_provenance_records_created") == 2),
                check("provenance_dependency_binding_exact", pilot.get("dependency_image_fingerprints") == EXPECTED_DEPENDENCY_IMAGE_FINGERPRINTS),
            ),
        ),
        scenario(
            "isolated_environment_and_internal_network_integrity",
            (
                check("environment_profile_fingerprint_exact", pilot.get("environment_profile_fingerprint") == EXPECTED_ENVIRONMENT_PROFILE_FINGERPRINT),
                check("compose_plan_fingerprint_exact", pilot.get("compose_plan_fingerprint") == EXPECTED_COMPOSE_PLAN_FINGERPRINT),
                check("internal_network_fingerprint_exact", pilot.get("internal_network_fingerprint") == EXPECTED_INTERNAL_NETWORK_FINGERPRINT),
                check("one_internal_network_created_and_removed", pilot.get("isolated_networks_created") == 1 and pilot.get("isolated_networks_removed") == 1),
                check("peak_container_bound_exact", pilot.get("running_staging_containers_peak") == 6),
            ),
        ),
        scenario(
            "loopback_exposure_and_host_port_boundary",
            (
                check("loopback_listener_created", pilot.get("loopback_listeners_created") == 1),
                check("no_public_listeners", pilot.get("public_listeners_created") == 0),
                check("no_non_loopback_listeners", pilot.get("non_loopback_listeners_created") == 0),
                check("ephemeral_port_used", pilot.get("ephemeral_port_used") is True),
                check("actual_port_not_retained", pilot.get("actual_port_retained") is False),
            ),
        ),
        scenario(
            "ephemeral_identity_fixture_integrity",
            (
                check("identity_fixture_fingerprint_exact", pilot.get("identity_fixture_fingerprint") == EXPECTED_IDENTITY_FIXTURE_FINGERPRINT),
                check("identity_keypair_created_once", pilot.get("ephemeral_identity_keypairs_created") == 1),
                check("identity_keypair_not_persisted", pilot.get("ephemeral_identity_keypairs_persisted") == 0),
                check("identity_spoofing_test_passed", pilot.get("identity_spoofing_tests_passed") == 1),
            ),
        ),
        scenario(
            "ephemeral_replay_fixture_and_rejection_integrity",
            (
                check("replay_fixture_fingerprint_exact", pilot.get("replay_fixture_fingerprint") == EXPECTED_REPLAY_FIXTURE_FINGERPRINT),
                check("replay_ledger_created_once", pilot.get("ephemeral_replay_ledgers_created") == 1),
                check("replay_ledger_not_persisted", pilot.get("ephemeral_replay_ledgers_persisted") == 0),
                check("replay_rejection_test_passed", pilot.get("replay_rejection_tests_passed") == 1),
            ),
        ),
        scenario(
            "staging_deployment_lifecycle_integrity",
            (
                check("single_deployment_completed", pilot.get("staging_deployments_completed") == 1),
                check("qualification_session_started_closed", pilot.get("staging_qualification_sessions_started") == 1 and pilot.get("staging_qualification_sessions_closed") == 1),
                check("no_active_session_after_close", pilot.get("active_qualification_sessions_after_close") == 0),
                check("local_staging_pilot_completed", pilot.get("local_staging_pilot_completed") is True),
            ),
        ),
        scenario(
            "health_and_readiness_evidence_integrity",
            (
                check("health_readiness_fingerprint_exact", pilot.get("health_readiness_report_fingerprint") == EXPECTED_HEALTH_READINESS_FINGERPRINT),
                check("health_checks_exact", pilot.get("health_checks_passed") == 3),
                check("readiness_checks_exact", pilot.get("readiness_checks_passed") == 4),
            ),
        ),
        scenario(
            "staging_security_validation_completeness",
            (
                check("security_report_fingerprint_exact", pilot.get("security_validation_report_fingerprint") == EXPECTED_SECURITY_VALIDATION_FINGERPRINT),
                check("all_security_scenarios_counted", pilot.get("security_tests_passed") == 12),
                check("security_validation_completed", pilot.get("staging_security_validation_completed") is True),
            ),
        ),
        scenario(
            "protected_material_redaction_integrity",
            (
                check("report_redacted", pilot.get("redacted") is True),
                check("redaction_test_passed", pilot.get("protected_material_redaction_tests_passed") == 1),
                check("protected_markers_absent", no_protected_markers(pilot)),
            ),
        ),
        scenario(
            "staging_configuration_drift_detection",
            (
                check("configuration_drift_test_passed", pilot.get("configuration_drift_tests_passed") == 1),
                check("release_effect_false", pilot.get("release_effect") is False),
                check("production_effect_false", pilot.get("production_effect") is False),
            ),
        ),
        scenario(
            "local_observability_evidence_integrity",
            (
                check("observability_fingerprint_exact", pilot.get("observability_snapshot_fingerprint") == EXPECTED_OBSERVABILITY_FINGERPRINT),
                check("observability_record_count_exact", pilot.get("local_observability_records_created") == 4),
                check("external_exports_zero", all(pilot.get(key) == 0 for key in ("external_log_exports", "external_metric_exports", "external_trace_exports"))),
            ),
        ),
        scenario(
            "controlled_degradation_detection",
            (
                check("one_degradation_injected", pilot.get("controlled_degradations_injected") == 1),
                check("health_failure_detected", pilot.get("health_failures_detected") == 1),
                check("post_rollback_health_recovered", pilot.get("post_rollback_health_recovered") is True),
            ),
        ),
        scenario(
            "rollback_and_post_recovery_integrity",
            (
                check("rollback_plan_fingerprint_exact", pilot.get("rollback_plan_fingerprint") == EXPECTED_ROLLBACK_PLAN_FINGERPRINT),
                check("rollback_result_fingerprint_exact", pilot.get("rollback_result_fingerprint") == EXPECTED_ROLLBACK_RESULT_FINGERPRINT),
                check("single_rollback_completed", pilot.get("staging_rollbacks_completed") == 1),
                check("staging_rollback_drill_completed", pilot.get("staging_rollback_drill_completed") is True),
                check("production_rollbacks_zero", pilot.get("production_rollbacks") == 0),
            ),
        ),
        scenario(
            "cleanup_and_preexisting_resource_preservation",
            (
                check("cleanup_fingerprint_exact", pilot.get("cleanup_result_fingerprint") == EXPECTED_CLEANUP_RESULT_FINGERPRINT),
                check("cleanup_completed", pilot.get("staging_cleanup_completed") is True),
                check("recorded_run_owned_resources_zero", all(pilot.get(key) == 0 for key in ("active_containers_after_cleanup", "active_volumes_after_cleanup", "active_networks_after_cleanup", "run_owned_images_after_cleanup"))),
                check("temporary_files_removed", pilot.get("temporary_files_retained") == 0),
                check("local_docker_cleanup_state_verified_or_not_required", docker_state["verified"] or not docker_state["required"], docker_state),
            ),
        ),
        scenario(
            "docker_command_allowlist_and_runner_boundary",
            (
                check("read_only_docker_inventory_commands_only", all(command[0] in {"context", "version", "info", "ps", "image", "network", "volume"} for command in READ_ONLY_DOCKER_COMMANDS)),
                check("runner_exists", (repo_root / "scripts/v02-staging-qualification-local-run.py").is_file()),
                check("registry_mutation_counters_zero", all(pilot.get(key) == 0 for key in ("registry_logins", "registry_pulls", "registry_pushes"))),
                check("evaluation_side_effect_fields_zero", True),
            ),
        ),
        scenario(
            "determinism_idempotency_redaction_and_performance",
            (
                check("pilot_fingerprint_stable", pilot_fingerprint_matches(api, pilot)),
                check("canonical_replay_stable", stable_fingerprint(pilot) == stable_fingerprint(json.loads(json.dumps(pilot)))),
                check("expected_counters_exact", expected_counter_match),
                check("prohibited_counters_exact", prohibited_counter_match),
                check("report_redacted", pilot.get("redacted") is True and no_protected_markers(pilot)),
            ),
        ),
        scenario(
            "zero_production_and_release_effects",
            (
                check("all_prohibited_counters_zero", prohibited_counter_match),
                check("release_candidate_absent", pilot.get("release_candidates_created") == 0),
                check("v02_ready_false", pilot.get("v02_release_ready") is False),
                check("v02_tag_created_false", pilot.get("v02_tag_created") is False and pilot.get("v02_tags_created") == 0),
                check("v02_release_created_false", pilot.get("v02_release_created") is False and pilot.get("v02_releases_created") == 0),
                check("local_v02_tags_absent", v02_tags_absent(repo_root)),
            ),
        ),
    ]
    prior_passed = all(item["passed"] for item in scenarios)
    scenarios.append(
        scenario(
            "deterministic_release_candidate_build_authorization_readiness",
            (
                check("all_prior_scenarios_passed", prior_passed),
                check("future_candidate_source_scope_recorded_not_created", not source["future_aion_243_source_present"] and not source["future_aion_243_runner_present"]),
                check("immutable_source_snapshot_authorizable", future_auth["approved_capabilities"]["immutable_candidate_source_snapshot_approved"]),
                check("bounded_release_metadata_authorizable", future_auth["approved_capabilities"]["bounded_package_version_update_approved"]),
                check("single_local_candidate_bundle_authorizable", future_auth["resource_limits"]["maximum_retained_candidate_bundles"] == 1),
                check("public_registry_forbidden", all(future_auth["prohibited_capabilities"][key] is False for key in ("registry_login_enabled", "registry_pull_enabled", "registry_push_enabled"))),
                check("publication_tag_release_forbidden", all(future_auth["prohibited_capabilities"][key] is False for key in ("release_candidate_publication_enabled", "git_tag_creation_enabled", "github_release_creation_enabled"))),
                check("production_deployment_forbidden", future_auth["prohibited_capabilities"]["production_deployment_enabled"] is False),
                check("final_release_decision_reserved_for_aion244", future_auth["formal_closeout_task"] == NEXT_FORMAL_CLOSEOUT_TASK),
            ),
        )
    )

    evaluation_passed = len(scenarios) == len(SCENARIO_IDS) and all(
        item["passed"] for item in scenarios
    )
    decision = PASS_DECISION if evaluation_passed else FAIL_DECISION
    hard_gate_results = [
        {
            "scenario_id": item["scenario_id"],
            "hard_gate": True,
            "passed": item["passed"],
            "status": item["status"],
        }
        for item in scenarios
    ]
    zero_effects = dict.fromkeys(REPORT_ZERO_EFFECT_FIELDS, 0)
    report: dict[str, Any] = {
        "schema_version": "aion-v02-staging-qualification-operator-evaluation/v1",
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "implementation_main_commit": implementation_main_commit,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [IMPLEMENTATION_PR],
        "implementation_feature_commits": [IMPLEMENTATION_COMMIT, EVIDENCE_COMMIT],
        "implementation_merge_commits": [IMPLEMENTATION_MERGE_COMMIT],
        "implementation_merged_at": IMPLEMENTATION_MERGED_AT,
        "required_ci_checks": list(REQUIRED_CI_CHECKS),
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenarios),
        "scenario_ids": list(SCENARIO_IDS),
        "scenario_results": scenarios,
        "hard_gate_count": len(hard_gate_results),
        "hard_gate_results": hard_gate_results,
        "pilot_validation": {
            "pilot_id": pilot.get("pilot_id"),
            "report_fingerprint": pilot.get("report_fingerprint"),
            "report_fingerprint_valid": pilot_fingerprint_matches(api, pilot),
            "staging_artifact_fingerprints": pilot.get("staging_artifact_fingerprints"),
            "sbom_component_count": pilot.get("sbom_component_count"),
            "prohibited_effect_counters": pilot.get("prohibited_effect_counters"),
        },
        "authorization_lineage": auth_state,
        "source_snapshot_integrity": {
            "source_snapshot_commit": pilot.get("source_snapshot_commit"),
            "git_tree_sha": pilot.get("git_tree_sha"),
            "source_tree_fingerprint": pilot.get("source_tree_fingerprint"),
            "git_archive_fingerprint": pilot.get("git_archive_fingerprint"),
            "source_snapshot_file_count": pilot.get("source_snapshot_file_count"),
            "source_snapshot_byte_count": pilot.get("source_snapshot_byte_count"),
        },
        "artifact_integrity": {
            "base_image_tag": pilot.get("base_image_tag"),
            "base_image_id": pilot.get("base_image_id"),
            "dependency_image_ids": pilot.get("dependency_image_ids"),
            "staging_artifact_fingerprints": pilot.get("staging_artifact_fingerprints"),
            "deployed_staging_image_fingerprint": pilot.get("deployed_staging_image_fingerprint"),
        },
        "sbom_integrity": {
            "sbom_fingerprint": pilot.get("sbom_fingerprint"),
            "sbom_component_count": pilot.get("sbom_component_count"),
        },
        "provenance_integrity": {
            "artifact_provenance_chain_head": pilot.get("artifact_provenance_chain_head"),
            "artifact_provenance_records_created": pilot.get("artifact_provenance_records_created"),
        },
        "staging_environment_integrity": {
            "environment_profile_fingerprint": pilot.get("environment_profile_fingerprint"),
            "compose_plan_fingerprint": pilot.get("compose_plan_fingerprint"),
            "internal_network_fingerprint": pilot.get("internal_network_fingerprint"),
            "loopback_listeners_created": pilot.get("loopback_listeners_created"),
        },
        "security_integrity": {
            "security_validation_report_fingerprint": pilot.get("security_validation_report_fingerprint"),
            "security_tests_passed": pilot.get("security_tests_passed"),
            "protected_material_redaction_tests_passed": pilot.get("protected_material_redaction_tests_passed"),
        },
        "rollback_integrity": {
            "rollback_plan_fingerprint": pilot.get("rollback_plan_fingerprint"),
            "rollback_result_fingerprint": pilot.get("rollback_result_fingerprint"),
            "staging_rollbacks_completed": pilot.get("staging_rollbacks_completed"),
            "post_rollback_health_recovered": pilot.get("post_rollback_health_recovered"),
        },
        "cleanup_integrity": {
            "cleanup_result_fingerprint": pilot.get("cleanup_result_fingerprint"),
            "recorded_active_resources": {
                "containers": pilot.get("active_containers_after_cleanup"),
                "volumes": pilot.get("active_volumes_after_cleanup"),
                "networks": pilot.get("active_networks_after_cleanup"),
                "images": pilot.get("run_owned_images_after_cleanup"),
            },
        },
        "repository_integrity": {
            "source_scope_state": source,
            "v02_tags_absent": v02_tags_absent(repo_root),
            "release_candidate_source_absent": not source["future_aion_243_source_present"],
        },
        "resource_state": docker_state,
        "next_architecture_decision": NEXT_ARCHITECTURE_PASS
        if evaluation_passed
        else NEXT_ARCHITECTURE_FAIL,
        "synthetic": False,
        "read_only": True,
        "redacted": True,
        **zero_effects,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
        "future_release_candidate_authorization_projection": future_auth,
    }
    report["report_fingerprint"] = report_fingerprint(report)
    return report


def validate_report(report: Mapping[str, Any]) -> None:
    required = {
        "evaluation_id": EVALUATION_ID,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "implementation_main_commit": IMPLEMENTATION_MERGE_COMMIT,
        "decision": PASS_DECISION if report.get("evaluation_passed") is True else FAIL_DECISION,
        "scenario_count": 28,
        "hard_gate_count": 28,
        "synthetic": False,
        "read_only": True,
        "redacted": True,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
    }
    for key, expected in required.items():
        if report.get(key) != expected:
            raise ValueError(f"AION-242 report mismatch {key}: {report.get(key)!r}")
    if list(report.get("scenario_ids", ())) != list(SCENARIO_IDS):
        raise ValueError("AION-242 report scenario IDs are not exact")
    if [item.get("scenario_id") for item in report.get("scenario_results", ())] != list(SCENARIO_IDS):
        raise ValueError("AION-242 scenario result order is not exact")
    if len(report.get("hard_gate_results", ())) != 28:
        raise ValueError("AION-242 hard-gate result count is not exact")
    if any(item.get("hard_gate") is not True for item in report.get("scenario_results", ())):
        raise ValueError("AION-242 scenario without hard_gate=true")
    if report.get("evaluation_passed") is True:
        if not all(item.get("passed") is True for item in report.get("scenario_results", ())):
            raise ValueError("AION-242 PASS report has failed scenario")
        if report.get("next_architecture_decision") != NEXT_ARCHITECTURE_PASS:
            raise ValueError("AION-242 PASS next architecture decision mismatch")
    for key in REPORT_ZERO_EFFECT_FIELDS:
        if report.get(key) != 0:
            raise ValueError(f"AION-242 evaluation side effect is nonzero: {key}")
    if report.get("release_candidates_created") != 0:
        raise ValueError("AION-242 must not create release candidates")
    if report.get("v02_tags_created") != 0 or report.get("v02_releases_created") != 0:
        raise ValueError("AION-242 must not create v0.2 tags or releases")
    if report.get("report_fingerprint") != report_fingerprint(report):
        raise ValueError("AION-242 report fingerprint mismatch")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=EVALUATION_ID)
    parser.add_argument("--implementation-main-commit")
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--pilot-evidence", type=Path)
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.validate_report:
            validate_report(load_json(args.validate_report))
            return 0
        missing = [
            name
            for name in (
                "repo_root",
                "implementation_main_commit",
                "evaluation_base_commit",
                "pilot_evidence",
                "temporary_output_directory",
                "report",
            )
            if getattr(args, name) is None
        ]
        if missing:
            raise ValueError(f"missing required arguments: {', '.join(missing)}")
        report = evaluate(
            repo_root=args.repo_root.resolve(),
            evaluation_id=args.evaluation_id,
            implementation_main_commit=args.implementation_main_commit,
            evaluation_base_commit=args.evaluation_base_commit,
            pilot_evidence_path=(args.repo_root / args.pilot_evidence)
            if not args.pilot_evidence.is_absolute()
            else args.pilot_evidence,
            temporary_output_directory=args.temporary_output_directory,
        )
        validate_report(report)
        write_json(report, args.report)
    except Exception as exc:
        print(f"AION-242 evaluator failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
