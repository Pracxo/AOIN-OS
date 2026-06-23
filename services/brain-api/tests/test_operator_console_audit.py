from __future__ import annotations

from pathlib import Path

import pytest

from aion_brain.contracts.operator_console import ConsoleAuditRequest
from aion_brain.operator_console.audit import ConsoleContractAuditService
from tests.kernel_fakes import AllowPolicy, FakeTelemetry

ROOT = Path(__file__).resolve().parents[3]


def test_contract_audit_passes_when_frontend_files_absent() -> None:
    service = ConsoleContractAuditService(
        repo_root=ROOT,
        policy_adapter=AllowPolicy(),
        telemetry_service=FakeTelemetry(),
    )

    result = service.audit(ConsoleAuditRequest(owner_scope=["workspace:main"]))

    assert result.status == "passed"
    assert result.frontend_absent is True
    assert result.redaction_passed is True


def test_contract_audit_fails_if_frontend_package_file_appears(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}")
    service = ConsoleContractAuditService(repo_root=tmp_path, policy_adapter=AllowPolicy())

    with pytest.raises(ValueError, match="frontend files are forbidden"):
        service.audit(ConsoleAuditRequest(owner_scope=["workspace:main"], include_examples=False))


def test_contract_audit_emits_telemetry() -> None:
    telemetry = FakeTelemetry()
    service = ConsoleContractAuditService(
        repo_root=ROOT,
        policy_adapter=AllowPolicy(),
        telemetry_service=telemetry,
    )

    service.audit(ConsoleAuditRequest(owner_scope=["workspace:main"]))

    assert telemetry.events
    assert telemetry.events[0].event_type == (
        "operator_console_contract_audit_completed"
    )
