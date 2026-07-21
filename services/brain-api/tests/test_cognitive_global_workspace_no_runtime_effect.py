"""AION-188 runtime-boundary and script-gate tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.workspace import WorkspaceBroadcast, WorkspaceSnapshot

ROOT = Path(__file__).resolve().parents[3]


def test_runtime_effect_flags_fail_closed() -> None:
    with pytest.raises(ValidationError):
        WorkspaceBroadcast(
            broadcast_id="broadcast-runtime",
            cycle_id="cycle-runtime",
            decision_id="decision-runtime",
            runtime_effect=True,
        )
    with pytest.raises(ValidationError):
        WorkspaceSnapshot(
            snapshot_id="snapshot-runtime",
            cycle_id="cycle-runtime",
            sequence=1,
            network_calls=1,
        )


def test_no_runtime_registration_or_api_route_added() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/workspace.py").exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/api/global_workspace.py").exists()
    kernel_files = (
        ROOT / "services/brain-api/src/aion_brain/kernel/container.py",
        ROOT / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    )
    for path in kernel_files:
        assert "aion_brain.workspace" not in path.read_text()


def test_workspace_source_avoids_prohibited_runtime_imports() -> None:
    prohibited = (
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
    )
    for path in (ROOT / "services/brain-api/src/aion_brain/workspace").glob("*.py"):
        text = path.read_text()
        for marker in prohibited:
            assert marker not in text


def test_cognitive_global_workspace_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-188 focused script test",
    }
    scripts = (
        "scripts/cognitive-global-workspace-no-go-regression.sh",
        "scripts/cognitive-global-workspace-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)


def test_workspace_imports_without_runtime_side_effects() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import aion_brain.contracts.workspace; import aion_brain.workspace",
        ],
        cwd=ROOT / "services/brain-api",
        check=True,
    )
