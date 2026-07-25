from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
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


def test_aion_212_branch_does_not_add_aion_213_runtime_source():
    for relative in AION213_SOURCE:
        assert not (REPO_ROOT / relative).exists(), relative


def test_no_forbidden_runtime_dependency_migration_or_workflow_changes():
    base = "origin/main"
    if _run(["git", "rev-parse", "--verify", "--quiet", base]).returncode != 0:
        base = "HEAD~1"
    diff = _run(
        [
            "git",
            "diff",
            "--name-only",
            f"{base}...HEAD",
            "--",
            ".github/workflows",
            "services/brain-api/src/aion_brain",
            "services/brain-api/pyproject.toml",
            "packages/aion-sdk-python/src",
            "migrations",
        ]
    )
    assert diff.returncode == 0
    assert diff.stdout.strip() == ""


def test_no_v02_tag_created():
    result = _run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"])
    assert result.returncode == 0
    assert result.stdout.strip() == ""
