"""AION-182 repository-boundary tests."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"


FORBIDDEN_DIFF_PATHS = (
    ".github/workflows",
    "services/brain-api/src/aion_brain",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
    "migrations",
)


def _load_validator():
    sys.path.insert(0, str(ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _aion217_source_paths() -> set[str]:
    validator = _load_validator()
    return set(validator.AION217_SOURCE_PATHS) | set(validator.AION217_OPTIONAL_SOURCE_PATHS)


def _aion239_source_paths() -> set[str]:
    program = json.loads(
        (ROOT / "docs/v02-release-qualification/program-ledger.json").read_text()
    )
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
    aion217_paths = _aion217_source_paths()
    aion239_paths = _aion239_source_paths()
    blocked = [
        path
        for path in changed
        if any(
            path == prefix or path.startswith(f"{prefix}/")
            for prefix in FORBIDDEN_DIFF_PATHS
        )
        and path not in aion217_paths
        and path not in aion239_paths
    ]
    if changed & aion217_paths:
        _assert_aion217_runtime_surfaces_absent()
    if changed & aion239_paths:
        _assert_aion239_runtime_surfaces_absent()
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
