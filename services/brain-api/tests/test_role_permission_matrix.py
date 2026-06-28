from __future__ import annotations

from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService


def test_permission_matrix_includes_all_local_roles() -> None:
    matrix = RolePermissionMatrixService().build_permission_matrix()

    assert set(matrix["roles"]) == {
        "viewer",
        "operator",
        "reviewer",
        "admin",
        "auditor",
        "system_service",
    }
    assert "system_service" not in matrix["static_console_roles"]
    assert matrix["write_allowed"] is False
    assert matrix["execute_allowed"] is False
    assert matrix["activation_allowed"] is False
    assert matrix["external_calls_allowed"] is False


def test_unknown_role_and_view_fail_closed() -> None:
    service = RolePermissionMatrixService()

    unknown_role = service.decide("unknown", "overview")
    unknown_view = service.decide("viewer", "unknown_view")

    assert unknown_role.decision == "denied"
    assert unknown_role.read_allowed is False
    assert unknown_view.decision == "denied"
    assert unknown_view.read_allowed is False


def test_role_specific_descriptor_permissions_remain_unprivileged() -> None:
    service = RolePermissionMatrixService()

    viewer = service.decide("viewer", "overview", action_key="run_dry_run_check")
    operator = service.decide("operator", "operator_actions", action_key="run_dry_run_check")
    reviewer = service.decide("reviewer", "operator_actions", action_key="create_review_record")
    auditor = service.decide("auditor", "audit_provenance", action_key="create_review_record")
    admin = service.decide("admin", "settings_safety", action_key="enable_production_auth")

    assert viewer.decision == "denied"
    assert operator.dry_run_allowed is True
    assert operator.execute_allowed is False
    assert reviewer.review_allowed is True
    assert reviewer.execute_allowed is False
    assert auditor.decision == "denied"
    assert admin.decision == "denied"
    assert admin.activation_allowed is False
