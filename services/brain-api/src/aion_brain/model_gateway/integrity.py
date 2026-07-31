"""Model-gateway integrity reporting."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.model_gateway import (
    ModelGatewayIntegrityFinding,
    ModelGatewayIntegrityReport,
    ModelGatewayIntegrityStatus,
)


def audit_integrity(
    *,
    report_id: str,
    session_id: str,
    audit_chain_head: str,
    checked_categories: tuple[str, ...],
    created_at: datetime,
    findings: tuple[ModelGatewayIntegrityFinding, ...] = (),
) -> ModelGatewayIntegrityReport:
    """Build a no-effect integrity report."""

    return ModelGatewayIntegrityReport(
        report_id=report_id,
        session_id=session_id,
        status=(
            ModelGatewayIntegrityStatus.failed
            if findings
            else ModelGatewayIntegrityStatus.passed
        ),
        findings=findings,
        checked_categories=checked_categories,
        audit_chain_head=audit_chain_head,
        created_at=created_at,
    )
