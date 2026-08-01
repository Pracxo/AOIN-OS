from __future__ import annotations

import os
import subprocess

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
    changed = {line for line in diff.stdout.splitlines() if line}
    allowed = set()
    if _aion224_implemented():
        allowed.update(AION224_SOURCE_SCOPE)
    if _aion226_implemented():
        allowed.update(AION226_SOURCE_SCOPE)
        allowed.update(AION226_SUPPORT_SCOPE)
    if _aion239_implemented():
        allowed.update(AION239_SOURCE_SCOPE)
    if allowed:
        assert changed <= allowed
    else:
        assert changed == set()
