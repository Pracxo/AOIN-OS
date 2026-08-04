from __future__ import annotations

import os
import subprocess

from aion243_release_candidate_scope import without_aion243_allowed_paths
from scripts.lib.governed_learning_memory_engagement_application import (
    AION226_SOURCE_SCOPE,
    AION226_SUPPORT_SCOPE,
)
from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION222_SOURCE_SCOPE,
    AION224_SOURCE_SCOPE,
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    FINAL_GLM_PROGRAM_STATES,
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
)
from test_governed_learning_memory_program_authorization import REPO_ROOT, load_json

AION239_SOURCE_SCOPE = {
    "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/__init__.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/artifact_provenance.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/authorization.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/credential_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/deployment_manifest.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/evidence.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/gap_matrix.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/identity_provider.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/integrity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/key_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/observability.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/production_auth_composition.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/protected_material.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/release_gate.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/replay_provisioning.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/request_identity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/rollback.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/runtime_guard.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/session_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/threat_model.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/token_lifecycle.py",
}
AION241_SOURCE_SCOPE = {
    "services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/__init__.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/artifact_manifest.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/authorization.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/build_plan.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/cleanup.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/component_binding.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/deployment_plan.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/environment_profile.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/evidence.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/health_readiness.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/identity_fixture.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/integrity.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/observability.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/provenance.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/replay_fixture.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/rollback.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/sbom.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/security_validation.py",
    "services/brain-api/src/aion_brain/v02_staging_qualification/source_snapshot.py",
}
AION248_SOURCE_SCOPE = {
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
}


def _git_ref_exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _comparison_base() -> str | None:
    candidates = []
    if base := os.environ.get("GITHUB_BASE_REF"):
        candidates.extend([f"origin/{base}", base])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if not _git_ref_exists(candidate):
            continue
        mb = subprocess.run(
            ["git", "merge-base", "HEAD", candidate],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if mb.returncode == 0 and mb.stdout.strip():
            return mb.stdout.strip()
    return "HEAD~1" if _git_ref_exists("HEAD~1") else None


def _aion224_implemented() -> bool:
    return (
        load_json("docs/governed-learning-memory/program-ledger.json")["program_state"]
        in {
            IMPLEMENTED_PENDING_CLOSEOUT_STATE,
            ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
            ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
            CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
            CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
            *FINAL_GLM_PROGRAM_STATES,
        }
    )


def _aion226_implemented() -> bool:
    return (
        load_json("docs/governed-learning-memory/program-ledger.json")["program_state"]
        in {
            ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
            CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
            CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
            *FINAL_GLM_PROGRAM_STATES,
        }
    )


def _aion239_implemented() -> bool:
    try:
        qualification = load_json("docs/v02-release-qualification/program-ledger.json")
    except FileNotFoundError:
        return False
    return qualification.get("v02_release_qualification_foundation_implemented") is True


def _aion241_implemented() -> bool:
    try:
        qualification = load_json("docs/v02-release-qualification/program-ledger.json")
    except FileNotFoundError:
        return False
    return qualification.get("controlled_staging_qualification_implemented") is True


def _aion248_implemented() -> bool:
    try:
        adaptive = load_json("docs/adaptive-intelligence/program-ledger.json")
    except FileNotFoundError:
        return False
    record = adaptive.get("aion_248_record", {})
    return (
        isinstance(record, dict)
        and adaptive.get("live_provider_pilot_authorized") is True
        and adaptive.get("active_adaptive_intelligence_authorization") == "AION-247-AI-0002"
        and adaptive.get("active_adaptive_intelligence_task") == "AION-248"
        and adaptive.get("formal_closeout_task") == "AION-249"
        and record.get("task_id") == "AION-248"
        and record.get("branch") == "phase/v03-openai-live-provider-pilot"
        and record.get("authorization_transaction") == "AION-247-AI-0002"
        and record.get("next_task") == "AION-249"
        and record.get("runtime_state")
        in {
            "single_openai_responses_api_live_provider_pilot_implementation_ready_live_execution_pending",
            "single_openai_responses_api_synthetic_live_provider_pilot_complete",
        }
    )


def test_aion_222_runtime_source_exists_and_aion_224_source_matches_state() -> None:
    for relative in AION222_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).exists(), relative
    for relative in AION224_SOURCE_SCOPE:
        if relative.endswith("__init__.py"):
            continue
        assert (REPO_ROOT / relative).exists() is _aion224_implemented(), relative
    for relative in AION226_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).exists() is _aion226_implemented(), relative


def test_aion_223_does_not_change_runtime_source_surface() -> None:
    base = _comparison_base()
    if base is None:
        return
    diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            base,
            "HEAD",
            "--",
            "services/brain-api/src/aion_brain",
            ".github/workflows",
            "services/brain-api/pyproject.toml",
            "packages/aion-sdk-python/src",
            "migrations",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = without_aion243_allowed_paths(
        {line for line in diff.stdout.splitlines() if line}
    )
    allowed = set()
    if _aion224_implemented():
        allowed.update(AION224_SOURCE_SCOPE)
    if _aion226_implemented():
        allowed.update(AION226_SOURCE_SCOPE)
        allowed.update(AION226_SUPPORT_SCOPE)
    if _aion239_implemented():
        allowed.update(AION239_SOURCE_SCOPE)
    if _aion241_implemented():
        allowed.update(AION241_SOURCE_SCOPE)
    if _aion248_implemented():
        allowed.update(AION248_SOURCE_SCOPE)
    if allowed:
        assert changed <= allowed
    else:
        assert changed == set()
