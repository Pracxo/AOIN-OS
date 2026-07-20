"""AION-181 incident evidence tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import ShadowActivationIncidentRecord


def test_incident_is_redacted_read_only_and_inert(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    incident = ShadowActivationIncidentRecord(
        incident_id="incident-181",
        activation_candidate_id=ctx["candidate"].activation_candidate_id,
        activation_request_id=ctx["request"].activation_request_id,
        incident_type="activation_deactivation_required",
        trigger_codes=("network_call_detected",),
        monitoring_snapshot_fingerprint=ctx["snapshot"].fingerprint,
        deactivation_plan_fingerprint=ctx["deactivation_plan"].fingerprint,
        created_at=NOW,
    )
    assert incident.redacted is True
    assert incident.runtime_action_performed is False
    with pytest.raises(ValidationError):
        ShadowActivationIncidentRecord(
            **{
                **incident.model_dump(mode="python", exclude={"fingerprint"}),
                "runtime_action_performed": True,
            }
        )
