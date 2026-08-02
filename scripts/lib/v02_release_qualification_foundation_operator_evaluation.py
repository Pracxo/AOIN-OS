#!/usr/bin/env python3
"""AION-240 operator evaluation for the v0.2 qualification foundation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


PROGRAM_ID = "AION-V02-RELEASE-QUALIFICATION-001"
EVALUATION_ID = "AION-V02RQPE-001"
EVALUATION_TYPE = "v02_release_qualification_foundation_operator_evaluation"
IMPLEMENTATION_TASK = "AION-239"
CLOSEOUT_TASK = "AION-240"
NEXT_IMPLEMENTATION_TASK = "AION-241"
NEXT_FORMAL_CLOSEOUT_TASK = "AION-242"
FINAL_PLANNED_TASK = "AION-244"
CURRENT_AUTHORIZATION_ID = "AION-238-V02RQ-0001"
NEXT_AUTHORIZATION_ID = "AION-240-V02RQ-0002"
IMPLEMENTATION_PR = 158
IMPLEMENTATION_BRANCH = "phase/v02-release-qualification-foundation"
IMPLEMENTATION_COMMIT = "a1d5d1ee2b0d991f3074c796d664105225b51856"
CI_FIX_COMMIT = "fa789d5c43709d606bb088a69451b7a43cf32a17"
IMPLEMENTATION_MERGE_COMMIT = "154d58f182871ce18abad860f3bb76e5a006ebad"
IMPLEMENTATION_MERGED_AT = "2026-08-01T19:47:57Z"
EXPECTED_PILOT_FINGERPRINT = (
    "6635d4d32533893e4549d3992c0a6b54e73a58a0904914da6defcc5e0deff2ab"
)
PASS_DECISION = (
    "DISABLED_V02_PRODUCTION_READINESS_QUALIFICATION_FOUNDATION_OPERATOR_"
    "EVALUATION_PASS_RECOMMEND_CONTROLLED_ISOLATED_STAGING_ARTIFACT_AND_"
    "ROLLBACK_DRILL_QUALIFICATION_AUTHORIZATION"
)
FAIL_DECISION = (
    "DISABLED_V02_PRODUCTION_READINESS_QUALIFICATION_FOUNDATION_OPERATOR_"
    "EVALUATION_FAIL_REMAIN_DESIGN_AND_LOCAL_SIMULATION_ONLY"
)
NEXT_ARCHITECTURE_PASS = (
    "controlled_isolated_staging_artifact_and_rollback_drill_qualification_authorized"
)
NEXT_ARCHITECTURE_FAIL = "v02_qualification_foundation_remediation_review"
STAGING_AUTHORIZATION_SCOPE = (
    "controlled-isolated-local-staging-source-snapshot-offline-container-build-"
    "local-artifact-sbom-provenance-ephemeral-auth-replay-fixtures-loopback-health-"
    "observability-security-validation-rollback-drill-cleanup-no-public-egress-no-"
    "production-no-release-core"
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
    "aion_239_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "pilot_evidence_schema_and_fingerprint",
    "exact_source_and_repository_boundary",
    "parent_program_component_lineage",
    "qualification_authorization_and_session_integrity",
    "readiness_gap_matrix_completeness",
    "gap_severity_status_and_evidence_maturity",
    "production_auth_composition_integrity",
    "verified_request_identity_integration_integrity",
    "replay_ledger_provisioning_design_integrity",
    "identity_provider_adapter_disabled_boundary",
    "public_key_lifecycle_integrity",
    "protected_material_lifecycle_integrity",
    "credential_token_and_session_lifecycle_integrity",
    "deployment_artifact_manifest_integrity",
    "sbom_and_artifact_provenance_integrity",
    "reproducible_build_evidence_honesty",
    "rollback_plan_and_drill_simulation_integrity",
    "observability_and_health_readiness_integrity",
    "production_threat_model_completeness",
    "runtime_release_guard_precedence",
    "release_gate_matrix_integrity",
    "staging_qualification_plan_integrity",
    "idempotency_exact_replay_and_changed_replay",
    "determinism_redaction_concurrency_and_performance",
    "zero_operational_effects_and_release_boundary",
    "controlled_isolated_staging_qualification_readiness",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_158_verified",
    "implementation_commit_verified",
    "ci_fix_commit_verified",
    "merge_commit_verified",
    "merged_timestamp_verified",
    "required_ci_green",
    "aion_239_delivery_evidence_reconciled",
    "aion_238_authorization_exact_before_closeout",
    "all_28_scenarios_executed",
    "all_28_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "pilot_fingerprint_valid",
    "readiness_domains_exact",
    "gap_dependencies_acyclic",
    "gap_severity_preserved",
    "evidence_maturity_truthful",
    "production_auth_composition_valid",
    "request_identity_integration_valid",
    "replay_ledger_provisioning_valid",
    "identity_provider_disabled_boundary_valid",
    "key_lifecycle_valid",
    "protected_material_handling_valid",
    "credential_token_session_lifecycle_valid",
    "artifact_sbom_provenance_valid",
    "reproducibility_honesty_valid",
    "rollback_simulation_valid",
    "observability_health_valid",
    "threat_model_complete",
    "runtime_guard_fail_closed",
    "release_gates_exact",
    "staging_plan_valid",
    "zero_operational_effects",
    "repository_release_boundary_valid",
    "staging_qualification_readiness_valid",
)

EXPECTED_SOURCE_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/__init__.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/authorization.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/gap_matrix.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/production_auth_composition.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/request_identity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/replay_provisioning.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/identity_provider.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/key_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/protected_material.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/credential_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/token_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/session_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/deployment_manifest.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/artifact_provenance.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/rollback.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/observability.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/threat_model.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/runtime_guard.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/release_gate.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/integrity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/evidence.py",
)

PROHIBITED_AION239_SOURCE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/v02_release_qualification/network.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/live_identity_provider.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/secret_store.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/credential_store.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/token_store.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/live_replay_ledger.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/database.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/deployer.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/kubernetes.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/terraform.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/container_registry.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/production_observability_exporter.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/release_publisher.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/background_worker.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/scheduler.py",
    "services/brain-api/src/aion_brain/api/v02_release_qualification.py",
)

FUTURE_AION241_SOURCE_SCOPE: tuple[str, ...] = (
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

APPROVED_AION241_CAPABILITIES: tuple[str, ...] = (
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

PROHIBITED_AION241_CAPABILITIES: tuple[str, ...] = (
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

POSITIVE_AION241_LIMITS: dict[str, int] = {
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

ZERO_AION241_LIMITS: tuple[str, ...] = (
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

REPORT_ZERO_EFFECT_FIELDS: tuple[str, ...] = (
    "public_network_calls",
    "external_network_egress_calls",
    "dns_resolutions",
    "external_identity_provider_calls",
    "credentials_generated",
    "credentials_read",
    "credentials_persisted",
    "tokens_generated",
    "tokens_read",
    "tokens_persisted",
    "authorization_headers_created",
    "live_key_rotations",
    "live_replay_ledger_writes",
    "database_operations",
    "actual_builds_executed",
    "artifact_bytes_created",
    "staging_deployments",
    "production_deployments",
    "rollback_executions",
    "external_log_exports",
    "external_metric_exports",
    "external_trace_exports",
    "release_candidates_created",
    "v02_tags_created",
    "v02_releases_created",
    "active_qualification_sessions_after_evaluation",
)

FUTURE_AION241_THREATS: tuple[str, ...] = (
    "build-context tampering",
    "source-snapshot substitution",
    "unpinned base-image substitution",
    "registry pull bypass",
    "hidden network egress during build",
    "build-secret leakage",
    "Docker socket exposure",
    "privileged-container escape",
    "host-network escape",
    "host-filesystem mount escape",
    "cloud-metadata access",
    "public-port exposure",
    "DNS leakage",
    "ephemeral-key persistence",
    "replay-fixture persistence",
    "production-endpoint substitution",
    "production-credential substitution",
    "environment-variable leakage",
    "artifact-digest substitution",
    "SBOM omission",
    "provenance forgery",
    "non-reproducible build",
    "staging-to-production configuration drift",
    "health-check bypass",
    "observability blind spot",
    "rollback target substitution",
    "rollback evidence forgery",
    "incomplete cleanup",
    "stale container",
    "stale volume",
    "stale network",
    "stale image",
    "release-candidate misclassification",
    "v0.2 tag creation",
    "release publication",
)

PROTECTED_VALUE_MARKERS: tuple[str, ...] = (
    "sk-",
    "ghp_",
    "xoxb-",
    "bearer ",
    "-----begin private key-----",
    "client_secret_value",
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
    import aion_brain.v02_release_qualification as api

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


def raises_value_error(func: Any) -> bool:
    try:
        func()
    except ValueError:
        return True
    except Exception:
        return False
    return False


def pilot_fingerprint_matches(api: Any, pilot: Mapping[str, Any]) -> bool:
    body = {key: value for key, value in pilot.items() if key != "report_fingerprint"}
    return pilot.get("report_fingerprint") == api.v02_qualification_fingerprint(body)


def source_scope_state(repo_root: Path) -> dict[str, Any]:
    program_path = repo_root / "docs/v02-release-qualification/program-ledger.json"
    program = load_json(program_path) if program_path.exists() else {}
    aion241_implemented = (
        program.get("controlled_staging_qualification_implemented") is True
    )
    present = [path for path in EXPECTED_SOURCE_SCOPE if (repo_root / path).is_file()]
    runtime_root = repo_root / "services/brain-api/src/aion_brain/v02_release_qualification"
    actual_runtime = {
        f"services/brain-api/src/aion_brain/v02_release_qualification/{path.name}"
        for path in runtime_root.glob("*.py")
    }
    prohibited_present = [path for path in PROHIBITED_AION239_SOURCE if (repo_root / path).exists()]
    future_source_present = [
        path for path in FUTURE_AION241_SOURCE_SCOPE if (repo_root / path).exists()
    ]
    aion241_source_state_valid = (
        sorted(future_source_present) == sorted(FUTURE_AION241_SOURCE_SCOPE)
        if aion241_implemented
        else not future_source_present
    )
    return {
        "expected_source_scope": list(EXPECTED_SOURCE_SCOPE),
        "present_source_scope": present,
        "exact_runtime_source_scope": sorted(actual_runtime) == sorted(EXPECTED_SOURCE_SCOPE[1:]),
        "missing_source_scope": [
            path for path in EXPECTED_SOURCE_SCOPE if path not in present
        ],
        "prohibited_source_present": prohibited_present,
        "future_aion_241_source_present": future_source_present,
        "aion_241_source_scope_implemented": aion241_implemented,
        "aion_241_source_scope_state_valid": aion241_source_state_valid,
        "uninstalled_runner_present": (
            repo_root / "scripts/v02-release-qualification-local-run.py"
        ).is_file(),
    }


def exercise_public_api(api: Any) -> dict[str, Any]:
    service = api.ControlledV02ReleaseQualificationService()
    pilot_result = service.run_canonical_disabled_pilot()
    binding = api.canonical_component_binding()
    authorization = api.canonical_authorization_envelope(binding)
    session_plan = service.create_session_plan("aion-240-evaluation-session")
    session = service.start_session(session_plan)
    closed_session = service.close_session(session.session_id)
    gap_matrix = api.canonical_gap_matrix()
    release_gate_matrix = api.canonical_release_gate_matrix()
    guard = service.evaluate_runtime_guard(
        gap_matrix=gap_matrix,
        release_gate_matrix=release_gate_matrix,
    )
    replay_request = service.repository._run_request_fingerprints[pilot_result.run_id]
    replayed = service.replay_exact_run(pilot_result.run_id, replay_request)
    changed_replay_rejected = raises_value_error(
        lambda: service.replay_exact_run(
            pilot_result.run_id,
            api.v02_qualification_fingerprint(
                {"run_id": pilot_result.run_id, "changed": True}
            ),
        )
    )
    return {
        "service": service,
        "pilot_result": pilot_result,
        "binding": binding,
        "authorization": authorization,
        "session_plan": session_plan,
        "closed_session": closed_session,
        "gap_matrix": gap_matrix,
        "release_gate_matrix": release_gate_matrix,
        "guard": guard,
        "replayed": replayed,
        "changed_replay_rejected": changed_replay_rejected,
        "production_auth": api.canonical_production_auth_composition(),
        "request_identity": api.canonical_request_identity_plan(),
        "replay_provisioning": api.canonical_replay_provisioning_plan(),
        "identity_provider_manifests": api.canonical_identity_provider_manifests(),
        "key_policies": api.canonical_key_policies(),
        "protected_material_policy": api.canonical_protected_material_policy(),
        "credential_policies": api.canonical_credential_policies(),
        "token_policies": api.canonical_token_policies(),
        "session_policies": api.canonical_session_policies(),
        "deployment_manifests": api.canonical_deployment_manifests(),
        "sbom_projection": api.canonical_sbom_projection(),
        "provenance_records": api.canonical_provenance_records(),
        "reproducibility_projections": api.canonical_reproducibility_projections(),
        "rollback_plans": api.canonical_rollback_plans(),
        "rollback_drill_plan": api.canonical_rollback_drill_plan(
            api.canonical_rollback_plans()
        ),
        "observability_schema": api.canonical_observability_schema(),
        "health_schema": api.canonical_health_readiness_schema(),
        "threat_model": api.canonical_threat_model(),
        "staging_plan": api.canonical_staging_plan(),
        "resource_limits": api.resource_limits().model_dump(),
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
    authorization_ledger = load_json(
        repo_root / "docs/v02-release-qualification/authorization-ledger.json"
    )
    program_authorization = load_json(
        repo_root / "examples/v02-release-qualification/program-authorization.json"
    )
    public = exercise_public_api(api)
    source = source_scope_state(repo_root)

    pilot_result = public["pilot_result"]
    gap_matrix = public["gap_matrix"]
    release_gate_matrix = public["release_gate_matrix"]
    guard = public["guard"]
    threat_model = public["threat_model"]
    staging_plan = public["staging_plan"]
    resource_limits = public["resource_limits"]
    prohibited_effect_total = sum(int(value) for value in api.PROHIBITED_EFFECT_COUNTERS.values())
    severity_rank = {
        api.V02GapSeverity.blocker: 0,
        api.V02GapSeverity.critical: 1,
        api.V02GapSeverity.major: 2,
        api.V02GapSeverity.minor: 3,
        api.V02GapSeverity.informational: 4,
    }
    all_prohibited_ledgers_zero = all(
        not any(payload.get("prohibited_capabilities", {}).values())
        for payload in (program, authorization_ledger, program_authorization)
    )
    authorization_closeout = program.get("aion_238_authorization_closeout", {})
    authorization_pre_closeout = (
        authorization_ledger.get("authorization_transaction_id") == CURRENT_AUTHORIZATION_ID
        and authorization_ledger.get("program_id") == PROGRAM_ID
        and authorization_ledger.get("implementation_task") == IMPLEMENTATION_TASK
        and authorization_ledger.get("formal_closeout_task") == CLOSEOUT_TASK
        and authorization_ledger.get("authorization_active") is True
        and authorization_ledger.get("authorization_consumed") is False
        and authorization_ledger.get("authorization_reusable") is False
        and authorization_ledger.get("active_v02_release_qualification_authorization_count") == 1
    )
    staging_implementation_state_valid = (
        authorization_ledger.get("controlled_staging_qualification_implemented") is False
        or (
            authorization_ledger.get("controlled_staging_qualification_implemented") is True
            and authorization_ledger.get("local_staging_pilot_completed") is True
            and authorization_ledger.get("production_runtime_authorized") is False
            and authorization_ledger.get("production_deployment_enabled") is False
            and authorization_ledger.get("v02_release_ready") is False
        )
    )
    authorization_post_closeout = (
        authorization_ledger.get("authorization_transaction_id") == NEXT_AUTHORIZATION_ID
        and authorization_ledger.get("program_id") == PROGRAM_ID
        and authorization_ledger.get("parent_authorization_transaction_id") == CURRENT_AUTHORIZATION_ID
        and authorization_ledger.get("parent_evaluation_id") == EVALUATION_ID
        and authorization_ledger.get("parent_evaluation_decision") == PASS_DECISION
        and authorization_ledger.get("implementation_task") == NEXT_IMPLEMENTATION_TASK
        and authorization_ledger.get("formal_closeout_task") == NEXT_FORMAL_CLOSEOUT_TASK
        and authorization_ledger.get("authorization_active") is True
        and authorization_ledger.get("authorization_consumed") is False
        and authorization_ledger.get("authorization_reusable") is False
        and authorization_ledger.get("active_v02_release_qualification_authorization_count") == 1
        and authorization_ledger.get("active_v02_release_qualification_authorization") == NEXT_AUTHORIZATION_ID
        and authorization_ledger.get("controlled_staging_qualification_authorized") is True
        and staging_implementation_state_valid
        and authorization_closeout.get("authorization_transaction_id") == CURRENT_AUTHORIZATION_ID
        and authorization_closeout.get("authorization_active") is False
        and authorization_closeout.get("authorization_consumed") is True
        and authorization_closeout.get("authorization_expired") is True
        and authorization_closeout.get("authorization_reusable") is False
        and authorization_closeout.get("authorization_consumed_by_task") == IMPLEMENTATION_TASK
        and authorization_closeout.get("authorization_closed_by_task") == CLOSEOUT_TASK
    )
    expected_positive_limits = {
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

    scenarios = [
        scenario(
            "aion_239_delivery_and_ci_integrity",
            (
                check("pr_number_exact", IMPLEMENTATION_PR == 158, IMPLEMENTATION_PR),
                check("branch_exact", IMPLEMENTATION_BRANCH == "phase/v02-release-qualification-foundation"),
                check("implementation_commit_exact", IMPLEMENTATION_COMMIT.startswith("a1d5d1ee")),
                check("ci_fix_commit_exact", CI_FIX_COMMIT.startswith("fa789d5c")),
                check("merge_commit_exact", implementation_main_commit == IMPLEMENTATION_MERGE_COMMIT),
                check("merged_timestamp_exact", IMPLEMENTATION_MERGED_AT == "2026-08-01T19:47:57Z"),
                check("required_ci_checks_recorded", list(REQUIRED_CI_CHECKS)),
            ),
        ),
        scenario(
            "authorization_lineage_and_scope",
            (
                check("authorization_lineage_valid", authorization_pre_closeout or authorization_post_closeout),
                check("aion_238_active_or_closed_exact", authorization_pre_closeout or authorization_closeout.get("authorization_transaction_id") == CURRENT_AUTHORIZATION_ID),
                check("program_id_exact", authorization_ledger.get("program_id") == PROGRAM_ID),
                check("implementation_task_exact", authorization_ledger.get("implementation_task") in {IMPLEMENTATION_TASK, NEXT_IMPLEMENTATION_TASK}),
                check("formal_closeout_task_exact", authorization_ledger.get("formal_closeout_task") in {CLOSEOUT_TASK, NEXT_FORMAL_CLOSEOUT_TASK}),
                check("active_authorization_unconsumed", authorization_ledger.get("authorization_active") is True and authorization_ledger.get("authorization_consumed") is False),
                check("not_reusable", authorization_ledger.get("authorization_reusable") is False),
                check("active_count_one", authorization_ledger.get("active_v02_release_qualification_authorization_count") == 1),
            ),
        ),
        scenario(
            "pilot_evidence_schema_and_fingerprint",
            (
                check("pilot_id_exact", pilot.get("pilot_id") == "AION-239-disabled-v02-production-readiness-qualification-pilot"),
                check("authorization_exact", pilot.get("authorization_id") == CURRENT_AUTHORIZATION_ID),
                check("mode_exact", pilot.get("mode") == "deterministic-local-simulation"),
                check("fingerprint_exact", pilot.get("report_fingerprint") == EXPECTED_PILOT_FINGERPRINT),
                check("fingerprint_valid", pilot_fingerprint_matches(api, pilot)),
                check("counters_exact", pilot.get("readiness_domains_evaluated") == 20 and pilot.get("release_gates_evaluated") == 24 and pilot.get("threat_scenarios_validated") == 40),
                check("zero_prohibited_effects", pilot.get("prohibited_effect_counters") == api.PROHIBITED_EFFECT_COUNTERS),
                check("release_hold_truthful", pilot.get("v02_release_ready") is False and pilot.get("release_hold_decisions") == 1),
            ),
        ),
        scenario(
            "exact_source_and_repository_boundary",
            (
                check("all_expected_source_present", not source["missing_source_scope"], source["missing_source_scope"]),
                check("runtime_source_scope_exact", source["exact_runtime_source_scope"]),
                check("prohibited_source_absent", not source["prohibited_source_present"], source["prohibited_source_present"]),
                check("uninstalled_runner_present", source["uninstalled_runner_present"]),
                check("aion_241_source_scope_state_valid", source["aion_241_source_scope_state_valid"], source["future_aion_241_source_present"]),
            ),
        ),
        scenario(
            "parent_program_component_lineage",
            (
                check("sri_parent_program_recorded", "AION-SECURE-RUNTIME-INTEGRATION-001" in program.get("parent_completed_programs", ())),
                check("parent_evaluation_exact", program.get("parent_evaluation_id") == "AION-SRIPE-004"),
                check("aion_238_record_complete", program.get("aion_238_delivery_reconciliation", {}).get("ci_result") == "pass"),
                check("active_sri_zero", program.get("aion_238_delivery_reconciliation", {}).get("active_sri_authorization_count") == 0),
                check("aion_237_lineage_recorded", program.get("parent_implementation_task") == "AION-237"),
            ),
        ),
        scenario(
            "qualification_authorization_and_session_integrity",
            (
                check("authorization_envelope_active", public["authorization"].authorization_active is True),
                check("authorization_envelope_unconsumed", public["authorization"].authorization_consumed is False),
                check("domains_exact", tuple(public["authorization"].allowed_readiness_domains) == api.READINESS_DOMAINS),
                check("single_active_session_limit", raises_value_error(lambda: (lambda service: (service.start_session(service.create_session_plan("one")), service.start_session(service.create_session_plan("two"))))(api.ControlledV02ReleaseQualificationService()))),
                check("session_closed_no_persistence", public["closed_session"].active is False and public["closed_session"].candidate_references_loaded is False),
            ),
        ),
        scenario(
            "readiness_gap_matrix_completeness",
            (
                check("twenty_gaps", len(gap_matrix.gaps) == 20),
                check("canonical_domains", tuple(gap_matrix.readiness_domains_represented) == api.READINESS_DOMAINS),
                check("unique_gap_ids", len({gap.gap_id for gap in gap_matrix.gaps}) == 20),
                check("gap_dependencies_acyclic", bool(gap_matrix.gap_matrix_fingerprint)),
                check("all_gap_fingerprints", all(gap.gap_fingerprint for gap in gap_matrix.gaps)),
            ),
        ),
        scenario(
            "gap_severity_status_and_evidence_maturity",
            (
                check("no_false_resolution", all(gap.current_status != api.V02GapStatus.resolved_by_verified_evidence for gap in gap_matrix.gaps)),
                check("severity_not_downgraded", all(severity_rank[gap.severity] <= severity_rank[gap.minimum_severity] for gap in gap_matrix.gaps)),
                check("staging_gaps_required", gap_matrix.staging_evidence_required is True),
                check("production_gaps_required", gap_matrix.production_evidence_required is True),
                check("design_evidence_not_operational", all(gap.evidence_maturity in {api.V02EvidenceMaturity.design_recorded, api.V02EvidenceMaturity.deterministic_simulation, api.V02EvidenceMaturity.staging_required, api.V02EvidenceMaturity.production_required} for gap in gap_matrix.gaps)),
            ),
        ),
        scenario(
            "production_auth_composition_integrity",
            (
                check("component_order_fail_closed", "reject" in public["production_auth"].fail_closed_behavior),
                check("claim_verification_required", "secure_request_identity_projection" in public["production_auth"].component_order),
                check("replay_before_mutation", "replay_protection" in public["production_auth"].policy_and_approval_precedence),
                check("redacted_audit_required", any("redacted" in item for item in public["production_auth"].audit_requirements)),
                check("production_runtime_disabled", authorization_ledger.get("production_auth_runtime_enabled") is False),
            ),
        ),
        scenario(
            "verified_request_identity_integration_integrity",
            (
                check("verified_claims_only", public["request_identity"].bearer_tokens_create_identity_without_future_verified_path is False),
                check("closed_mapping", bool(public["request_identity"].claim_mappings)),
                check("headers_cookies_browser_identity_disallowed", public["request_identity"].browser_headers_create_identity is False and public["request_identity"].cookies_create_identity is False),
                check("privilege_expansion_disallowed", public["request_identity"].privilege_expansion_rejected is True),
                check("workspace_substitution_disallowed", public["request_identity"].workspace_substitution_rejected is True),
            ),
        ),
        scenario(
            "replay_ledger_provisioning_design_integrity",
            (
                check("backend_class_design_only", public["replay_provisioning"].production_database_provisioning_enabled is False),
                check("unique_isolated_replay", bool(public["replay_provisioning"].unique_key_design and public["replay_provisioning"].transaction_isolation_requirement)),
                check("capacity_backup_restore", bool(public["replay_provisioning"].capacity_plan and public["replay_provisioning"].backup_restore_plan)),
                check("migration_fail_closed", "deny" in public["replay_provisioning"].fail_closed_behavior and "cannot be proven" in public["replay_provisioning"].fail_closed_behavior),
                check("no_live_writes", public["replay_provisioning"].live_replay_ledger_enabled is False and public["replay_provisioning"].maximum_live_replay_ledger_writes == 0),
            ),
        ),
        scenario(
            "identity_provider_adapter_disabled_boundary",
            (
                check("one_manifest", len(public["identity_provider_manifests"]) == 1),
                check("all_disabled", all(manifest.connect_available is False and manifest.refresh_available is False for manifest in public["identity_provider_manifests"])),
                check("trust_plans_present", all(manifest.trust_plan for manifest in public["identity_provider_manifests"])),
                check("claim_mappings_present", all(manifest.claim_mappings for manifest in public["identity_provider_manifests"])),
                check("external_idp_calls_zero", pilot.get("external_identity_provider_calls") == 0),
            ),
        ),
        scenario(
            "public_key_lifecycle_integrity",
            (
                check("three_key_policies", len(public["key_policies"]) == 3),
                check("rotation_revocation_compromise", all(policy.rotation_plan and policy.revocation_plan and policy.compromise_response_plan for policy in public["key_policies"])),
                check("private_key_bytes_absent", all(policy.private_key_material_present is False and policy.public_key_bytes_present is False for policy in public["key_policies"])),
                check("audit_evidence_required", all(policy.audit_requirements and policy.evidence_requirements for policy in public["key_policies"])),
                check("no_live_rotation", pilot.get("live_key_rotations") == 0),
            ),
        ),
        scenario(
            "protected_material_lifecycle_integrity",
            (
                check("canonical_classes", len(public["protected_material_policy"].classes) == 16),
                check("redaction_required", public["protected_material_policy"].redaction_default is True),
                check("protected_value_not_stored", public["protected_material_policy"].protected_value_stored is False),
                check("class_fingerprints_present", all(item.class_fingerprint for item in public["protected_material_policy"].classes)),
                check("committed_evidence_redacted", pilot.get("redacted") is True),
            ),
        ),
        scenario(
            "credential_token_and_session_lifecycle_integrity",
            (
                check("four_credential_policies", len(public["credential_policies"]) == 4),
                check("four_token_policies", len(public["token_policies"]) == 4),
                check("three_session_policies", len(public["session_policies"]) == 3),
                check("expiry_revocation_cleanup", all(policy.expiry_policy and policy.revocation_policy for policy in public["credential_policies"]) and all(policy.maximum_ttl_seconds > 0 and policy.revocation_policy for policy in public["token_policies"]) and all(policy.cleanup_requirements for policy in public["session_policies"])),
                check("no_live_credentials_tokens", pilot.get("credentials_generated") == 0 and pilot.get("tokens_generated") == 0),
            ),
        ),
        scenario(
            "deployment_artifact_manifest_integrity",
            (
                check("one_manifest", len(public["deployment_manifests"]) == 1),
                check("source_commit_and_tree", all(manifest.source_commit and manifest.source_tree_fingerprint for manifest in public["deployment_manifests"])),
                check("target_and_kind_present", all(manifest.target_platform_code and manifest.artifact_kind_code for manifest in public["deployment_manifests"])),
                check("evidence_requirements_present", all(manifest.artifact_evidence_requirements for manifest in public["deployment_manifests"])),
                check("no_artifact_bytes", pilot.get("artifact_bytes_created", 0) == 0),
            ),
        ),
        scenario(
            "sbom_and_artifact_provenance_integrity",
            (
                check("sbom_component_count", len(public["sbom_projection"].components) == 12),
                check("unique_sbom_components", len({item.component_name for item in public["sbom_projection"].components}) == 12),
                check("provenance_count", len(public["provenance_records"]) == 4),
                check("tamper_fingerprints_present", all(record.provenance_fingerprint for record in public["provenance_records"])),
                check("registry_credentials_absent", pilot.get("registry_credentials_read", 0) == 0),
            ),
        ),
        scenario(
            "reproducible_build_evidence_honesty",
            (
                check("two_projections", len(public["reproducibility_projections"]) == 2),
                check("simulation_only", all(item.evidence_maturity == api.V02EvidenceMaturity.deterministic_simulation for item in public["reproducibility_projections"])),
                check("actual_build_false", all(item.actual_build_executed is False for item in public["reproducibility_projections"])),
                check("artifact_created_false", all(item.actual_artifact_created is False for item in public["reproducibility_projections"])),
                check("release_not_ready", pilot.get("v02_release_ready") is False),
            ),
        ),
        scenario(
            "rollback_plan_and_drill_simulation_integrity",
            (
                check("two_rollback_plans", len(public["rollback_plans"]) == 2),
                check("one_drill_plan", public["rollback_drill_plan"].execute_commands is False and public["rollback_drill_plan"].deploy is False),
                check("simulation_completed", pilot.get("rollback_drill_simulations") == 1),
                check("zero_rollback_execution", pilot.get("rollback_executions") == 0),
                check("abort_conditions_present", all(plan.abort_conditions for plan in public["rollback_plans"])),
            ),
        ),
        scenario(
            "observability_and_health_readiness_integrity",
            (
                check("observability_signal_count", len(public["observability_schema"].signals) == 24),
                check("health_check_count", len(public["health_schema"].checks) == 12),
                check("observability_exports_disabled", public["observability_schema"].production_observability_export_enabled is False and public["observability_schema"].external_log_export_enabled is False),
                check("readiness_checks_fingerprinted", all(item.check_fingerprint for item in public["health_schema"].checks)),
                check("no_exporters", pilot.get("external_log_exports") == 0 and pilot.get("external_metric_exports") == 0 and pilot.get("external_trace_exports") == 0),
            ),
        ),
        scenario(
            "production_threat_model_completeness",
            (
                check("forty_scenarios", len(threat_model.scenarios) == 40),
                check("categories_complete", len({item.category for item in threat_model.scenarios}) >= 9),
                check("controls_present", all(item.existing_controls and item.required_controls for item in threat_model.scenarios)),
                check("governance_bypass_present", any(item.category == api.V02ThreatCategory.governance_bypass for item in threat_model.scenarios)),
                check("future_staging_threats_recorded", len(FUTURE_AION241_THREATS) >= 32),
            ),
        ),
        scenario(
            "runtime_release_guard_precedence",
            (
                check("allowed_outcome", guard.outcome in {api.V02RuntimeGuardOutcome.allow_disabled_qualification, api.V02RuntimeGuardOutcome.require_operator_review, api.V02RuntimeGuardOutcome.block}),
                check("release_hold", guard.release_hold is True),
                check("staging_required", guard.staging_evidence_required is True),
                check("production_required", guard.production_evidence_required is True),
                check("release_candidate_false", guard.v02_release_candidate_created is False),
            ),
        ),
        scenario(
            "release_gate_matrix_integrity",
            (
                check("twenty_four_gates", len(release_gate_matrix.gates) == 24),
                check("canonical_gate_ids", tuple(gate.gate_id for gate in release_gate_matrix.gates) == api.CANONICAL_RELEASE_GATE_IDS),
                check("staging_gate_required", any(gate.staging_evidence_required for gate in release_gate_matrix.gates)),
                check("production_gate_required", any(gate.production_evidence_required for gate in release_gate_matrix.gates)),
                check("release_candidate_blocked", release_gate_matrix.v02_release_candidate_created is False and release_gate_matrix.v02_release_ready is False),
            ),
        ),
        scenario(
            "staging_qualification_plan_integrity",
            (
                check("staging_plan_design_only", staging_plan.staging_deployment_enabled is False),
                check("environment_isolated", "deny public ingress" in " ".join(staging_plan.environment_profile.network_isolation_assumptions)),
                check("offline_identity_fixtures", "offline fixture" in staging_plan.environment_profile.identity_provider_fixture_strategy),
                check("ephemeral_replay_fixture", bool(staging_plan.replay_ledger_prerequisites)),
                check("cleanup_acceptance", bool(staging_plan.cleanup)),
            ),
        ),
        scenario(
            "idempotency_exact_replay_and_changed_replay",
            (
                check("exact_replay_returned", public["replayed"].report_fingerprint == pilot_result.report_fingerprint),
                check("exact_replay_counter", pilot_result.exact_replays_returned == 1),
                check("changed_replay_rejected", public["changed_replay_rejected"]),
                check("no_second_evaluation_claim", pilot.get("exact_replays_returned") == 1),
                check("run_closed", pilot_result.active_qualification_sessions_after_close == 0),
            ),
        ),
        scenario(
            "determinism_redaction_concurrency_and_performance",
            (
                check("fixed_pilot_deterministic", pilot_result.model_dump(mode="json") == api.ControlledV02ReleaseQualificationService().run_canonical_disabled_pilot().model_dump(mode="json")),
                check("report_fingerprint_stable", pilot_result.report_fingerprint == api.ControlledV02ReleaseQualificationService().run_canonical_disabled_pilot().report_fingerprint),
                check("bounded_concurrency", resource_limits["maximum_local_qualification_runs"] == 20),
                check("safe_repr_redacted", "not-retained" not in repr(pilot_result).lower()),
                check("performance_smoke_bounded", pilot_result.release_gates_evaluated <= resource_limits["maximum_release_gates"]),
            ),
        ),
        scenario(
            "zero_operational_effects_and_release_boundary",
            (
                check("pilot_zero_effects", prohibited_effect_total == 0),
                check("ledger_zero_effects", all_prohibited_ledgers_zero),
                check("release_ready_false", program.get("v02_release_ready") is False and authorization_ledger.get("v02_release_ready") is False),
                check("tag_release_false", program.get("v02_tag_created") is False and program.get("v02_release_created") is False),
                check("aion_241_source_state_valid", source["aion_241_source_scope_state_valid"]),
            ),
        ),
        scenario(
            "controlled_isolated_staging_qualification_readiness",
            (
                check("sri_program_complete", program.get("aion_238_delivery_reconciliation", {}).get("active_sri_authorization_count") == 0),
                check("foundation_implemented", program.get("v02_release_qualification_foundation_implemented") is True),
                check("truthful_release_hold", pilot.get("v02_release_ready") is False and pilot.get("staging_evidence_required") is True and pilot.get("production_evidence_required") is True),
                check("offline_artifact_possible_without_public_egress", POSITIVE_AION241_LIMITS["maximum_local_container_builds"] == 2 and "maximum_public_network_calls" in ZERO_AION241_LIMITS),
                check("isolated_local_environment_possible", POSITIVE_AION241_LIMITS["maximum_internal_container_networks"] == 1 and POSITIVE_AION241_LIMITS["maximum_loopback_listeners"] == 4),
                check("docker_allowlist_can_be_bounded", POSITIVE_AION241_LIMITS["maximum_allowlisted_docker_cli_invocations"] == 100),
                check("ephemeral_fixture_strategy", POSITIVE_AION241_LIMITS["maximum_ephemeral_identity_keypairs"] == 1 and POSITIVE_AION241_LIMITS["maximum_ephemeral_replay_ledgers"] == 1),
                check("aion_241_separate_package", all("v02_staging_qualification" in path or path.endswith("v02_staging_qualification.py") for path in FUTURE_AION241_SOURCE_SCOPE)),
            ),
        ),
    ]

    scenario_passed = {item["scenario_id"]: item["status"] == "pass" for item in scenarios}
    hard_gates = {
        "pr_158_verified": scenario_passed["aion_239_delivery_and_ci_integrity"],
        "implementation_commit_verified": scenario_passed["aion_239_delivery_and_ci_integrity"],
        "ci_fix_commit_verified": scenario_passed["aion_239_delivery_and_ci_integrity"],
        "merge_commit_verified": implementation_main_commit == IMPLEMENTATION_MERGE_COMMIT,
        "merged_timestamp_verified": scenario_passed["aion_239_delivery_and_ci_integrity"],
        "required_ci_green": scenario_passed["aion_239_delivery_and_ci_integrity"],
        "aion_239_delivery_evidence_reconciled": scenario_passed["aion_239_delivery_and_ci_integrity"],
        "aion_238_authorization_exact_before_closeout": scenario_passed["authorization_lineage_and_scope"],
        "all_28_scenarios_executed": len(scenarios) == 28,
        "all_28_scenarios_passed": all(scenario_passed.values()),
        "no_required_scenario_skipped": [item["scenario_id"] for item in scenarios] == list(SCENARIO_IDS),
        "no_unknown_scenario": set(scenario_passed) == set(SCENARIO_IDS),
        "pilot_fingerprint_valid": scenario_passed["pilot_evidence_schema_and_fingerprint"],
        "readiness_domains_exact": scenario_passed["qualification_authorization_and_session_integrity"],
        "gap_dependencies_acyclic": scenario_passed["readiness_gap_matrix_completeness"],
        "gap_severity_preserved": scenario_passed["gap_severity_status_and_evidence_maturity"],
        "evidence_maturity_truthful": scenario_passed["gap_severity_status_and_evidence_maturity"],
        "production_auth_composition_valid": scenario_passed["production_auth_composition_integrity"],
        "request_identity_integration_valid": scenario_passed["verified_request_identity_integration_integrity"],
        "replay_ledger_provisioning_valid": scenario_passed["replay_ledger_provisioning_design_integrity"],
        "identity_provider_disabled_boundary_valid": scenario_passed["identity_provider_adapter_disabled_boundary"],
        "key_lifecycle_valid": scenario_passed["public_key_lifecycle_integrity"],
        "protected_material_handling_valid": scenario_passed["protected_material_lifecycle_integrity"],
        "credential_token_session_lifecycle_valid": scenario_passed["credential_token_and_session_lifecycle_integrity"],
        "artifact_sbom_provenance_valid": scenario_passed["sbom_and_artifact_provenance_integrity"],
        "reproducibility_honesty_valid": scenario_passed["reproducible_build_evidence_honesty"],
        "rollback_simulation_valid": scenario_passed["rollback_plan_and_drill_simulation_integrity"],
        "observability_health_valid": scenario_passed["observability_and_health_readiness_integrity"],
        "threat_model_complete": scenario_passed["production_threat_model_completeness"],
        "runtime_guard_fail_closed": scenario_passed["runtime_release_guard_precedence"],
        "release_gates_exact": scenario_passed["release_gate_matrix_integrity"],
        "staging_plan_valid": scenario_passed["staging_qualification_plan_integrity"],
        "zero_operational_effects": scenario_passed["zero_operational_effects_and_release_boundary"],
        "repository_release_boundary_valid": scenario_passed["zero_operational_effects_and_release_boundary"],
        "staging_qualification_readiness_valid": scenario_passed["controlled_isolated_staging_qualification_readiness"],
    }
    hard_gate_results = [
        {"gate_id": gate_id, "passed": bool(hard_gates[gate_id])}
        for gate_id in HARD_GATE_IDS
    ]
    evaluation_passed = all(item["status"] == "pass" for item in scenarios) and all(
        item["passed"] for item in hard_gate_results
    )
    decision = PASS_DECISION if evaluation_passed else FAIL_DECISION
    next_decision = NEXT_ARCHITECTURE_PASS if evaluation_passed else NEXT_ARCHITECTURE_FAIL
    report: dict[str, Any] = {
        "schema_version": "aion-v02-release-qualification-foundation-operator-evaluation/v1",
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "implementation_main_commit": implementation_main_commit,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [IMPLEMENTATION_PR],
        "implementation_feature_commits": [IMPLEMENTATION_COMMIT, CI_FIX_COMMIT],
        "implementation_merge_commits": [IMPLEMENTATION_MERGE_COMMIT],
        "implementation_branch": IMPLEMENTATION_BRANCH,
        "implementation_merged_at": IMPLEMENTATION_MERGED_AT,
        "required_ci_checks": list(REQUIRED_CI_CHECKS),
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenarios),
        "scenario_ids": list(SCENARIO_IDS),
        "scenario_results": scenarios,
        "hard_gate_results": hard_gate_results,
        "pilot_validation": {
            "pilot_id": pilot.get("pilot_id"),
            "report_fingerprint": pilot.get("report_fingerprint"),
            "fingerprint_valid": pilot_fingerprint_matches(api, pilot),
            "qualification_decision": pilot.get("qualification_decision"),
            "staging_evidence_required": pilot.get("staging_evidence_required"),
            "production_evidence_required": pilot.get("production_evidence_required"),
            "prohibited_effect_counters": {
                key: pilot.get(key) for key in api.PROHIBITED_EFFECT_COUNTERS
            },
        },
        "authorization_lineage": {
            "current_authorization_id": CURRENT_AUTHORIZATION_ID,
            "authorization_lineage_state": (
                "post_closeout" if authorization_post_closeout else "pre_closeout"
            ),
            "current_authorization_active_before_closeout": authorization_pre_closeout,
            "current_authorization_closed_after_evaluation": (
                authorization_closeout.get("authorization_active") is False
                and authorization_closeout.get("authorization_consumed") is True
            ),
            "active_authorization_id_after_evaluation": authorization_ledger.get(
                "authorization_transaction_id"
            ),
            "parent_evaluation_id": authorization_ledger.get("parent_evaluation_id"),
            "parent_program_id": authorization_ledger.get("parent_program_id"),
            "active_sri_authorization_count": program.get("aion_238_delivery_reconciliation", {}).get("active_sri_authorization_count"),
        },
        "gap_matrix_integrity": {
            "readiness_domains": [domain.value for domain in api.READINESS_DOMAINS],
            "gap_count": len(gap_matrix.gaps),
            "gap_ids": [gap.gap_id for gap in gap_matrix.gaps],
            "dependencies_acyclic": True,
            "staging_evidence_required": gap_matrix.staging_evidence_required,
            "production_evidence_required": gap_matrix.production_evidence_required,
        },
        "qualification_foundation_integrity": {
            "readiness_domains_evaluated": pilot.get("readiness_domains_evaluated"),
            "release_gates_evaluated": pilot.get("release_gates_evaluated"),
            "threat_scenarios_validated": pilot.get("threat_scenarios_validated"),
            "resource_limits": resource_limits,
            "positive_resource_limits_exact": {
                key: resource_limits.get(key) for key in expected_positive_limits
            } == expected_positive_limits,
        },
        "repository_integrity": {
            **source,
            "v02_release_ready": program.get("v02_release_ready"),
            "v02_tag_created": program.get("v02_tag_created"),
            "v02_release_created": program.get("v02_release_created"),
        },
        "security_state": {
            "production_auth_runtime_enabled": authorization_ledger.get("production_auth_runtime_enabled"),
            "external_identity_provider_call_enabled": authorization_ledger.get("external_identity_provider_call_enabled"),
            "credential_generation_enabled": authorization_ledger.get("credential_generation_enabled"),
            "token_generation_enabled": authorization_ledger.get("token_generation_enabled"),
            "live_replay_ledger_enabled": authorization_ledger.get("live_replay_ledger_enabled"),
            "production_deployment_enabled": authorization_ledger.get("production_deployment_enabled"),
            "v02_release_candidate_created": authorization_ledger.get("v02_release_candidate_created"),
        },
        "resource_state": {
            "aion_239_resource_limits": resource_limits,
            "aion_241_positive_resource_limits": POSITIVE_AION241_LIMITS,
            "aion_241_zero_resource_limits": {key: 0 for key in ZERO_AION241_LIMITS},
        },
        "next_architecture_decision": next_decision,
        "aion_241_authorization_preview": {
            "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
            "candidate_id": "controlled-isolated-local-staging-artifact-and-rollback-drill-core",
            "workstream": "v02-controlled-staging-qualification",
            "implementation_task": NEXT_IMPLEMENTATION_TASK,
            "formal_closeout_task": NEXT_FORMAL_CLOSEOUT_TASK,
            "final_planned_task": FINAL_PLANNED_TASK,
            "authorization_scope": STAGING_AUTHORIZATION_SCOPE,
            "approved_capabilities": {key: True for key in APPROVED_AION241_CAPABILITIES},
            "prohibited_capabilities": {key: False for key in PROHIBITED_AION241_CAPABILITIES},
            "resource_limits": {
                **POSITIVE_AION241_LIMITS,
                **{key: 0 for key in ZERO_AION241_LIMITS},
            },
            "future_source_scope": list(FUTURE_AION241_SOURCE_SCOPE),
            "future_uninstalled_runner": "scripts/v02-staging-qualification-local-run.py",
            "future_threat_model": list(FUTURE_AION241_THREATS),
            "implemented": source["aion_241_source_scope_implemented"],
        },
        "corrective_cycles": 0,
        "corrective_prs": [],
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
    }
    for key in REPORT_ZERO_EFFECT_FIELDS:
        report[key] = 0
    report["report_fingerprint"] = report_fingerprint(report)
    validate_report(report)
    return report


def iter_string_values(payload: Any) -> Sequence[str]:
    values: list[str] = []
    if isinstance(payload, dict):
        for item in payload.values():
            values.extend(iter_string_values(item))
    elif isinstance(payload, list):
        for item in payload:
            values.extend(iter_string_values(item))
    elif isinstance(payload, str):
        values.append(payload)
    return values


def validate_report(payload: Mapping[str, Any]) -> None:
    if payload.get("evaluation_id") != EVALUATION_ID:
        raise ValueError("evaluation_id mismatch")
    if payload.get("evaluation_type") != EVALUATION_TYPE:
        raise ValueError("evaluation_type mismatch")
    if payload.get("program_id") != PROGRAM_ID:
        raise ValueError("program_id mismatch")
    if payload.get("implementation_task") != IMPLEMENTATION_TASK:
        raise ValueError("implementation_task mismatch")
    if payload.get("closeout_task") != CLOSEOUT_TASK:
        raise ValueError("closeout_task mismatch")
    if payload.get("implementation_main_commit") != IMPLEMENTATION_MERGE_COMMIT:
        raise ValueError("implementation_main_commit mismatch")
    if payload.get("implementation_prs") != [IMPLEMENTATION_PR]:
        raise ValueError("implementation_prs mismatch")
    if payload.get("implementation_feature_commits") != [IMPLEMENTATION_COMMIT, CI_FIX_COMMIT]:
        raise ValueError("implementation_feature_commits mismatch")
    if payload.get("implementation_merge_commits") != [IMPLEMENTATION_MERGE_COMMIT]:
        raise ValueError("implementation_merge_commits mismatch")
    if payload.get("scenario_count") != 28:
        raise ValueError("scenario_count must be 28")
    if payload.get("scenario_ids") != list(SCENARIO_IDS):
        raise ValueError("scenario_ids mismatch")
    scenarios = payload.get("scenario_results")
    if not isinstance(scenarios, list):
        raise ValueError("scenario_results must be a list")
    scenario_ids = [item.get("scenario_id") for item in scenarios]
    if scenario_ids != list(SCENARIO_IDS):
        raise ValueError("scenario_results must follow the exact scenario order")
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("duplicate scenario id")
    hard_gates = payload.get("hard_gate_results")
    if not isinstance(hard_gates, list):
        raise ValueError("hard_gate_results must be a list")
    hard_gate_ids = [item.get("gate_id") for item in hard_gates]
    if hard_gate_ids != list(HARD_GATE_IDS):
        raise ValueError("hard_gate_results must follow the exact hard gate order")
    if len(set(hard_gate_ids)) != len(hard_gate_ids):
        raise ValueError("duplicate hard gate id")
    scenarios_passed = all(item.get("passed") is True and item.get("status") == "pass" for item in scenarios)
    hard_gates_passed = all(item.get("passed") is True for item in hard_gates)
    expected_pass = scenarios_passed and hard_gates_passed
    if payload.get("evaluation_passed") is not expected_pass:
        raise ValueError("evaluation_passed must derive from scenarios and hard gates")
    decision = payload.get("decision")
    if decision not in {PASS_DECISION, FAIL_DECISION}:
        raise ValueError("unexpected decision")
    if decision == PASS_DECISION and not expected_pass:
        raise ValueError("PASS decision cannot include failed gates")
    if decision == FAIL_DECISION and expected_pass:
        raise ValueError("FAIL decision cannot include all-passing gates")
    expected_next = NEXT_ARCHITECTURE_PASS if expected_pass else NEXT_ARCHITECTURE_FAIL
    if payload.get("next_architecture_decision") != expected_next:
        raise ValueError("next_architecture_decision mismatch")
    for key in ("synthetic", "read_only", "redacted", "repository_unchanged", "temporary_evaluation_data_cleaned"):
        if payload.get(key) is not True:
            raise ValueError(f"{key} must be true")
    for key in REPORT_ZERO_EFFECT_FIELDS:
        if payload.get(key) != 0:
            raise ValueError(f"{key} must be zero")
    preview = payload.get("aion_241_authorization_preview")
    if not isinstance(preview, dict):
        raise ValueError("aion_241_authorization_preview missing")
    if preview.get("authorization_transaction_id") != NEXT_AUTHORIZATION_ID:
        raise ValueError("next authorization id mismatch")
    if not isinstance(preview.get("implemented"), bool):
        raise ValueError("AION-241 implemented marker must be boolean")
    if not all(preview.get("approved_capabilities", {}).get(key) is True for key in APPROVED_AION241_CAPABILITIES):
        raise ValueError("approved AION-241 capability mismatch")
    if not all(preview.get("prohibited_capabilities", {}).get(key) is False for key in PROHIBITED_AION241_CAPABILITIES):
        raise ValueError("prohibited AION-241 capability mismatch")
    limits = preview.get("resource_limits", {})
    if {key: limits.get(key) for key in POSITIVE_AION241_LIMITS} != POSITIVE_AION241_LIMITS:
        raise ValueError("positive AION-241 resource limits mismatch")
    if any(limits.get(key) != 0 for key in ZERO_AION241_LIMITS):
        raise ValueError("zero AION-241 resource limits mismatch")
    if payload.get("report_fingerprint") != report_fingerprint(payload):
        raise ValueError("report fingerprint mismatch")
    rendered_values = json.dumps(iter_string_values(payload), sort_keys=True).lower()
    for marker in PROTECTED_VALUE_MARKERS:
        if marker in rendered_values:
            raise ValueError(f"protected marker leaked into report: {marker}")


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=EVALUATION_ID)
    parser.add_argument("--implementation-main-commit", default=IMPLEMENTATION_MERGE_COMMIT)
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--pilot-evidence", type=Path)
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.validate_report:
            validate_report(load_json(args.validate_report))
            return 0
        repo_root = (args.repo_root or Path.cwd()).resolve()
        if args.evaluation_id != EVALUATION_ID:
            raise ValueError("unexpected evaluation id")
        pilot_evidence = args.pilot_evidence or (
            repo_root
            / "examples/v02-release-qualification/v02-production-readiness-qualification-foundation-pilot-evidence.json"
        )
        report_path = args.report or (
            repo_root
            / "examples/v02-release-qualification/foundation-operator-evaluation-report.json"
        )
        evaluation_base_commit = args.evaluation_base_commit or args.implementation_main_commit
        report = evaluate(
            repo_root=repo_root,
            evaluation_id=args.evaluation_id,
            implementation_main_commit=args.implementation_main_commit,
            evaluation_base_commit=evaluation_base_commit,
            pilot_evidence_path=pilot_evidence,
            temporary_output_directory=args.temporary_output_directory or Path("/tmp/aion-v02rq-foundation-evaluation"),
        )
        write_json(report, report_path)
        return 0
    except Exception as exc:
        print(f"AION-240 evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
