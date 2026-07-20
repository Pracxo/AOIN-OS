"""AION-181 determinism tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.self_improvement.shadow_activation_simulator import (
    ControlledShadowActivationSimulator,
    ShadowActivationSimulationRequest,
)


def test_fixed_inputs_produce_identical_simulation_output(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
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
    simulator = ControlledShadowActivationSimulator()
    first = simulator.simulate(request)
    second = simulator.simulate(request)
    assert first.fingerprint == second.fingerprint


def test_parallel_simulations_are_isolated(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)

    def run(index: int) -> str:
        request = ShadowActivationSimulationRequest(
            simulation_id=f"simulation-181-{index}",
            candidate=ctx["candidate"],
            request=ctx["request"],
            approval_binding=ctx["approval"],
            current_facts=ctx["facts"],
            resource_usage=ctx["usage"],
            health_snapshots=(ctx["snapshot"],),
            created_at=NOW,
        )
        return ControlledShadowActivationSimulator().simulate(request).simulation_id

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(run, range(8)))
    assert len(results) == len(set(results))
