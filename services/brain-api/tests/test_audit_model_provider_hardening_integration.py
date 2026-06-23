"""Audit and provenance integration for provider simulations."""

from __future__ import annotations

from typing import Any

from aion_brain.model_provider_hardening import ModelProviderSimulator
from tests.kernel_fakes import AllowPolicy, FakeTelemetry
from tests.model_provider_hardening_helpers import (
    FakeProvenance,
    repository,
    settings,
    simulation_request,
)


class FakeAuditSink:
    """Collect audit requests."""

    def __init__(self) -> None:
        self.requests: list[Any] = []

    def record(self, request: Any) -> Any:
        self.requests.append(request)
        return request


def test_provider_simulation_records_audit_and_provenance() -> None:
    audit = FakeAuditSink()
    provenance = FakeProvenance()
    simulator = ModelProviderSimulator(
        repository(),
        AllowPolicy(),
        telemetry_service=FakeTelemetry(),
        audit_sink=audit,
        provenance_service=provenance,
        settings=settings(),
    )

    simulation = simulator.simulate(simulation_request())

    assert audit.requests[0].action_type == "model_provider.simulate"
    assert audit.requests[0].payload["model_invoked"] is False
    assert provenance.records == [("model_provider_simulation", simulation.provider_simulation_id)]
