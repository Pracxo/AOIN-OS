"""Freeze gate resilience integration tests."""

from __future__ import annotations

from pathlib import Path

from aion_brain.contracts.freeze import FreezeGateRunRequest
from tests.resilience_fakes import SCOPE
from tests.resilience_fakes import test_run as resilience_test_run
from tests.test_freeze_gate import FakeApp, _service
from tests.versioning_fakes import write_minimal_release_docs


def test_freeze_gate_warns_when_resilience_runner_missing(tmp_path: Path) -> None:
    write_minimal_release_docs(tmp_path)
    service = _service(tmp_path)

    run = service.run(FreezeGateRunRequest(version="0.1.0", owner_scope=SCOPE), app=FakeApp())
    checks = {check.name: check for check in run.checks}

    assert checks["resilience_status_healthy_or_only_optional_degraded"].status == "warning"


def test_freeze_gate_fails_on_critical_resilience_failure(tmp_path: Path) -> None:
    write_minimal_release_docs(tmp_path)
    service = _service(tmp_path)
    service._resilience_test_runner = FakeResilienceRunner("failed")  # noqa: SLF001

    run = service.run(FreezeGateRunRequest(version="0.1.0", owner_scope=SCOPE), app=FakeApp())
    checks = {check.name: check for check in run.checks}

    assert checks["resilience_status_healthy_or_only_optional_degraded"].status == "failed"
    assert run.status == "failed"


class FakeResilienceRunner:
    def __init__(self, status: str) -> None:
        self.status = status

    def run(self, request: object) -> object:
        return resilience_test_run(self.status)
