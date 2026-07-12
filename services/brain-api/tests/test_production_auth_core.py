from __future__ import annotations

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthPolicyRequest,
)
from aion_brain.production_auth import ProductionAuthCoreService


def test_production_auth_core_status_reports_implemented_disabled() -> None:
    status = ProductionAuthCoreService(ProductionAuthCoreConfig()).status()

    assert status.implementation_state == "implemented_disabled"
    assert status.production_auth_core_implemented is True
    assert status.implementation_present is True
    assert status.runtime_enabled is False
    assert status.runtime_guard_hold_active is True
    assert status.runtime_no_go_status is True


def test_production_auth_core_has_no_operational_auth_methods() -> None:
    service = ProductionAuthCoreService(ProductionAuthCoreConfig())

    for method_name in (
        "authenticate",
        "login",
        "logout",
        "callback",
        "issue_token",
        "refresh_token",
        "persist_session",
        "create_cookie",
        "call_provider",
    ):
        assert not hasattr(service, method_name)


def test_production_auth_core_policy_is_blocked_with_required_reasons() -> None:
    service = ProductionAuthCoreService(ProductionAuthCoreConfig())
    decision = service.evaluate_policy(
        ProductionAuthPolicyRequest(
            request_id="request-core",
            requested_operation="future_login",
        )
    )

    assert decision.outcome == "blocked"
    assert decision.runtime_effect is False
    assert "production_auth_runtime_disabled" in decision.reason_codes
    assert "runtime_enablement_guard_locked" in decision.reason_codes
    assert "authorization_scope_implementation_only" in decision.reason_codes
    assert "endpoint_surface_absent" in decision.reason_codes
    assert "protected_material_storage_absent" in decision.reason_codes
    assert "external_identity_provider_absent" in decision.reason_codes
