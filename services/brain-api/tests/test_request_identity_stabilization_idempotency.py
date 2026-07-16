from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.api import RequestContext
from aion_brain.contracts.request_identity import RequestIdentityContext
from aion_brain.production_auth.request_boundary import ProductionAuthRequestIdentityBoundary
from aion_brain.production_auth.verifier import DeterministicDisabledTestVerifier

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def _boundary() -> ProductionAuthRequestIdentityBoundary:
    return ProductionAuthRequestIdentityBoundary(
        DeterministicDisabledTestVerifier(
            clock=lambda: FIXED_NOW,
            id_factory=lambda prefix: f"{prefix}-stable",
        ),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-stable",
    )


def _context(request_id: str) -> RequestContext:
    return RequestContext(
        request_id=request_id,
        trace_id="trace-stable",
        correlation_id="corr-stable",
        actor_id="actor-ignored",
        method="GET",
        path="/idempotent",
        started_at=FIXED_NOW,
    )


def test_deterministic_evidence_fingerprints_remain_stable_for_same_input() -> None:
    first = asyncio.run(_boundary().build_bundle(_context("request-stable")))
    second = asyncio.run(_boundary().build_bundle(_context("request-stable")))

    assert first.verification.fingerprint == second.verification.fingerprint
    assert first.identity_context.fingerprint == second.identity_context.fingerprint
    assert first.audit_event.fingerprint == second.audit_event.fingerprint
    assert first.provenance.fingerprint == second.provenance.fingerprint
    assert first.status.fingerprint == second.status.fingerprint
    assert first.fingerprint == second.fingerprint
    assert first.request_identity_middleware_implementation == "pure_asgi"
    assert first.stabilization_authorization_transaction_id == "AION-157-PA-0004"


def test_safety_relevant_field_changes_alter_fingerprint() -> None:
    first = asyncio.run(_boundary().build_bundle(_context("request-a")))
    second = asyncio.run(_boundary().build_bundle(_context("request-b")))

    assert first.fingerprint != second.fingerprint
    assert first.identity_context.fingerprint != second.identity_context.fingerprint


def test_fingerprint_excludes_itself_and_rejects_runtime_drift() -> None:
    context = asyncio.run(_boundary().build_bundle(_context("request-fp"))).identity_context
    payload = context.model_dump(mode="json", exclude={"fingerprint"})

    assert "fingerprint" not in payload
    with pytest.raises(ValidationError):
        RequestIdentityContext(**{**payload, "authenticated": True})
    with pytest.raises(ValidationError):
        RequestIdentityContext(
            **{
                **payload,
                "stabilization_authorization_transaction_id": "AION-157-PA-9999",
            }
        )
