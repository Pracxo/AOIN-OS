from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts import v02_staging_qualification as c
from aion_brain.v02_staging_qualification import (
    ControlledV02StagingQualificationService,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = REPO_ROOT / "scripts/v02-staging-qualification-local-run.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("aion241_runner", RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_aion_241_constants_resource_limits_and_source_scope_are_exact():
    limits = c.resource_limits().limits

    assert c.PROGRAM_ID == "AION-V02-RELEASE-QUALIFICATION-001"
    assert c.AUTHORIZATION_TRANSACTION_ID == "AION-240-V02RQ-0002"
    assert c.IMPLEMENTATION_TASK == "AION-241"
    assert c.FORMAL_CLOSEOUT_TASK == "AION-242"
    assert c.FINAL_PLANNED_TASK == "AION-244"
    assert limits == {**c.POSITIVE_RESOURCE_LIMITS, **dict.fromkeys(c.ZERO_RESOURCE_LIMITS, 0)}
    assert len(c.REQUIRED_SOURCE_SCOPE) == 20
    for blocked in {
        "public_deployment",
        "production_deployment",
        "external_registry",
        "production_identity",
        "production_database",
        "release_candidate",
        "release_ready",
        "tag_created",
        "release_published",
    }:
        assert blocked not in {item.value for item in c.V02StagingDeploymentStatus}


def test_canonical_builders_cover_required_staging_surfaces():
    service = ControlledV02StagingQualificationService()
    context = c.canonical_docker_context_projection()
    inventory = c.canonical_local_image_inventory()
    snapshot = c.canonical_source_snapshot_manifest()
    build_plan = c.canonical_build_plan(snapshot, inventory)
    artifact = c.canonical_artifact_manifest(snapshot, inventory)
    sbom = c.canonical_sbom(snapshot, inventory)
    provenance = c.canonical_provenance(snapshot, inventory, sbom)
    comparison = c.canonical_reproducibility_comparison(snapshot, inventory)
    environment = c.canonical_environment_profile()
    identity = c.canonical_identity_fixture_result()
    replay = c.canonical_replay_fixture_result(identity.assertion_fingerprint)
    deployment = c.canonical_deployment_plan()
    health = c.canonical_health_readiness_report()
    security = c.canonical_security_validation_report()
    observability = c.canonical_observability_snapshot()
    rollback = c.canonical_rollback_plan()
    rollback_result = c.V02StagingRollbackResult(rollback_id=rollback.rollback_id)
    cleanup = c.canonical_cleanup_result()

    assert service.validate_docker_context_projection(context) == context
    assert service.validate_local_image_inventory(inventory) == inventory
    assert service.validate_source_snapshot(snapshot) == snapshot
    assert service.validate_build_plan(build_plan) == build_plan
    assert service.validate_artifact_manifest(artifact) == artifact
    assert service.validate_sbom(sbom) == sbom
    assert service.validate_provenance(provenance) == provenance
    assert service.validate_reproducibility_comparison(comparison) == comparison
    assert service.validate_environment_profile(environment) == environment
    assert service.validate_identity_fixture(identity) == identity
    assert service.validate_replay_fixture(replay) == replay
    assert service.validate_deployment_plan(deployment) == deployment
    assert service.validate_health_readiness(health) == health
    assert service.validate_security_validation(security) == security
    assert service.validate_observability(observability) == observability
    assert service.validate_rollback_plan(rollback) == rollback
    assert service.validate_rollback_result(rollback_result) == rollback_result
    assert service.validate_cleanup_result(cleanup) == cleanup


def test_authorization_session_and_replay_fail_closed():
    service = ControlledV02StagingQualificationService()
    binding = c.canonical_component_binding()
    authorization = c.canonical_authorization_envelope(binding)
    first = service.create_session_plan("aion-241-session-one")
    second = service.create_session_plan("aion-241-session-two")

    assert service.validate_authorization(authorization).authorization_active is True
    session = service.start_session(first)
    with pytest.raises(ValueError):
        service.start_session(second)
    assert service.close_session(session.session_id).active is False

    bundle = service.run_canonical_pilot_projection()
    request = service.repository._request_fingerprints[bundle.pilot_id]
    assert service.replay_exact_qualification(bundle.pilot_id, request).pilot_id == c.PILOT_ID
    assert service.reject_changed_replay(bundle.pilot_id) is True


def test_contracts_reject_protected_material_and_live_effect_claims():
    with pytest.raises(ValidationError):
        c.V02StagingEvidenceRecord(
            evidence_id="AION-241-EVIDENCE-SECRET",
            evidence_maturity=c.V02EvidenceMaturity.implemented,
            evidence_payload_fingerprint=c.ZERO_FINGERPRINT,
            token="sk-not-retained",  # type: ignore[call-arg]
        )

    environment = c.canonical_environment_profile()
    environment_payload = environment.model_dump()
    environment_payload.update(
        {
            "public_network_access_enabled": True,
            "environment_profile_fingerprint": None,
        }
    )
    with pytest.raises(ValidationError):
        c.V02StagingEnvironmentProfile(**environment_payload)

    build_plan = c.canonical_build_plan(
        c.canonical_source_snapshot_manifest(),
        c.canonical_local_image_inventory(),
    )
    build_payload = build_plan.model_dump()
    build_payload.update({"registry_pulls": 1, "build_plan_fingerprint": None})
    with pytest.raises(ValidationError):
        c.V02StagingBuildPlan(**build_payload)


def test_runner_command_policy_rejects_registry_and_privileged_commands():
    runner = load_runner()
    docker = "/usr/local/bin/docker"

    runner.assert_allowed_docker_command(
        docker,
        [
            docker,
            "buildx",
            "build",
            "--load",
            "--pull=false",
            "--network=none",
            "--file",
            "Dockerfile",
            "--tag",
            "aion241:test",
            "context",
        ],
    )
    runner.assert_allowed_docker_command(
        docker,
        [
            docker,
            "run",
            "--rm",
            "--pull",
            "never",
            "--network",
            "aion241-deadbeef_aion241_internal",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "image",
        ],
    )
    with pytest.raises(RuntimeError):
        runner.assert_allowed_docker_command(docker, [docker, "login"])
    with pytest.raises(RuntimeError):
        runner.assert_allowed_docker_command(
            docker,
            [docker, "run", "--rm", "--privileged", "image"],
        )
    with pytest.raises(RuntimeError):
        runner.assert_allowed_docker_command(
            docker,
            [
                docker,
                "run",
                "--rm",
                "--network",
                "bridge",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "image",
            ],
        )


def test_runner_dependency_publisher_detection_is_fail_closed():
    runner = load_runner()

    for value in (None, "", "[]", "null", "None", []):
        assert runner.has_host_publishers(value) is False
    assert (
        runner.has_host_publishers([{"URL": "", "TargetPort": 8080, "PublishedPort": 0}])
        is False
    )
    assert runner.has_host_publishers([{"URL": "127.0.0.1", "PublishedPort": 12345}]) is True
    assert runner.has_host_publishers([{"URL": "", "PublishedPort": 12345}]) is True
    assert runner.has_host_publishers("127.0.0.1:12345->8080/tcp") is True


def test_committed_pilot_evidence_when_present_has_valid_fingerprint():
    evidence_path = (
        REPO_ROOT
        / "examples"
        / "v02-release-qualification"
        / "v02-controlled-isolated-staging-pilot-evidence.json"
    )
    if not evidence_path.exists():
        return
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    expected = c.v02_staging_fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    assert payload["report_fingerprint"] == expected
    assert payload["pilot_id"] == c.PILOT_ID
    assert payload["authorization_id"] == c.AUTHORIZATION_TRANSACTION_ID
    assert payload["integrity_passed"] is True
    assert payload["v02_release_ready"] is False
