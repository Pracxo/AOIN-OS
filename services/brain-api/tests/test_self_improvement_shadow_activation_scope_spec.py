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

from self_improvement_governance import (  # noqa: E402
    SHADOW_ACTIVATION_ALLOWED_CREATE,
    SHADOW_ACTIVATION_ALLOWED_UPDATE,
)


def test_aion181_runtime_source_is_absent_in_aion180() -> None:
    for relative in SHADOW_ACTIVATION_ALLOWED_CREATE:
        assert not (ROOT / relative).exists(), relative


def test_aion181_source_scope_is_exactly_recorded() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    assert tuple(record["allowed_aion181_create_paths"]) == SHADOW_ACTIVATION_ALLOWED_CREATE
    assert tuple(record["allowed_aion181_update_paths"]) == SHADOW_ACTIVATION_ALLOWED_UPDATE
    assert "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py" in record[
        "aion181_must_not_modify_paths"
    ]
    assert ".github/workflows/" in record["aion181_must_not_modify_paths"]
    assert "migrations/" in record["aion181_must_not_modify_paths"]


def test_aion180_branch_does_not_modify_runtime_or_package_surfaces() -> None:
    changed = _changed_files(
        ".github/workflows",
        "services/brain-api/src/aion_brain",
        "services/brain-api/pyproject.toml",
        "packages/aion-sdk-python/src",
        "migrations",
    )
    assert changed == set()


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
