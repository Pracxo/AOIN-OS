from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.production_auth import (
    PROHIBITED_RUNTIME_FIELDS,
    ProductionAuthAuditEvent,
    ProductionAuthCoreConfig,
    ProductionAuthPolicyDecision,
    ProductionAuthPolicyRequest,
    ProductionAuthProvenanceRecord,
    utc_now,
)


def test_production_auth_core_config_accepts_disabled_defaults() -> None:
    config = ProductionAuthCoreConfig()

    assert config.production_auth_core_implemented is True
    assert config.production_auth_core_state == "implemented_disabled"
    assert config.implementation_present is True
    assert config.runtime_enabled is False
    assert config.authorization_transaction_id == "AION-151-PA-0001"
    assert config.authorization_scope == "disabled-production-auth-core"


def test_production_auth_core_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthCoreConfig(unexpected=True)


def test_production_auth_core_config_rejects_each_runtime_true_flag() -> None:
    base = ProductionAuthCoreConfig().model_dump()

    for field_name in PROHIBITED_RUNTIME_FIELDS:
        with pytest.raises(ValidationError), pytest.MonkeyPatch.context():
            ProductionAuthCoreConfig(**{**base, field_name: True})


def test_production_auth_contracts_reject_protected_material_payloads() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthPolicyRequest(
            request_id="request-unsafe",
            requested_operation="core_status_read",
            metadata={"access_token": "redacted-demo"},
        )

    with pytest.raises(ValidationError):
        ProductionAuthPolicyRequest(
            request_id="request-claims",
            requested_operation="core_status_read",
            metadata={"raw_claims": {"sub": "demo"}},
        )


def test_production_auth_policy_decision_cannot_allow_or_have_runtime_effect() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthPolicyDecision(
            decision_id="decision-allow",
            request_id="request-allow",
            outcome="allowed",
            runtime_effect=False,
            created_at=utc_now(),
        )

    with pytest.raises(ValidationError):
        ProductionAuthPolicyDecision(
            decision_id="decision-effect",
            request_id="request-effect",
            outcome="blocked",
            runtime_effect=True,
            created_at=utc_now(),
        )


def test_audit_and_provenance_require_redacted_zero_effect_records() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthAuditEvent(
            event_id="event-effect",
            event_type="policy_evaluation_preview",
            request_id="request-effect",
            outcome="blocked",
            runtime_effect=True,
            redacted=True,
            created_at=utc_now(),
        )

    with pytest.raises(ValidationError):
        ProductionAuthAuditEvent(
            event_id="event-unredacted",
            event_type="policy_evaluation_preview",
            request_id="request-unredacted",
            outcome="blocked",
            runtime_effect=False,
            redacted=False,
            created_at=utc_now(),
        )

    with pytest.raises(ValidationError):
        ProductionAuthProvenanceRecord(
            provenance_id="prov-unredacted",
            source_refs=["docs/adr/0143-v02-disabled-production-auth-core-implementation.md"],
            runtime_effect=False,
            redacted=False,
            created_at=utc_now(),
        )
