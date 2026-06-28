from __future__ import annotations

from aion_brain.contracts.local_session import LocalSessionAuditRequest
from aion_brain.local_session.audit import LocalSessionAuditService


def test_local_session_audit_passes_safe_local_boundaries() -> None:
    result = LocalSessionAuditService().audit(
        LocalSessionAuditRequest(
            owner_scope=["workspace:main"],
            include_examples=True,
            created_by="local.operator",
        )
    )

    assert result.status == "passed"
    assert result.sessions_are_dev_only is True
    assert result.sessions_are_read_only is True
    assert result.credentials_absent is True
    assert result.tokens_absent is True
    assert result.cookies_absent is True
    assert result.persistence_absent is True
    assert result.production_auth_absent is True
    assert result.write_actions_disabled is True
    assert result.execution_disabled is True
    assert result.activation_disabled is True
    assert result.external_calls_disabled is True
