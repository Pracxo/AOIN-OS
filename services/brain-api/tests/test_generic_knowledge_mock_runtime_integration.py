"""Generic Knowledge mock runtime integration tests."""

from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts.module_mock_runtime import (
    ModuleMockInvocationCreateRequest,
    ModuleMockOutput,
    ModuleMockProfileCreateRequest,
)

ROOT = Path(__file__).parents[3]
EXAMPLE_DIR = ROOT / "examples/modules/generic-knowledge-intelligence"


def test_generic_knowledge_mock_runtime_fixtures_validate() -> None:
    profile = ModuleMockProfileCreateRequest.model_validate(
        json.loads((EXAMPLE_DIR / "mock-profile.json").read_text())
    )
    invocation = ModuleMockInvocationCreateRequest.model_validate(
        json.loads((EXAMPLE_DIR / "mock-invocation-request.json").read_text())
    )
    output = ModuleMockOutput.model_validate(
        json.loads((EXAMPLE_DIR / "mock-output-example.json").read_text())
    )
    readiness = json.loads((EXAMPLE_DIR / "mock-readiness-trail.json").read_text())

    assert profile.profile_key == "generic.knowledge.mock"
    assert invocation.mode == "dry_run"
    assert output.redacted_output_payload["synthetic"] is True
    assert readiness["expected"]["activation_allowed"] is False
    assert readiness["expected"]["execution_allowed"] is False
