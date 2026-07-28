from __future__ import annotations

import os
import subprocess

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION222_SOURCE_SCOPE,
    AION224_SOURCE_SCOPE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
)
from test_governed_learning_memory_program_authorization import REPO_ROOT, load_json


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
        in {IMPLEMENTED_PENDING_CLOSEOUT_STATE, ENGAGEMENT_APPLICATION_AUTHORIZED_STATE}
    )


def test_aion_222_runtime_source_exists_and_aion_224_source_matches_state() -> None:
    for relative in AION222_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).exists(), relative
    for relative in AION224_SOURCE_SCOPE:
        if relative.endswith("__init__.py"):
            continue
        assert (REPO_ROOT / relative).exists() is _aion224_implemented(), relative


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
    if _aion224_implemented():
        assert changed <= set(AION224_SOURCE_SCOPE)
    else:
        assert changed == set()
