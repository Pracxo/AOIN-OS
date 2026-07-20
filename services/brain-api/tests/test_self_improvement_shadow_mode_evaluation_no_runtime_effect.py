"""AION-179 no-runtime-effect regression tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


def test_shadow_operator_evaluation_report_has_no_side_effects() -> None:
    report = _json("examples/self-improvement/shadow-mode-operator-evaluation-report.json")

    for key in (
        "runtime_activation_created",
        "new_implementation_authorization_created",
        "shadow_plane_runtime_enabled",
        "source_modified",
        "git_mutated",
        "pull_request_created",
        "approval_created",
        "runtime_effect",
        "active_learning_promoted",
    ):
        assert report[key] is False, key
    assert report["hard_gates"]["no_network_calls_observed"] is True
    assert report["hard_gates"]["no_git_mutations_observed"] is True
    assert report["hard_gates"]["no_source_mutations_observed"] is True


def test_runtime_influence_scenario_records_zero_effects() -> None:
    report = _json("examples/self-improvement/shadow-mode-operator-evaluation-report.json")
    scenarios = {item["scenario_id"]: item for item in report["scenario_results"]}
    runtime = scenarios["runtime-influence-boundary"]

    assert runtime["passed"] is True
    assert runtime["hard_gates"] == {
        "approval_creation_absent": True,
        "git_operations_zero": True,
        "network_calls_zero": True,
        "real_pull_requests_zero": True,
        "runtime_effect_absent": True,
        "runtime_promotions_zero": True,
        "source_mutations_zero": True,
    }


def test_shadow_operator_harness_has_no_protected_runtime_imports() -> None:
    harness = (ROOT / "scripts/lib/self_improvement_shadow_operator_evaluation.py").read_text()

    forbidden_imports = (
        "import subprocess",
        "import socket",
        "import requests",
        "import httpx",
        "import aiohttp",
        "import git",
        "import github",
    )
    forbidden_controllers = (
        "self_improvement.worktree",
        "self_improvement.patch_generator",
        "self_improvement.git_controller",
        "self_improvement.pr_controller",
        "self_improvement.merge_controller",
        "self_improvement.canary",
        "self_improvement.rollback_controller",
    )
    for marker in (*forbidden_imports, *forbidden_controllers):
        assert marker not in harness


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
