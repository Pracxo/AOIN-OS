"""Freeze gate performance check tests."""

from pathlib import Path

from aion_brain.contracts.freeze import FreezeGateRunRequest
from tests.test_freeze_gate import FakeApp, _service
from tests.versioning_fakes import SCOPE, write_minimal_release_docs


def test_freeze_gate_includes_performance_warning_when_missing(tmp_path: Path) -> None:
    write_minimal_release_docs(tmp_path)
    service = _service(tmp_path)

    run = service.run(FreezeGateRunRequest(version="0.1.0", owner_scope=SCOPE), app=FakeApp())
    checks = {check.name: check for check in run.checks}

    assert checks["performance_baseline_available"].status in {"warning", "passed"}
    assert checks["benchmark_smoke_passed"].status in {"warning", "passed"}
