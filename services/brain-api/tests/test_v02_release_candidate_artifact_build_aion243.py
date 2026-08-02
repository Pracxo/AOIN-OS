from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts import v02_release_candidate as c
from aion_brain.v02_release_candidate import ControlledV02ReleaseCandidateService

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = REPO_ROOT / "scripts/v02-release-candidate-local-run.py"
EVIDENCE_PATH = (
    REPO_ROOT
    / "examples"
    / "v02-release-qualification"
    / "v02-release-candidate-artifact-build-evidence.json"
)


def load_runner():
    spec = importlib.util.spec_from_file_location("aion243_runner", RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_aion_243_constants_resource_limits_and_source_scope_are_exact() -> None:
    assert c.PROGRAM_ID == "AION-V02-RELEASE-QUALIFICATION-001"
    assert c.AUTHORIZATION_TRANSACTION_ID == "AION-242-V02RQ-0003"
    assert c.IMPLEMENTATION_TASK == "AION-243"
    assert c.FORMAL_CLOSEOUT_TASK == "AION-244"
    assert c.CANDIDATE_LABEL == "aion-v0.2.0-rc.1"
    assert c.PYTHON_PACKAGE_VERSION == "0.2.0rc1"
    assert c.LOCAL_IMAGE_TAG == "aoinos-brain-api:aion-v0.2.0-rc.1"
    assert c.resource_limits() == {
        **c.POSITIVE_RESOURCE_LIMITS,
        **dict.fromkeys(c.ZERO_RESOURCE_LIMITS, 0),
    }
    assert len(c.REQUIRED_SOURCE_SCOPE) == 18
    for relative in c.REQUIRED_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).is_file()


def test_service_validates_candidate_contract_surfaces() -> None:
    service = ControlledV02ReleaseCandidateService()
    authorization = c.canonical_authorization_envelope()
    plan = c.canonical_artifact_plan()
    version = c.canonical_version_manifest()

    assert service.validate_authorization(authorization) == authorization
    assert service.validate_artifact_plan(plan) == plan
    assert service.validate_version_manifest(version) == version

    with pytest.raises(ValueError):
        service.validate_artifact_plan(plan.model_copy(update={"network_mode": "bridge"}))
    with pytest.raises(ValueError):
        service.validate_version_manifest(version.model_copy(update={"dependency_changes": 1}))


def test_contracts_reject_protected_material_publication_and_tags() -> None:
    with pytest.raises(ValidationError):
        c.V02CandidateArtifactRecord(
            artifact_id="bad",
            artifact_kind="bad",
            relative_path="metadata/bad.json",
            byte_count=1,
            sha256=c.ZERO_FINGERPRINT,
            source_commit=c.AUTHORIZED_SOURCE_COMMIT_PLACEHOLDER,
            private_key="not-retained",  # type: ignore[call-arg]
        )

    with pytest.raises(ValidationError):
        c.V02CandidateArtifactRecord(
            artifact_id="bad",
            artifact_kind="bad",
            relative_path="/tmp/bad.json",
            byte_count=1,
            sha256=c.ZERO_FINGERPRINT,
            source_commit=c.AUTHORIZED_SOURCE_COMMIT_PLACEHOLDER,
        )

    version = c.canonical_version_manifest()
    service = ControlledV02ReleaseCandidateService()
    with pytest.raises(ValueError):
        service.validate_version_manifest(version.model_copy(update={"git_tag_created": True}))


def test_runner_command_policy_and_command_surface_are_fail_closed(tmp_path: Path) -> None:
    runner = load_runner()
    docker = "/usr/local/bin/docker"
    state = runner.RunnerState(docker=docker, run_id="test", temporary_root=tmp_path)

    runner.assert_allowed_docker_command(
        state,
        [
            docker,
            "buildx",
            "build",
            "--load",
            "--pull=false",
            "--network=none",
            "--provenance=false",
            "--sbom=false",
            "--tag",
            c.LOCAL_IMAGE_TAG,
            "--file",
            "Dockerfile",
            "context",
        ],
    )
    runner.assert_allowed_docker_command(
        state,
        [
            docker,
            "buildx",
            "build",
            "--pull=false",
            "--network=none",
            "--provenance=false",
            "--sbom=false",
            "--output",
            "type=oci,dest=/tmp/aion.oci.tar",
            "--file",
            "Dockerfile",
            "context",
        ],
    )
    with pytest.raises(RuntimeError):
        runner.assert_allowed_docker_command(state, [docker, "login"])
    with pytest.raises(RuntimeError):
        runner.assert_allowed_docker_command(
            state,
            [docker, "run", "--rm", "--pull", "never", "--network", "host", "image"],
        )

    parser = runner.build_parser()
    assert set(parser._subparsers._group_actions[0].choices) == {  # type: ignore[attr-defined]
        "preflight",
        "build-candidate",
        "verify-candidate",
        "audit-evidence",
        "cleanup-temporary",
    }


def test_runner_deterministic_tar_helper_replays_exactly(tmp_path: Path) -> None:
    runner = load_runner()
    source = tmp_path / "source"
    source.mkdir()
    (source / "b.txt").write_text("two\n", encoding="utf-8")
    (source / "a.txt").write_text("one\n", encoding="utf-8")
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    runner.deterministic_tar_gz(source, first, prefix="probe")
    runner.deterministic_tar_gz(source, second, prefix="probe")

    assert runner.sha256_file(first) == runner.sha256_file(second)


def test_current_state_keeps_release_hold_and_authorization_active() -> None:
    program = load_json("docs/v02-release-qualification/program-ledger.json")
    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")
    evidence_exists = EVIDENCE_PATH.is_file()

    for payload in (program, auth):
        assert payload["active_v02_release_qualification_authorization"] == (
            c.AUTHORIZATION_TRANSACTION_ID
        )
        assert payload["active_v02_release_qualification_task"] == "AION-243"
        assert payload["formal_closeout_task"] == "AION-244"
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["release_candidate_published"] is False
        assert payload["production_deployment_enabled"] is False
        assert payload["v02_release_ready"] is False
        assert payload["v02_tag_created"] is False
        assert payload["v02_release_created"] is False
        assert payload["release_candidate_artifact_build_implemented"] is evidence_exists
        assert payload["release_candidate_created"] is evidence_exists


def test_committed_candidate_evidence_when_present_has_valid_fingerprint() -> None:
    if not EVIDENCE_PATH.is_file():
        return

    payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    expected = c.v02_release_candidate_fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    assert payload["report_fingerprint"] == expected
    assert payload["candidate_id"] == c.CANDIDATE_LABEL
    assert payload["authorization_id"] == c.AUTHORIZATION_TRANSACTION_ID
    assert payload["brain_api_package_version"] == c.PYTHON_PACKAGE_VERSION
    assert payload["sdk_package_version"] == c.PYTHON_PACKAGE_VERSION
    assert payload["candidate_bundle_retained"] is True
    assert payload["candidate_image_retained"] is True
    assert payload["release_candidate_published"] is False
    assert payload["v02_release_ready"] is False
    assert payload["integrity_passed"] is True
