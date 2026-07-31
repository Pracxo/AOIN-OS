from __future__ import annotations

from aion_brain.model_gateway.integrity import audit_integrity
from tests.model_gateway_aion233_test_support import NOW


def test_integrity_report_preserves_no_effect_boundaries() -> None:
    report = audit_integrity(
        report_id="integrity-AION-233",
        session_id="gateway-session",
        audit_chain_head="0" * 64,
        checked_categories=("audit", "no_network", "no_provider_calls"),
        created_at=NOW,
    )
    assert report.status.value == "passed"
    assert report.no_credentials is True
    assert report.no_tokens is True
    assert report.no_network is True
    assert report.no_provider_calls is True
    assert report.no_production_writes is True
    assert report.production_effect is False
