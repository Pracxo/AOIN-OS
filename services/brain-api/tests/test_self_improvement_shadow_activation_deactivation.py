"""AION-181 deactivation decision tests."""

from __future__ import annotations

from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import ShadowActivationHealthSnapshot
from aion_brain.self_improvement.shadow_activation_deactivation import (
    ShadowActivationDeactivationService,
)
from aion_brain.self_improvement.shadow_activation_monitoring import evaluate_monitoring_snapshot


def test_no_trigger_produces_no_incident(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    service = ShadowActivationDeactivationService()
    decision, incident = service.evaluate(
        candidate=ctx["candidate"],
        request=ctx["request"],
        monitoring_decision=evaluate_monitoring_snapshot(
            ctx["snapshot"],
            ctx["monitoring_plan"],
            activation_window_end=ctx["request"].activation_window_end,
            maximum_runs=ctx["request"].maximum_runs,
            now=NOW,
        ),
        deactivation_plan=ctx["deactivation_plan"],
        now=NOW,
    )
    assert decision.triggered is False
    assert incident is None


def test_trigger_produces_redacted_incident_and_no_side_effect(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    decision, incident = ShadowActivationDeactivationService().evaluate(
        candidate=ctx["candidate"],
        request=ctx["request"],
        monitoring_decision=evaluate_monitoring_snapshot(
            ShadowActivationHealthSnapshot(
                activation_candidate_id=ctx["candidate"].activation_candidate_id,
                network_call_count=1,
                observed_at=NOW,
            ),
            ctx["monitoring_plan"],
            activation_window_end=ctx["request"].activation_window_end,
            maximum_runs=ctx["request"].maximum_runs,
            now=NOW,
        ),
        deactivation_plan=ctx["deactivation_plan"],
        now=NOW,
    )
    assert decision.triggered is True
    assert decision.stop_future_runs is True
    assert decision.runtime_action_performed is False
    assert decision.source_action_performed is False
    assert decision.reactivation_authorized is False
    assert incident is not None
    assert incident.redacted is True
    assert incident.runtime_action_performed is False
