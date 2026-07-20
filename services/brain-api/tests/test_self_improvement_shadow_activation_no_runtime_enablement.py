"""AION-181 runtime enablement regression tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_GLOB = [
    REPO_ROOT / "services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py",
    *(REPO_ROOT / "services/brain-api/src/aion_brain/self_improvement").glob(
        "shadow_activation*.py",
    ),
]


def test_new_activation_source_has_no_runtime_registration_terms() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_GLOB)
    for marker in (
        "KernelContainer",
        "include_router",
        "add_event_handler",
        "on_event",
        "startup",
        "scheduler",
        "create_task",
    ):
        assert marker not in combined
    for marker in (
        "shadow_activation_enabled: bool = True",
        "runtime_effect: bool = True",
        "pull_request_created: bool = True",
        "approval_created: bool = True",
        "merged: bool = True",
    ):
        assert marker not in combined
