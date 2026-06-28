from __future__ import annotations

from aion_brain.auth_runtime import AuthRuntimeAuditService
from aion_brain.contracts.auth_runtime import AuthRuntimeAuditRequest


def test_auth_runtime_audit_passes_disabled_boundaries() -> None:
    result = AuthRuntimeAuditService().audit(
        AuthRuntimeAuditRequest(owner_scope=["workspace:main"], include_examples=True)
    )

    assert result.status == "passed"
    assert result.production_auth_disabled is True
    assert result.external_identity_disabled is True
    assert result.credentials_disabled is True
    assert result.token_issuance_disabled is True
    assert result.cookie_issuance_disabled is True
    assert result.session_persistence_disabled is True
    assert result.login_logout_absent is True
    assert result.mock_only is True
