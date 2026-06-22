"""Module mock finding service tests."""

from __future__ import annotations

from aion_brain.contracts.module_mock_runtime import ModuleMockFindingDismissRequest
from aion_brain.module_mock_runtime import ModuleMockFindingService, ModuleMockSimulator
from tests.kernel_fakes import AllowPolicy
from tests.module_mock_helpers import SCOPE, invocation_request, repository, settings


def test_finding_service_dismiss_does_not_change_run_status() -> None:
    repo = repository()
    simulator = ModuleMockSimulator(repo, AllowPolicy(), settings=settings())
    run = simulator.invoke(invocation_request("missing-binding"))
    finding = run.findings[0]

    dismissed = ModuleMockFindingService(repo, AllowPolicy()).dismiss_finding(
        finding.module_mock_finding_id,
        SCOPE,
        ModuleMockFindingDismissRequest(reason="reviewed"),
    )
    stored_run = repo.get_run(run.module_mock_run_id)

    assert dismissed.status == "dismissed"
    assert stored_run is not None
    assert stored_run.status == "blocked"
