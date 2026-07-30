from __future__ import annotations

from aion_brain.contracts.secure_runtime import (
    SecureRuntimeIntegrityFinding,
    SecureRuntimeIntegrityReport,
    SecureRuntimeIntegrityStatus,
)
from tests.secure_runtime_test_support import NOW, secure_runtime_fixture


def test_integrity_report_records_no_effect_boundary() -> None:
    fixture = secure_runtime_fixture()
    finding = SecureRuntimeIntegrityFinding(
        finding_id="finding-AION-231",
        category="dispatch",
        status=SecureRuntimeIntegrityStatus.passed,
        reason_code="simulation_only",
        evidence_fingerprints=(fixture.dispatch.result_fingerprint or "",),
        created_at=NOW,
    )
    report = SecureRuntimeIntegrityReport(
        report_id="integrity-report-AION-231",
        session_id=fixture.session.session_id,
        status=SecureRuntimeIntegrityStatus.passed,
        findings=(finding,),
        checked_categories=("dispatch_simulation_only", "no_credentials", "no_tokens"),
        created_at=NOW,
    )

    assert report.status == SecureRuntimeIntegrityStatus.passed
    assert report.no_credentials is True
    assert report.no_tokens is True
    assert report.no_network is True
