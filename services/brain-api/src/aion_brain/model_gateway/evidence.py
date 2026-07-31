"""Redacted model-gateway evidence bundles."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.model_gateway import (
    ModelGatewayDiagnostics,
    ModelGatewayEvidenceBundle,
    ModelGatewayIncident,
    ModelGatewayOperatorReviewItem,
)


def operator_review_item(
    *,
    review_item_id: str,
    session_id: str,
    created_at: datetime,
    request_fingerprint: str | None = None,
) -> ModelGatewayOperatorReviewItem:
    """Create the mandatory no-effect operator-review item."""

    return ModelGatewayOperatorReviewItem(
        review_item_id=review_item_id,
        session_id=session_id,
        request_fingerprint=request_fingerprint,
        created_at=created_at,
    )


def diagnostics(
    *,
    diagnostics_id: str,
    counters: dict[str, int],
    created_at: datetime,
) -> ModelGatewayDiagnostics:
    """Create redacted diagnostics evidence."""

    return ModelGatewayDiagnostics(
        diagnostics_id=diagnostics_id,
        counters=counters,
        prohibited_effect_counters_zero=all(value == 0 for value in counters.values()),
        created_at=created_at,
    )


def evidence_bundle(
    *,
    bundle_id: str,
    diagnostics_record: ModelGatewayDiagnostics,
    operator_review_items: tuple[ModelGatewayOperatorReviewItem, ...],
    integrity_report_fingerprint: str,
    audit_chain_head: str,
    created_at: datetime,
    incidents: tuple[ModelGatewayIncident, ...] = (),
) -> ModelGatewayEvidenceBundle:
    """Create a redacted evidence bundle."""

    return ModelGatewayEvidenceBundle(
        bundle_id=bundle_id,
        diagnostics=diagnostics_record,
        incidents=incidents,
        operator_review_items=operator_review_items,
        integrity_report_fingerprint=integrity_report_fingerprint,
        audit_chain_head=audit_chain_head,
        created_at=created_at,
    )
