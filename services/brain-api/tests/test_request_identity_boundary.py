from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_boundary import ProductionAuthRequestIdentityBoundary
from aion_brain.production_auth.verifier import DeterministicDisabledTestVerifier

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def _request_context(**overrides: object) -> RequestContext:
    payload = {
        "request_id": "request-1",
        "trace_id": "trace-1",
        "correlation_id": "corr-1",
        "actor_id": "legacy-actor-header",
        "workspace_id": "workspace-1",
        "idempotency_key": "idem-1",
        "method": "GET",
        "path": "/health",
        "started_at": FIXED_NOW,
    }
    payload.update(overrides)
    return RequestContext(**payload)


def test_boundary_consumes_safe_correlation_and_ignores_actor_metadata() -> None:
    boundary = ProductionAuthRequestIdentityBoundary(
        DeterministicDisabledTestVerifier(
            clock=lambda: FIXED_NOW,
            id_factory=lambda prefix: f"{prefix}-fixed",
        ),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )
    context = _request_context()
    original = context.model_dump()

    bundle = asyncio.run(boundary.build_bundle(context))

    assert context.model_dump() == original
    assert bundle.request_id == "request-1"
    assert bundle.trace_id == "trace-1"
    assert bundle.correlation_id == "corr-1"
    assert bundle.identity_context.actor_id is None
    assert bundle.identity_context.authenticated is False
    assert bundle.audit_event.metadata["request_context_actor_ignored"] is True
    serialized = str(bundle.model_dump(mode="json"))
    assert "legacy-actor-header" not in serialized
    assert "workspace-1" not in serialized
    assert "idem-1" not in serialized


def test_boundary_builds_stable_correlated_evidence() -> None:
    boundary = ProductionAuthRequestIdentityBoundary(
        DeterministicDisabledTestVerifier(
            clock=lambda: FIXED_NOW,
            id_factory=lambda prefix: f"{prefix}-fixed",
        ),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )
    first = asyncio.run(boundary.build_bundle(_request_context()))
    second = asyncio.run(boundary.build_bundle(_request_context()))

    assert first.fingerprint == second.fingerprint
    assert first.verification.request_id == first.identity_context.request_id
    assert first.audit_event.request_id == first.provenance.request_id
    assert first.status.runtime_no_go_status is True


def test_boundary_bundle_build_performance_smoke() -> None:
    boundary = ProductionAuthRequestIdentityBoundary(
        DeterministicDisabledTestVerifier(
            clock=lambda: FIXED_NOW,
            id_factory=lambda prefix: f"{prefix}-fixed",
        ),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )

    async def run_many() -> None:
        for index in range(1000):
            bundle = await boundary.build_bundle(
                _request_context(
                    request_id=f"request-{index}",
                    trace_id=f"trace-{index}",
                    correlation_id=f"corr-{index}",
                )
            )
            assert bundle.identity_context.authenticated is False
            assert bundle.runtime_effect is False

    asyncio.run(run_many())
