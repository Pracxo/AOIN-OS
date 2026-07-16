from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthPolicyRequest,
)
from aion_brain.production_auth import ProductionAuthCoreService

FIXED_NOW = datetime(2026, 7, 13, 11, 0, 0, tzinfo=UTC)


def test_identical_canonical_inputs_produce_identical_evidence_fingerprints() -> None:
    service = ProductionAuthCoreService(
        ProductionAuthCoreConfig(),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-idempotent",
    )
    request = ProductionAuthPolicyRequest(
        request_id="request-idempotent",
        requested_operation="policy_evaluation_preview",
    )

    first_decision = service.evaluate_policy(request)
    second_decision = service.evaluate_policy(request)
    first_audit = service.build_audit_event(event_type="guard_check", decision=first_decision)
    second_audit = service.build_audit_event(event_type="guard_check", decision=second_decision)
    first_provenance = service.build_provenance_record(
        source_refs=["docs/auth/production-auth-canonical-evidence.md"]
    )
    second_provenance = service.build_provenance_record(
        source_refs=["docs/auth/production-auth-canonical-evidence.md"]
    )
    first_diagnostic = service.diagnostic_snapshot()
    second_diagnostic = service.diagnostic_snapshot()

    assert first_decision.fingerprint == second_decision.fingerprint
    assert first_audit.fingerprint == second_audit.fingerprint
    assert first_provenance.fingerprint == second_provenance.fingerprint
    assert first_diagnostic.fingerprint == second_diagnostic.fingerprint


def test_policy_fingerprint_changes_when_internal_operation_changes() -> None:
    service = ProductionAuthCoreService(
        ProductionAuthCoreConfig(),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-idempotent",
    )

    first = service.evaluate_policy(
        ProductionAuthPolicyRequest(
            request_id="request-operation",
            requested_operation="policy_evaluation_preview",
        )
    )
    second = service.evaluate_policy(
        ProductionAuthPolicyRequest(
            request_id="request-operation",
            requested_operation="configuration_validation",
        )
    )

    assert first.fingerprint != second.fingerprint
