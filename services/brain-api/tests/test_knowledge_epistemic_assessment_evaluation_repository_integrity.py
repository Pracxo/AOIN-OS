from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from aion243_release_candidate_scope import without_aion243_allowed_paths

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = (
    REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
)
FORBIDDEN_DIFF_PATHS = (
    ".github/workflows",
    "services/brain-api/src/aion_brain",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
    "migrations",
)
AION213_SOURCE = (
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_profiles.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_routing.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_deliberation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_synthesis.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_evidence.py",
)


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def _load_validator():
    sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))
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
        (REPO_ROOT / "docs/v02-release-qualification/program-ledger.json").read_text()
    )
    if (
        program.get("active_v02_release_qualification_task") not in {"AION-239", "AION-241"}
        or program.get("v02_release_qualification_foundation_implemented") is not True
        or program.get("foundation_runtime_state")
        != "implemented_disabled_design_only_local_simulation"
    ):
        return set()
    source_scope = program.get("implemented_source_scope")
    assert isinstance(source_scope, list)
    return {str(path) for path in source_scope}


def _assert_aion217_boundaries(changed: set[str]) -> None:
    assert changed <= _aion217_source_paths()
    for relative in (
        "services/brain-api/src/aion_brain/api/verified_knowledge.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_runtime.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_database.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/cognitive_memory_writer.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_policy_updater.py",
    ):
        assert not (REPO_ROOT / relative).exists(), relative


def _assert_aion239_boundaries(changed: set[str]) -> None:
    assert changed <= _aion239_source_paths()
    assert not (
        REPO_ROOT / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
    ).exists()


def _git_ref_exists(ref: str) -> bool:
    return _run(["git", "rev-parse", "--verify", "--quiet", ref]).returncode == 0


def _comparison_base() -> str | None:
    candidates: list[str] = []

    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.append(f"origin/{github_base_ref}")
        candidates.append(github_base_ref)

    candidates.extend(["origin/main", "main"])

    for candidate in candidates:
        if not _git_ref_exists(candidate):
            continue
        merge_base = _run(["git", "merge-base", "HEAD", candidate])
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()

    for candidate in ("HEAD^1", "HEAD~1"):
        if _git_ref_exists(candidate):
            return candidate

    return None


def _changed_forbidden_files() -> set[str]:
    base = _comparison_base()
    if base is None:
        return set()

    diff = _run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMRT",
            base,
            "HEAD",
            "--",
            *FORBIDDEN_DIFF_PATHS,
        ]
    )
    assert diff.returncode == 0, diff.stderr
    return without_aion243_allowed_paths(
        {line.strip() for line in diff.stdout.splitlines() if line.strip()}
    )


def test_aion_212_branch_does_not_add_aion_213_runtime_source():
    program = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text()
    )
    if (
        program.get("program_state")
        in {
            "domain_expert_mesh_implemented_persistent_write_disabled_pending_closeout",
            "tool_verification_fabric_authorized_not_implemented",
            "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout",
            "verified_knowledge_memory_authorized_not_implemented",
            "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout",
            "controlled_public_research_pilot_authorized_not_implemented",
            "controlled_public_research_pilot_implemented_operator_invoked_persistent_write_disabled_pending_closeout",
            "knowledge_intelligence_program_complete",
        }
    ):
        for relative in AION213_SOURCE:
            assert (REPO_ROOT / relative).exists(), relative
        assert program["model_call_enabled"] is False
        assert program["persistent_mesh_write_enabled"] is False
        assert program["runtime_effect"] is False
        return

    for relative in AION213_SOURCE:
        assert not (REPO_ROOT / relative).exists(), relative


def test_no_forbidden_runtime_dependency_migration_or_workflow_changes():
    changed = _changed_forbidden_files()
    if changed and changed <= _aion217_source_paths():
        _assert_aion217_boundaries(changed)
        return
    if changed and changed <= _aion239_source_paths():
        _assert_aion239_boundaries(changed)
        return
    assert changed == set()


def test_no_v02_tag_created():
    result = _run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"])
    assert result.returncode == 0
    assert result.stdout.strip() == ""
