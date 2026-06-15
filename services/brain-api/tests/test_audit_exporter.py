"""Audit exporter tests."""

from __future__ import annotations

from aion_brain.audit_integrity.exporter import AuditExporter
from aion_brain.contracts.audit_integrity import AuditExportRequest, AuditRecordRequest
from tests.audit_integrity_fakes import AllowPolicy, ledger


def test_audit_exporter_dry_run_writes_no_files(tmp_path) -> None:
    service, repo, _telemetry = ledger()
    service.record(_request())
    exporter = AuditExporter(repo, AllowPolicy())

    record = exporter.export(
        AuditExportRequest(owner_scope=["workspace:main"], output_dir=str(tmp_path), dry_run=True)
    )

    assert record.status == "dry_run"
    assert list(tmp_path.iterdir()) == []


def test_audit_exporter_write_mode_writes_jsonl(tmp_path) -> None:
    service, repo, _telemetry = ledger()
    service.record(_request())
    exporter = AuditExporter(repo, AllowPolicy())

    record = exporter.export(
        AuditExportRequest(owner_scope=["workspace:main"], output_dir=str(tmp_path), dry_run=False)
    )

    assert record.status == "completed"
    assert any(path.suffix == ".jsonl" for path in tmp_path.iterdir())


def test_audit_exporter_redacts_sensitive_fields(tmp_path) -> None:
    service, repo, _telemetry = ledger()
    service.record(_request())
    exporter = AuditExporter(repo, AllowPolicy())

    exporter.export(
        AuditExportRequest(owner_scope=["workspace:main"], output_dir=str(tmp_path), dry_run=False)
    )

    exported = "\n".join(path.read_text() for path in tmp_path.iterdir())
    assert "secret" not in exported.lower()


def _request() -> AuditRecordRequest:
    return AuditRecordRequest(
        action_type="command.dispatch",
        resource_type="command",
        event_type="command_created",
        outcome="completed",
        source_component="test",
        payload={"value": "safe"},
    )
