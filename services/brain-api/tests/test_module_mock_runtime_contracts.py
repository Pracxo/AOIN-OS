"""Module mock runtime contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.module_mock_runtime import (
    ModuleMockInvocationCreateRequest,
    ModuleMockOutput,
    ModuleMockProfile,
    ModuleMockRun,
)
from tests.module_mock_helpers import SCOPE


def test_module_mock_profile_validates_profile_type() -> None:
    with pytest.raises(ValidationError):
        ModuleMockProfile.model_validate(
            {
                "mock_profile_id": "profile-1",
                "profile_key": "generic.mock",
                "name": "Generic",
                "description": "Generic mock profile.",
                "status": "active",
                "profile_type": "executable",
                "owner_scope": SCOPE,
            }
        )


def test_module_mock_profile_rejects_executable_simulation_rule() -> None:
    with pytest.raises(ValidationError):
        ModuleMockProfile.model_validate(
            {
                "mock_profile_id": "profile-1",
                "profile_key": "generic.mock",
                "name": "Generic",
                "description": "Generic mock profile.",
                "status": "active",
                "profile_type": "generic",
                "owner_scope": SCOPE,
                "simulation_rules": [{"command": "run-anything"}],
            }
        )


def test_module_mock_invocation_request_mode_must_be_dry_run() -> None:
    with pytest.raises(ValidationError):
        ModuleMockInvocationCreateRequest.model_validate(
            {
                "capability_binding_id": "binding-1",
                "capability_key": "generic.mock",
                "mode": "execute",
                "owner_scope": SCOPE,
            }
        )


def test_module_mock_run_safety_flags_must_stay_false() -> None:
    base = {
        "module_mock_run_id": "run-1",
        "mock_invocation_request_id": "request-1",
        "capability_binding_id": "binding-1",
        "status": "passed",
        "mode": "dry_run",
        "owner_scope": SCOPE,
        "score": 1.0,
        "schema_valid": True,
        "policy_valid": True,
        "sandbox_valid": True,
        "activation_allowed": False,
        "execution_allowed": False,
        "external_calls_made": False,
        "code_loaded": False,
    }
    assert ModuleMockRun.model_validate(base).activation_allowed is False
    for key in (
        "activation_allowed",
        "execution_allowed",
        "external_calls_made",
        "code_loaded",
    ):
        with pytest.raises(ValidationError):
            ModuleMockRun.model_validate({**base, key: True})


def test_module_mock_output_requires_synthetic_marker() -> None:
    payload = {
        "module_mock_output_id": "output-1",
        "module_mock_run_id": "run-1",
        "capability_binding_id": "binding-1",
        "capability_key": "generic.mock",
        "output_type": "generic",
        "status": "created",
        "output_payload_hash": "abc",
        "redacted_output_payload": {"synthetic": True},
        "output_summary": "Synthetic output.",
        "confidence": 0.8,
    }
    assert ModuleMockOutput.model_validate(payload).redacted_output_payload["synthetic"] is True
    with pytest.raises(ValidationError):
        ModuleMockOutput.model_validate({**payload, "redacted_output_payload": {}})
