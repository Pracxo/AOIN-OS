from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthPolicyDecision,
    ProductionAuthPolicyRequest,
)
from aion_brain.production_auth import ProductionAuthCoreService
from aion_brain.production_auth.canonical import sha256_fingerprint

FIXED_NOW = datetime(2026, 7, 13, 10, 0, 0, tzinfo=UTC)


def _service() -> ProductionAuthCoreService:
    return ProductionAuthCoreService(
        ProductionAuthCoreConfig(),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )


def test_evidence_fingerprints_are_deterministic_and_self_excluding() -> None:
    service = _service()
    status = service.status()
    decision = service.evaluate_policy(
        ProductionAuthPolicyRequest(
            request_id="request-fingerprint",
            requested_operation="policy_evaluation_preview",
        )
    )
    audit = service.build_audit_event(event_type="guard_check", decision=decision)
    provenance = service.build_provenance_record(
        source_refs=["docs/adr/0145-v02-production-auth-core-stabilization.md"]
    )
    diagnostic = service.diagnostic_snapshot()

    for item in (status, decision, audit, provenance, diagnostic):
        assert item.fingerprint is not None
        assert len(item.fingerprint) == 64
        payload = item.model_dump(mode="json", exclude={"fingerprint"})
        assert item.fingerprint == sha256_fingerprint(payload)


def test_fingerprint_is_stable_for_identical_inputs_and_changes_for_safety_change() -> None:
    service = _service()
    request = ProductionAuthPolicyRequest(
        request_id="request-stable",
        requested_operation="policy_evaluation_preview",
    )

    first = service.evaluate_policy(request)
    second = service.evaluate_policy(request)
    changed = ProductionAuthPolicyDecision(
        decision_id=first.decision_id,
        request_id=first.request_id,
        requested_operation=first.requested_operation,
        outcome="denied",
        created_at=first.created_at,
    )

    assert first.fingerprint == second.fingerprint
    assert changed.fingerprint != first.fingerprint


def test_incorrect_supplied_fingerprint_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthPolicyDecision(
            decision_id="decision-bad-fingerprint",
            request_id="request-bad-fingerprint",
            requested_operation="policy_evaluation_preview",
            outcome="blocked",
            created_at=FIXED_NOW,
            fingerprint="0" * 64,
        )
