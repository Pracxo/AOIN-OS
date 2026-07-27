from __future__ import annotations

from aion_brain.knowledge_intelligence.public_research_integrity import (
    audit_public_research_pilot_integrity,
    passing_public_research_integrity_checks,
)


def test_integrity_report_fails_when_required_check_fails() -> None:
    checks = passing_public_research_integrity_checks()
    checks["peer_address_verified"] = False
    report = audit_public_research_pilot_integrity(report_id="integrity-0001", checks=checks)
    assert report.passed is False
