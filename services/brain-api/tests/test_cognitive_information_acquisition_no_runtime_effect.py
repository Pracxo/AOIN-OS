"""AION-194 no-runtime-effect regression tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ACQUISITION_CORE = (
    REPO_ROOT / "services/brain-api/src/aion_brain/information_acquisition/core.py"
)
ACQUISITION_CONTRACTS = (
    REPO_ROOT / "services/brain-api/src/aion_brain/contracts/information_acquisition.py"
)


def test_information_acquisition_has_no_api_route_or_kernel_registration() -> None:
    assert not (
        REPO_ROOT / "services/brain-api/src/aion_brain/api/information_acquisition.py"
    ).exists()

    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (REPO_ROOT / relative).read_text()
        assert "InformationAcquisitionPlanner" not in text
        assert "aion_brain.information_acquisition" not in text


def test_information_acquisition_source_has_no_prohibited_runtime_markers() -> None:
    source_text = "\n".join((ACQUISITION_CORE.read_text(), ACQUISITION_CONTRACTS.read_text()))
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


def test_information_acquisition_imports_do_not_create_runtime_effects() -> None:
    code = """
from aion_brain.contracts.information_acquisition import InformationAcquisitionRuntimeBoundary
from aion_brain.information_acquisition import InformationAcquisitionPlanner

boundary = InformationAcquisitionRuntimeBoundary(boundary_id="import-boundary")
assert boundary.runtime_effect is False
assert boundary.network_calls == 0
assert boundary.connector_calls == 0
assert boundary.model_provider_calls == 0
assert boundary.tool_execution is False
assert boundary.information_acquired is False
assert boundary.unauthorized_information_acquisition == 0
assert boundary.source_rewrite is False
assert boundary.git_mutation is False
assert InformationAcquisitionPlanner is not None
"""
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT / "services/brain-api",
        check=True,
    )


def test_information_acquisition_scripts_pass_under_pytest_context() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "test_information_acquisition_scripts",
    }
    for script in (
        "scripts/cognitive-information-acquisition-no-go-regression.sh",
        "scripts/cognitive-information-acquisition-check.sh",
    ):
        subprocess.run(
            [str(REPO_ROOT / script)],
            cwd=REPO_ROOT,
            env=env,
            check=True,
        )
