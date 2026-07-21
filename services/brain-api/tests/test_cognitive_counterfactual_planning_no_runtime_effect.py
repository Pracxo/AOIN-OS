"""AION-192 no-runtime-effect regression tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLANNING_CORE = REPO_ROOT / "services/brain-api/src/aion_brain/planning/core.py"
PLANNING_CONTRACTS = REPO_ROOT / "services/brain-api/src/aion_brain/contracts/planning.py"


def test_counterfactual_planning_has_no_api_route_or_kernel_registration() -> None:
    assert not (REPO_ROOT / "services/brain-api/src/aion_brain/api/planning.py").exists()
    assert not (
        REPO_ROOT / "services/brain-api/src/aion_brain/api/counterfactual_planning.py"
    ).exists()

    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (REPO_ROOT / relative).read_text()
        assert "StrategicPlanner" not in text
        assert "aion_brain.planning.core" not in text


def test_counterfactual_planning_source_has_no_prohibited_runtime_markers() -> None:
    source_text = "\n".join((PLANNING_CORE.read_text(), PLANNING_CONTRACTS.read_text()))
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        assert marker not in source_text


def test_counterfactual_planning_imports_do_not_create_runtime_effects() -> None:
    code = """
from aion_brain.contracts.planning import PlanningRuntimeBoundary
from aion_brain.planning import StrategicPlanner

boundary = PlanningRuntimeBoundary(boundary_id="import-boundary")
assert boundary.runtime_effect is False
assert boundary.network_calls == 0
assert boundary.connector_calls == 0
assert boundary.model_provider_calls == 0
assert boundary.direct_action_execution is False
assert boundary.source_rewrite is False
assert boundary.background_planning_loop is False
assert boundary.git_mutation is False
assert StrategicPlanner is not None
"""
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT / "services/brain-api",
        check=True,
    )


def test_counterfactual_planning_scripts_pass_under_pytest_context() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "test_counterfactual_planning_scripts",
    }
    for script in (
        "scripts/cognitive-counterfactual-planning-no-go-regression.sh",
        "scripts/cognitive-counterfactual-planning-check.sh",
    ):
        subprocess.run(
            [str(REPO_ROOT / script)],
            cwd=REPO_ROOT,
            env=env,
            check=True,
        )
