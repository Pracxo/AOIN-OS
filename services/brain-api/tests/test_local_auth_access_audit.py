from __future__ import annotations

from aion_brain.local_auth.access_audit import RoleAccessAuditService


def test_role_access_audit_passes_safety_booleans() -> None:
    result = RoleAccessAuditService().audit()

    assert result.status == "passed"
    assert result.forbidden_actions_visible is True
    assert result.write_actions_absent is True
    assert result.execution_absent is True
    assert result.activation_absent is True
    assert result.external_calls_absent is True
    assert result.redaction_applied is True
    assert "system_service" in result.roles_checked
