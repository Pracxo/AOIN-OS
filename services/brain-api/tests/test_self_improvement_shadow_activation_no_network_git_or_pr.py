"""AION-181 prohibited integration regression tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_GLOB = [
    REPO_ROOT / "services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py",
    *(REPO_ROOT / "services/brain-api/src/aion_brain/self_improvement").glob(
        "shadow_activation*.py",
    ),
]


def test_no_prohibited_imports_or_controllers() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_GLOB)
    for marker in (
        "import subprocess",
        "from subprocess",
        "import socket",
        "from socket",
        "import requests",
        "import httpx",
        "import aiohttp",
        "import git",
        "import github",
        "self_improvement.worktree",
        "self_improvement.patch_generator",
        "self_improvement.git_controller",
        "self_improvement.pr_controller",
        "self_improvement.merge_controller",
        "self_improvement.canary",
        "self_improvement.rollback_controller",
    ):
        assert marker not in combined
