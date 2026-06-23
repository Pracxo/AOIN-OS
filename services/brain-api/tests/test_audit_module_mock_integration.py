"""Audit/provenance integration for module mock runtime."""

from __future__ import annotations

from aion_brain.module_mock_runtime import ModuleMockSimulator
from tests.kernel_fakes import AllowPolicy
from tests.module_mock_helpers import (
    FakeProvenance,
    bound_module,
    invocation_request,
    repository,
    settings,
)


def test_module_mock_simulator_records_provenance() -> None:
    repo = repository()
    provenance = FakeProvenance()
    binding_services, _slot_id, binding_id = bound_module()
    simulator = ModuleMockSimulator(
        repo,
        AllowPolicy(),
        module_binding_repository=binding_services["repository"],
        provenance_service=provenance,
        settings=settings(),
    )

    run = simulator.invoke(invocation_request(binding_id))

    assert provenance.records == [("module_mock_run", run.module_mock_run_id)]
