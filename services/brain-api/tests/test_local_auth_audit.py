from __future__ import annotations

from aion_brain.contracts.local_auth import LocalAuthAuditRequest
from aion_brain.local_auth.audit import LocalAuthAuditService


def test_local_auth_audit_passes_safe_local_boundaries() -> None:
    result = LocalAuthAuditService().audit(
        LocalAuthAuditRequest(
            owner_scope=["workspace:main"],
            include_examples=True,
            created_by="local.operator",
        )
    )

    assert result.status == "passed"
    assert result.production_auth_absent is True
    assert result.credentials_absent is True
    assert result.sessions_absent is True
    assert result.external_identity_absent is True
    assert result.write_actions_disabled is True
    assert result.execution_disabled is True
    assert result.activation_disabled is True
