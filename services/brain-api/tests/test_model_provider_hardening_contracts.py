"""Model provider hardening contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.model_provider_hardening import (
    ModelProviderProfile,
    ModelProviderReadiness,
    ModelProviderSimulation,
    PromptEgressPreview,
)
from tests.model_provider_hardening_helpers import SCOPE


def test_model_provider_profile_validates_provider_type() -> None:
    with pytest.raises(ValidationError):
        ModelProviderProfile.model_validate(
            {
                "provider_profile_id": "profile-1",
                "provider_key": "generic.metadata_only",
                "name": "Generic",
                "description": "Generic profile.",
                "status": "proposed",
                "provider_type": "live_provider",
                "owner_scope": SCOPE,
                "risk_level": "medium",
                "external_calls_allowed": False,
                "credentials_required": False,
            }
        )


def test_model_provider_profile_rejects_external_calls_allowed() -> None:
    with pytest.raises(ValidationError):
        ModelProviderProfile.model_validate(
            {
                "provider_profile_id": "profile-1",
                "provider_key": "generic.metadata_only",
                "name": "Generic",
                "description": "Generic profile.",
                "status": "proposed",
                "provider_type": "metadata_only",
                "owner_scope": SCOPE,
                "risk_level": "medium",
                "external_calls_allowed": True,
                "credentials_required": False,
            }
        )


def test_model_provider_profile_rejects_secret_metadata() -> None:
    with pytest.raises(ValidationError):
        ModelProviderProfile.model_validate(
            {
                "provider_profile_id": "profile-1",
                "provider_key": "generic.metadata_only",
                "name": "Generic",
                "description": "Generic profile.",
                "status": "proposed",
                "provider_type": "metadata_only",
                "owner_scope": SCOPE,
                "risk_level": "medium",
                "external_calls_allowed": False,
                "credentials_required": False,
                "metadata": {"api_key": "sk-test"},
            }
        )


def test_prompt_egress_preview_external_call_allowed_false() -> None:
    preview = PromptEgressPreview.model_validate(
        {
            "prompt_egress_preview_id": "preview-1",
            "provider_key": "generic.metadata_only",
            "status": "warning",
            "preview_type": "dry_run",
            "owner_scope": SCOPE,
            "redacted_prompt_summary": {"section_count": 1},
            "egress_allowed": False,
            "external_call_allowed": False,
        }
    )
    assert preview.external_call_allowed is False
    with pytest.raises(ValidationError):
        PromptEgressPreview.model_validate(
            {**preview.model_dump(mode="python"), "external_call_allowed": True}
        )


def test_model_provider_simulation_safety_flags_remain_false() -> None:
    base = {
        "provider_simulation_id": "simulation-1",
        "provider_key": "generic.metadata_only",
        "status": "passed",
        "simulation_type": "dry_run",
        "owner_scope": SCOPE,
        "simulated_request_hash": "abc",
        "simulated_response_hash": "def",
        "redacted_simulated_request": {"input_manifest_ref": "manifest-1"},
        "redacted_simulated_response": {"synthetic": True},
        "output_governance_status": "passed",
        "tool_intent_status": "none",
        "grounding_status": "synthetic",
        "external_calls_made": False,
        "credentials_used": False,
        "model_invoked": False,
        "score": 1.0,
    }
    assert ModelProviderSimulation.model_validate(base).model_invoked is False
    for key in ("external_calls_made", "credentials_used", "model_invoked"):
        with pytest.raises(ValidationError):
            ModelProviderSimulation.model_validate({**base, key: True})


def test_model_provider_readiness_external_and_credentials_ready_false() -> None:
    base = {
        "provider_readiness_id": "readiness-1",
        "provider_key": "generic.metadata_only",
        "status": "ready_for_review",
        "readiness_level": "dry_run_ready",
        "owner_scope": SCOPE,
        "external_call_ready": False,
        "credentials_ready": False,
        "egress_guard_ready": True,
        "output_governance_ready": True,
        "tool_intent_guard_ready": True,
        "grounding_ready": True,
        "policy_ready": True,
        "audit_ready": True,
        "score": 0.8,
    }
    assert ModelProviderReadiness.model_validate(base).external_call_ready is False
    with pytest.raises(ValidationError):
        ModelProviderReadiness.model_validate({**base, "external_call_ready": True})
    with pytest.raises(ValidationError):
        ModelProviderReadiness.model_validate({**base, "credentials_ready": True})
