"""AION-181 simulator tests."""

from __future__ import annotations

from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationApprovalBinding,
    ShadowActivationHealthSnapshot,
)
from aion_brain.self_improvement.shadow_activation_simulator import (
    ControlledShadowActivationSimulator,
    ShadowActivationSimulationRequest,
)


def _simulation_request(
    ctx: dict[str, object],
    **patch: object,
) -> ShadowActivationSimulationRequest:
    payload = {
        "simulation_id": "simulation-181",
        "candidate": ctx["candidate"],
        "request": ctx["request"],
        "approval_binding": ctx["approval"],
        "current_facts": ctx["facts"],
        "resource_usage": ctx["usage"],
        "health_snapshots": (ctx["snapshot"],),
        "created_at": NOW,
    }
    payload.update(patch)
    return ShadowActivationSimulationRequest(**payload)


def test_valid_external_approval_reaches_review_pending(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    result = ControlledShadowActivationSimulator().simulate(_simulation_request(ctx))
    assert result.simulation_passed is True
    assert result.state_sequence[-1] == "review_pending"
    assert "active" not in result.state_sequence
    assert result.shadow_activation_enabled is False
    assert result.pull_request_created is False


def test_invalid_approval_stops_before_simulation_ready(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    payload = ctx["approval"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    payload["approver_principal_ids"] = ("operator-requester", "operator-b")
    approval = ShadowActivationApprovalBinding(**payload)
    result = ControlledShadowActivationSimulator().simulate(
        _simulation_request(ctx, approval_binding=approval)
    )
    assert result.simulation_passed is False
    assert "simulation_ready" not in result.state_sequence
    assert result.approval_created is False


def test_deactivation_trigger_creates_failed_evidence(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    snapshot = ShadowActivationHealthSnapshot(
        activation_candidate_id=ctx["candidate"].activation_candidate_id,
        network_call_count=1,
        observed_at=NOW,
    )
    result = ControlledShadowActivationSimulator().simulate(
        _simulation_request(ctx, health_snapshots=(snapshot,))
    )
    assert result.simulation_passed is False
    assert result.incident_records
    assert result.runtime_effect is False
