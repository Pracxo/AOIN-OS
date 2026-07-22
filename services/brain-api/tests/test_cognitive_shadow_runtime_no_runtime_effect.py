"""AION-199 runtime-boundary and script-gate tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_cognitive_shadow_runtime import (
    NOW,
    cycle_input,
    runtime_with_session,
)

from aion_brain.contracts.cognitive_runtime import (
    CognitiveRuntimeDiagnostics,
    CognitiveRuntimeEvidence,
)

ROOT = Path(__file__).resolve().parents[3]


def test_runtime_boundary_flags_fail_closed() -> None:
    runtime, _manifest, session = runtime_with_session()
    output = runtime.run_cycle(session, cycle_input())

    with pytest.raises(ValidationError):
        CognitiveRuntimeDiagnostics(
            diagnostics_id="bad-runtime-effect",
            session_id=session.session_id,
            cycle_id="bad-cycle",
            status="operator_review_required",
            cycle_steps_completed=output.diagnostics.cycle_steps_completed,
            cycle_count=1,
            runtime_effect=True,
            created_at=NOW,
        )
    with pytest.raises(ValidationError):
        CognitiveRuntimeEvidence(
            evidence_id="bad-network",
            session_id=session.session_id,
            cycle_id="bad-cycle",
            state_before_hash=output.state_before.content_hash or "",
            state_after_hash=output.state_after.content_hash or "",
            workspace_snapshot_hash=output.workspace_snapshot.snapshot_hash or "",
            plan_fingerprint=output.plan.fingerprint or "",
            information_plan_fingerprint=output.information_plan.fingerprint or "",
            consolidation_checkpoint_fingerprint=(
                output.consolidation_outcome.checkpoint.fingerprint or ""
            ),
            learning_candidate_ids=tuple(
                candidate.candidate_id for candidate in output.learning_candidates
            ),
            simulated_outcome_ids=tuple(
                outcome.observed_effect_id for outcome in output.simulated_outcomes
            ),
            network_calls=1,
            created_at=NOW,
        )


def test_no_api_route_kernel_registration_or_startup_surface_added() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/cognitive_runtime.py").exists()
    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "ControlledCognitiveShadowRuntime" not in text
        assert "aion_brain.cognitive_runtime" not in text


def test_shadow_runtime_source_avoids_prohibited_external_imports() -> None:
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
    source_files = tuple(
        (ROOT / "services/brain-api/src/aion_brain/cognitive_runtime").glob("*.py")
    ) + (
        ROOT / "services/brain-api/src/aion_brain/contracts/cognitive_runtime.py",
    )
    for path in source_files:
        text = path.read_text()
        for marker in prohibited:
            assert f"import {marker}" not in text
            assert f"from {marker} import" not in text


def test_shadow_runtime_imports_without_registration_side_effects() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import aion_brain.contracts.cognitive_runtime; "
            "import aion_brain.cognitive_runtime",
        ],
        cwd=ROOT / "services/brain-api",
        check=True,
    )


def test_shadow_runtime_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-199 focused script test",
    }
    scripts = (
        "scripts/cognitive-shadow-runtime-no-go-regression.sh",
        "scripts/cognitive-shadow-runtime-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
