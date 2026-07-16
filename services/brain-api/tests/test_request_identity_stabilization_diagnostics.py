from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_request_identity_diagnostic_snapshot_exposes_stabilized_disabled_state() -> None:
    container = kernel_container()
    snapshot = container.production_auth_request_identity_boundary.diagnostic_snapshot(
        registered=True
    )

    assert snapshot.request_identity_boundary_implemented is True
    assert snapshot.request_identity_boundary_state == "implemented_disabled"
    assert snapshot.request_identity_boundary_default_enabled is False
    assert snapshot.request_identity_boundary_registered is True
    assert snapshot.request_identity_boundary_mode == "observe_only_disabled"
    assert snapshot.request_identity_middleware_implementation == "pure_asgi"
    assert snapshot.streaming_passthrough is True
    assert snapshot.request_body_passthrough is True
    assert snapshot.cancellation_propagation is True
    assert snapshot.non_http_scope_bypass is True
    assert snapshot.duplicate_registration_prevented is True
    assert snapshot.identity_verification_enabled is False
    assert snapshot.authenticated_requests_enabled is False
    assert snapshot.production_auth_runtime_enabled is False
    assert snapshot.runtime_effect is False
    assert snapshot.runtime_no_go_status is True
    assert snapshot.implementation_authorization_transaction_id == "AION-155-PA-0003"
    assert snapshot.stabilization_authorization_transaction_id == "AION-157-PA-0004"
    serialized = str(snapshot.model_dump(mode="json"))
    assert "actor-1" not in serialized
    assert "cookie=value" not in serialized.casefold()
    assert "bearer " not in serialized.casefold()


def test_kernel_diagnostics_include_stabilization_checks() -> None:
    container = kernel_container()
    checks = {
        check.name: check.status
        for check in KernelDiagnostics(container).run()
        if check.component == "production_auth_request_identity"
    }

    assert checks["request_identity_middleware_pure_asgi"] == "passed"
    assert checks["request_identity_streaming_and_body_passthrough"] == "passed"
    assert checks["request_identity_cancellation_and_non_http_bypass"] == "passed"
    assert checks["request_identity_duplicate_registration_prevented"] == "passed"
    assert checks["request_identity_stabilization_authorization"] == "passed"
