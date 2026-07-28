from __future__ import annotations

import os
import subprocess

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
    candidates: list[str] = []
    if github_base_ref := os.environ.get("GITHUB_BASE_REF"):
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])

    for candidate in candidates:
        if not _git_ref_exists(candidate):
            continue
        merge_base = subprocess.run(
            ["git", "merge-base", "HEAD", candidate],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    if _git_ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def test_aion_222_runtime_source_is_absent() -> None:
    ledger = load_json("docs/governed-learning-memory/authorization-ledger.json")
    for relative in ledger["authorized_source_scope"]:
        assert (REPO_ROOT / relative).exists(), relative


def test_aion_221_does_not_change_runtime_source_surface() -> None:
    base = _comparison_base()
    if base is None:
        return
    diff = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD", "--", "services/brain-api/src/aion_brain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line for line in diff.stdout.splitlines() if line}
    authorized = set(
        load_json("docs/governed-learning-memory/authorization-ledger.json")[
            "authorized_source_scope"
        ]
    )
    assert changed <= authorized
