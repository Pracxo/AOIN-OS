from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_boundary import ProductionAuthRequestIdentityBoundary
from aion_brain.production_auth.verifier import DeterministicDisabledTestVerifier

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def test_request_identity_audit_and_provenance_are_redacted_and_correlated() -> None:
    boundary = ProductionAuthRequestIdentityBoundary(
        DeterministicDisabledTestVerifier(
            clock=lambda: FIXED_NOW,
            id_factory=lambda prefix: f"{prefix}-fixed",
        ),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )
    bundle = asyncio.run(
        boundary.build_bundle(
            RequestContext(
                request_id="request-1",
                trace_id="trace-1",
                correlation_id="corr-1",
                actor_id="ignored-actor",
                method="GET",
                path="/health",
                started_at=FIXED_NOW,
            )
        )
    )

    assert bundle.audit_event.event_type == "request_identity_boundary_attached"
    assert bundle.audit_event.redacted is True
    assert bundle.audit_event.runtime_effect is False
    assert bundle.provenance.redacted is True
    assert bundle.provenance.runtime_effect is False
    assert "authorization_transaction:AION-155-PA-0003" in bundle.provenance.source_refs
    assert "implementation_task:AION-156" in bundle.provenance.source_refs
    assert "trace_id:trace-1" in bundle.provenance.source_refs
    assert "correlation_id:corr-1" in bundle.provenance.source_refs
    assert "ignored-actor" not in str(bundle.model_dump(mode="json"))
