"""AION-184 runtime-boundary and script-gate tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.cognitive_state import CognitiveStateProvenance

ROOT = Path(__file__).resolve().parents[3]


def test_runtime_effect_flags_fail_closed() -> None:
    with pytest.raises(ValidationError):
        CognitiveStateProvenance(
            provenance_id="prov-runtime",
            operation_id="op-runtime",
            source="synthetic-test",
            evidence_refs=("aion://evidence/runtime",),
            runtime_effect=True,
        )


def test_no_runtime_registration_or_api_route_added() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/cognitive_state.py").exists()
    kernel_files = (
        ROOT / "services/brain-api/src/aion_brain/kernel/container.py",
        ROOT / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    )
    for path in kernel_files:
        assert "cognitive_architecture" not in path.read_text()


def test_cognitive_state_source_avoids_prohibited_controllers() -> None:
    prohibited = (
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
    )
    for path in (
        ROOT / "services/brain-api/src/aion_brain/cognitive_architecture"
    ).glob("*.py"):
        text = path.read_text()
        for marker in prohibited:
            assert marker not in text


def test_cognitive_persistent_state_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-184 focused script test",
    }
    scripts = (
        "scripts/cognitive-persistent-state-no-go-regression.sh",
        "scripts/cognitive-persistent-state-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)


def test_cognitive_state_contracts_import_without_runtime_side_effects() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import aion_brain.contracts.cognitive_state; "
                "import aion_brain.cognitive_architecture"
            ),
        ],
        cwd=ROOT / "services/brain-api",
        check=True,
    )
