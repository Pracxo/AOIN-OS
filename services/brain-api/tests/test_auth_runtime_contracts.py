from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.auth_runtime import (
    AuthRuntimeAuditRequest,
    AuthRuntimeAuditResult,
    AuthRuntimeStatus,
    MockClaimsPreviewRequest,
    MockClaimsPreviewResult,
    utc_now,
)


def test_auth_runtime_status_requires_disabled_flags() -> None:
    status = AuthRuntimeStatus(
        status_id="auth-runtime-status-test",
        production_auth_enabled=False,
        auth_runtime_enabled=False,
        mock_claims_preview_enabled=True,
        external_identity_provider_enabled=False,
        credentials_enabled=False,
        token_issuance_enabled=False,
        cookie_issuance_enabled=False,
        session_persistence_enabled=False,
        login_endpoint_enabled=False,
        logout_endpoint_enabled=False,
        actor_mapping_preview_enabled=True,
        blockers=[],
        warnings=[],
        metadata={"disabled_by_default": True},
        created_at=utc_now(),
    )

    assert status.production_auth_enabled is False
    assert status.auth_runtime_enabled is False

    with pytest.raises(ValidationError):
        AuthRuntimeStatus(
            **status.model_copy(update={"production_auth_enabled": True}).model_dump()
        )


def test_mock_claims_request_is_mock_only_and_role_checked() -> None:
    request = MockClaimsPreviewRequest(
        issuer="mock.local",
        subject="local.operator",
        roles=["operator"],
    )

    assert request.mode == "preview"
    assert request.owner_scope == ["workspace:main"]

    with pytest.raises(ValidationError):
        MockClaimsPreviewRequest(
            issuer="prod.example",
            subject="local.operator",
            roles=["operator"],
        )

    with pytest.raises(ValidationError):
        MockClaimsPreviewRequest(subject="local.operator", roles=["root"])


def test_mock_claims_result_cannot_contain_auth_material() -> None:
    result = MockClaimsPreviewResult(
        mock_claims_preview_id="mock-claims-preview-test",
        status="preview",
        issuer="mock.local",
        subject="local.operator",
        audience="aion.local",
        roles=["operator"],
        workspace_id="local",
        owner_scope=["workspace:main"],
        production_identity=False,
        credentials_present=False,
        token_present=False,
        cookie_present=False,
        session_persisted=False,
        actor_context_preview={"preview_only": True},
        role_decisions={"write_allowed": False},
        created_at=utc_now(),
    )

    assert result.actor_context_preview["preview_only"] is True

    with pytest.raises(ValidationError):
        MockClaimsPreviewResult(
            **result.model_copy(update={"token_present": True}).model_dump()
        )


def test_auth_runtime_audit_result_requires_all_disabled_proofs() -> None:
    request = AuthRuntimeAuditRequest(owner_scope=["workspace:main"])
    result = AuthRuntimeAuditResult(
        auth_runtime_audit_id="auth-runtime-audit-test",
        trace_id=request.trace_id,
        status="passed",
        owner_scope=request.owner_scope,
        checks_run=["production_auth_disabled"],
        findings=[],
        production_auth_disabled=True,
        external_identity_disabled=True,
        credentials_disabled=True,
        token_issuance_disabled=True,
        cookie_issuance_disabled=True,
        session_persistence_disabled=True,
        login_logout_absent=True,
        mock_only=True,
        created_at=utc_now(),
    )

    assert result.mock_only is True

    with pytest.raises(ValidationError):
        AuthRuntimeAuditResult(
            **result.model_copy(update={"credentials_disabled": False}).model_dump()
        )
