"""AION-181 CI-safe performance smoke tests."""

from __future__ import annotations

import time
from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    evaluate_shadow_activation_budget,
    evaluate_shadow_activation_deactivation,
    evaluate_shadow_activation_health,
    validate_activation_candidate,
    validate_shadow_activation_approval,
)
from aion_brain.self_improvement.shadow_activation_simulator import (
    ControlledShadowActivationSimulator,
    ShadowActivationSimulationRequest,
)


def test_performance_smoke(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    start = time.perf_counter()
    for _ in range(10_000):
        validate_activation_candidate(ctx["candidate"], now=NOW)
    for _ in range(10_000):
        type(ctx["request"]).model_validate(ctx["request"].model_dump(mode="python"))
    for _ in range(5_000):
        evaluate_shadow_activation_budget(ctx["usage"], ctx["budget"])
    for _ in range(5_000):
        validate_shadow_activation_approval(
            approval=ctx["approval"],
            candidate=ctx["candidate"],
            request=ctx["request"],
            current_facts=ctx["facts"],
            now=NOW,
        )
    for _ in range(5_000):
        evaluate_shadow_activation_health(
            ctx["snapshot"],
            ctx["monitoring_plan"],
            activation_window_end=ctx["request"].activation_window_end,
            maximum_runs=ctx["request"].maximum_runs,
            now=NOW,
        )
    monitoring = evaluate_shadow_activation_health(
        ctx["snapshot"],
        ctx["monitoring_plan"],
        activation_window_end=ctx["request"].activation_window_end,
        maximum_runs=ctx["request"].maximum_runs,
        now=NOW,
    )
    for _ in range(2_000):
        evaluate_shadow_activation_deactivation(
            health_decision=monitoring,
            deactivation_plan=ctx["deactivation_plan"],
            now=NOW,
        )
    simulator = ControlledShadowActivationSimulator()
    request = ShadowActivationSimulationRequest(
        simulation_id="simulation-181",
        candidate=ctx["candidate"],
        request=ctx["request"],
        approval_binding=ctx["approval"],
        current_facts=ctx["facts"],
        resource_usage=ctx["usage"],
        health_snapshots=(ctx["snapshot"],),
        created_at=NOW,
    )
    for _ in range(1_000):
        simulator.simulate(request)
    assert time.perf_counter() - start < 60
