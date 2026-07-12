from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthPolicyRequest,
)
from aion_brain.production_auth import ProductionAuthCoreService

ROOT = Path(__file__).resolve().parents[3]


def test_production_auth_audit_event_is_redacted_and_traceable() -> None:
    service = ProductionAuthCoreService(ProductionAuthCoreConfig())
    decision = service.evaluate_policy(
        ProductionAuthPolicyRequest(
            request_id="request-audit",
            requested_operation="guard_check",
        )
    )
    event = service.build_audit_event(event_type="guard_check", decision=decision)

    assert event.redacted is True
    assert event.runtime_effect is False
    assert event.authorization_transaction_id == "AION-151-PA-0001"
    assert "production_auth_runtime_disabled" in event.reason_codes


def test_production_auth_provenance_record_is_redacted_and_scoped() -> None:
    service = ProductionAuthCoreService(ProductionAuthCoreConfig())
    record = service.build_provenance_record(
        source_refs=[
            "docs/adr/0143-v02-disabled-production-auth-core-implementation.md",
            "docs/release/v02-production-auth-core-implementation.md",
        ],
        metadata={"evidence_kind": "implementation_only"},
    )

    assert record.redacted is True
    assert record.runtime_effect is False
    assert record.implementation_task == "AION-152"
    assert record.authorization_scope == "disabled-production-auth-core"


def test_production_auth_examples_are_valid_synthetic_json() -> None:
    for relative in [
        "examples/auth/production-auth-core-config.json",
        "examples/auth/production-auth-core-status.json",
        "examples/auth/production-auth-policy-decision.json",
        "examples/auth/production-auth-audit-event.json",
        "examples/auth/production-auth-provenance-record.json",
    ]:
        payload = json.loads((ROOT / relative).read_text())
        assert payload["synthetic"] is True
        assert payload["authorization_transaction_id"] == "AION-151-PA-0001"
        assert payload["authorization_scope"] == "disabled-production-auth-core"
        assert payload["implementation_task"] == "AION-152"
        assert payload["production_auth_core_implemented"] is True
        assert payload["production_auth_runtime_enabled"] is False
        serialized = json.dumps(payload, sort_keys=True).lower()
        for marker in ("sk-", "ghp_", "xoxb-", "bearer ", "private_key"):
            assert marker not in serialized
