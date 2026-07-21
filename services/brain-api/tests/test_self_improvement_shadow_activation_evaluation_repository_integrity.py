"""AION-182 repository-boundary tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


FORBIDDEN_DIFF_PATHS = (
    ".github/workflows",
    "services/brain-api/src/aion_brain",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
    "migrations",
)


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
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend((f"origin/{github_base_ref}", github_base_ref))
    candidates.extend(("origin/main", "main"))
    for candidate in candidates:
        if _git_ref_exists(candidate):
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


def _changed_files() -> set[str]:
    base = _comparison_base()
    if base is None:
        return set()
    diff = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in diff.stdout.splitlines() if line.strip()}


def test_aion_182_does_not_modify_protected_runtime_paths() -> None:
    changed = _changed_files()
    blocked = [
        path
        for path in changed
        if any(path == prefix or path.startswith(f"{prefix}/") for prefix in FORBIDDEN_DIFF_PATHS)
    ]
    assert blocked == []


def test_evaluation_report_records_repository_unchanged() -> None:
    report = json.loads(
        (
            ROOT
            / (
                "examples/self-improvement/"
                "shadow-activation-control-plane-operator-evaluation-report.json"
            )
        ).read_text()
    )

    assert report["repository_digest_before"] == report["repository_digest_after"]
    assert report["repository_integrity"]["canonical_repository_untouched_by_evaluation"] is True
    assert report["repository_integrity"]["control_plane_real_pull_request_created"] is False


def test_release_tags_remain_unchanged() -> None:
    tag = subprocess.run(
        ["git", "rev-parse", "aion-v0.1.0^{}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    v02_tags = subprocess.run(
        ["git", "tag", "--list", "v0.2*", "aion-v0.2*"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert tag == "105fe29348160a2218ac095cfffadcb6f234421f"
    assert v02_tags == ""
