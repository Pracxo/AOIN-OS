"""AION-180 / AION-181 source-scope specification tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from knowledge_intelligence_verified_knowledge_authorization import (  # noqa: E402
    AION217_OPTIONAL_SOURCE_PATHS,
    AION217_SOURCE_PATHS,
)
from self_improvement_governance import (  # noqa: E402
    SHADOW_ACTIVATION_ALLOWED_CREATE,
    SHADOW_ACTIVATION_ALLOWED_UPDATE,
)

AION217_ALLOWED_SOURCE_PATHS = set(AION217_SOURCE_PATHS) | set(
    AION217_OPTIONAL_SOURCE_PATHS
)


def _aion239_source_paths() -> set[str]:
    program = _json("docs/v02-release-qualification/program-ledger.json")
    if (
        program.get("active_v02_release_qualification_task") != "AION-239"
        or program.get("v02_release_qualification_foundation_implemented") is not True
        or program.get("foundation_runtime_state")
        != "implemented_disabled_design_only_local_simulation"
    ):
        return set()
    source_scope = program.get("implemented_source_scope")
    assert isinstance(source_scope, list)
    return {str(path) for path in source_scope}


def test_aion181_runtime_source_is_present_after_authorized_implementation() -> None:
    for relative in SHADOW_ACTIVATION_ALLOWED_CREATE:
        assert (ROOT / relative).is_file(), relative


def test_aion181_source_scope_is_exactly_recorded() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    assert tuple(record["allowed_aion181_create_paths"]) == SHADOW_ACTIVATION_ALLOWED_CREATE
    assert tuple(record["allowed_aion181_update_paths"]) == SHADOW_ACTIVATION_ALLOWED_UPDATE
    assert "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py" in record[
        "aion181_must_not_modify_paths"
    ]
    assert ".github/workflows/" in record["aion181_must_not_modify_paths"]
    assert "migrations/" in record["aion181_must_not_modify_paths"]


def test_aion181_branch_modifies_only_authorized_runtime_or_package_surfaces() -> None:
    changed = _changed_files(
        ".github/workflows",
        "services/brain-api/src/aion_brain",
        "services/brain-api/pyproject.toml",
        "packages/aion-sdk-python/src",
        "migrations",
    )
    aion239_source_paths = _aion239_source_paths()
    assert (
        changed
        <= set(SHADOW_ACTIVATION_ALLOWED_CREATE)
        | AION217_ALLOWED_SOURCE_PATHS
        | aion239_source_paths
    )
    if changed & AION217_ALLOWED_SOURCE_PATHS:
        _assert_aion217_runtime_surfaces_absent()
    if changed & aion239_source_paths:
        _assert_aion239_runtime_surfaces_absent()


def _assert_aion217_runtime_surfaces_absent() -> None:
    for relative in (
        "services/brain-api/src/aion_brain/api/verified_knowledge.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_runtime.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_database.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/cognitive_memory_writer.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_policy_updater.py",
    ):
        assert not (ROOT / relative).exists(), relative


def _assert_aion239_runtime_surfaces_absent() -> None:
    assert not (
        ROOT / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
    ).exists()


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _git_ref_exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _comparison_base() -> str | None:
    candidates = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])

    for candidate in candidates:
        if not _git_ref_exists(candidate):
            continue
        merge_base = subprocess.run(
            ["git", "merge-base", "HEAD", candidate],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()

    if _git_ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def _changed_files(*pathspecs: str) -> set[str]:
    base = _comparison_base()
    if base is None:
        return set()

    changed = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD", "--", *pathspecs],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in changed.stdout.splitlines() if line.strip()}
