"""AION-178 prohibited integration tests."""

from __future__ import annotations

import ast

from test_self_improvement_shadow_contracts import ROOT

SHADOW_SOURCE = (
    ROOT / "services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py",
    *(
        ROOT / "services/brain-api/src/aion_brain/self_improvement"
    ).glob("shadow_*.py"),
)

PROHIBITED_IMPORTS = {
    "subprocess",
    "socket",
    "requests",
    "httpx",
    "aiohttp",
    "git",
    "github",
}
PROHIBITED_CONTROLLERS = {
    "worktree",
    "patch_generator",
    "git_controller",
    "pr_controller",
    "merge_controller",
    "canary",
    "rollback_controller",
}


def test_shadow_source_has_no_network_git_or_pr_imports() -> None:
    for path in SHADOW_SOURCE:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
                assert not imported & PROHIBITED_IMPORTS, path
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
                assert module.split(".")[0] not in PROHIBITED_IMPORTS, path
                assert not any(
                    f"self_improvement.{item}" in module for item in PROHIBITED_CONTROLLERS
                )


def test_shadow_source_has_no_runtime_adapters_or_startup_hooks() -> None:
    joined = "\n".join(path.read_text() for path in SHADOW_SOURCE)

    for marker in (
        "startup",
        "scheduler",
        "poller",
        "provider client",
        "connector client",
        "model adapter",
        "create_pull_request",
        "merge_pull_request",
    ):
        assert marker not in joined
