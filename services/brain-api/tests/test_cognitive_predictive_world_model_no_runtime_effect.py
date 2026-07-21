"""AION-186 runtime-boundary and script-gate tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.world_model import WorldModelSnapshot

ROOT = Path(__file__).resolve().parents[3]


def test_runtime_effect_flags_fail_closed() -> None:
    with pytest.raises(ValidationError):
        WorldModelSnapshot(
            snapshot_id="snapshot-runtime",
            model_kind="probabilistic-counts",
            model_version="probabilistic-counts/test",
            evidence_count=0,
            state_count=0,
            action_count=0,
            transition_count=0,
            model_fingerprint="0" * 64,
            runtime_effect=True,
        )


def test_no_runtime_registration_or_api_route_added() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/world_model.py").exists()
    kernel_files = (
        ROOT / "services/brain-api/src/aion_brain/kernel/container.py",
        ROOT / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    )
    for path in kernel_files:
        assert "world_model" not in path.read_text()


def test_world_model_source_avoids_prohibited_runtime_imports() -> None:
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
    for path in (ROOT / "services/brain-api/src/aion_brain/world_model").glob("*.py"):
        text = path.read_text()
        for marker in prohibited:
            assert marker not in text


def test_cognitive_world_model_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-186 focused script test",
    }
    scripts = (
        "scripts/cognitive-world-model-no-go-regression.sh",
        "scripts/cognitive-world-model-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)


def test_world_model_imports_without_runtime_side_effects() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import aion_brain.contracts.world_model; "
                "import aion_brain.world_model"
            ),
        ],
        cwd=ROOT / "services/brain-api",
        check=True,
    )
