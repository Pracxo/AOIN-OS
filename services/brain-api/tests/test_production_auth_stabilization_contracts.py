from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.production_auth import (
    CANONICALIZATION_VERSION,
    POLICY_VERSION,
    REASON_CODE_REGISTRY_VERSION,
    SCHEMA_VERSION,
    STABILIZATION_AUTHORIZATION_SCOPE,
    STABILIZATION_AUTHORIZATION_TASK,
    STABILIZATION_AUTHORIZATION_TRANSACTION_ID,
    ProductionAuthAuditEvent,
    ProductionAuthCoreConfig,
    ProductionAuthPolicyDecision,
    ProductionAuthPolicyRequest,
    ProductionAuthProvenanceRecord,
)


def test_stabilization_lineage_is_separate_from_historical_implementation_lineage() -> None:
    config = ProductionAuthCoreConfig()

    assert config.implementation_authorization_transaction_id == "AION-151-PA-0001"
    assert config.implementation_authorization_task == "AION-152"
    assert config.implementation_authorization_scope == "disabled-production-auth-core"
    assert config.stabilization_authorization_transaction_id == "AION-153-PA-0002"
    assert config.stabilization_authorization_task == "AION-154"
    assert (
        config.stabilization_authorization_scope
        == "disabled-production-auth-core-stabilization"
    )
    assert config.stabilization_authorization_reusable is False
    assert config.stabilization_authorization_expires_on_aion_154_merge is True


def test_contracts_expose_stable_version_fields_and_reject_unknown_versions() -> None:
    request = ProductionAuthPolicyRequest(
        request_id="request-versioned",
        requested_operation="policy_evaluation_preview",
    )

    assert request.schema_version == SCHEMA_VERSION
    assert request.canonicalization_version == CANONICALIZATION_VERSION
    assert request.policy_version == POLICY_VERSION
    assert request.reason_code_registry_version == REASON_CODE_REGISTRY_VERSION

    with pytest.raises(ValidationError):
        ProductionAuthCoreConfig(schema_version="production-auth-core/v2")


def test_unknown_preview_operations_fail_closed() -> None:
    for operation in (
        "login",
        "logout",
        "callback",
        "authenticate",
        "issue_token",
        "refresh_token",
        "persist_session",
        "create_cookie",
        "provider_call",
    ):
        with pytest.raises(ValidationError):
            ProductionAuthPolicyRequest(
                request_id=f"request-{operation}",
                requested_operation=operation,
            )


def test_evidence_models_are_immutable_after_construction() -> None:
    decision = ProductionAuthPolicyDecision(
        decision_id="decision-immutable",
        request_id="request-immutable",
        requested_operation="guard_check",
        outcome="blocked",
        created_at=datetime(2026, 7, 13, tzinfo=UTC),
        metadata={"scope": "internal"},
    )
    event = ProductionAuthAuditEvent(
        event_id="event-immutable",
        event_type="guard_check",
        request_id="request-immutable",
        outcome="blocked",
        created_at=datetime(2026, 7, 13, tzinfo=UTC),
        metadata={"policy_version": POLICY_VERSION},
    )
    record = ProductionAuthProvenanceRecord(
        provenance_id="prov-immutable",
        source_refs=("docs/adr/0145-v02-production-auth-core-stabilization.md",),
        created_at=datetime(2026, 7, 13, tzinfo=UTC),
    )

    with pytest.raises(ValidationError):
        decision.outcome = "denied"  # type: ignore[misc]
    with pytest.raises(TypeError):
        event.metadata["leak"] = "blocked"
    with pytest.raises(ValidationError):
        record.source_refs = ("docs/other.md",)  # type: ignore[misc]


def test_evidence_models_include_stabilization_authorization_fields() -> None:
    decision = ProductionAuthPolicyDecision(
        decision_id="decision-lineage",
        request_id="request-lineage",
        requested_operation="policy_evaluation_preview",
        outcome="blocked",
        created_at=datetime(2026, 7, 13, tzinfo=UTC),
    )

    assert decision.stabilization_authorization_transaction_id == (
        STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    )
    assert decision.stabilization_authorization_task == STABILIZATION_AUTHORIZATION_TASK
    assert decision.stabilization_authorization_scope == STABILIZATION_AUTHORIZATION_SCOPE
    assert decision.stabilization_authorization_reusable is False
    assert decision.stabilization_authorization_expires_on_aion_154_merge is True
