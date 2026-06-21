"""Freeze Gate integration with Contract Registry."""

from __future__ import annotations

from aion_brain.contracts.freeze import FreezeGateRunRequest
from tests.contract_registry_helpers import SCOPE, drift_finding, repository
from tests.test_freeze_gate import FakeApp, _service
from tests.versioning_fakes import write_minimal_release_docs


def test_freeze_gate_fails_on_active_breaking_contract_findings(tmp_path) -> None:  # type: ignore[no-untyped-def]
    write_minimal_release_docs(tmp_path)
    repo = repository()
    repo.save_finding(drift_finding())
    service = _service(tmp_path)
    service.set_contract_registry_repository(repo)

    run = service.run(FreezeGateRunRequest(version="0.1.0", owner_scope=SCOPE), app=FakeApp())

    assert any(check.name == "no_active_breaking_interface_findings" for check in run.checks)
    assert run.status == "failed"
