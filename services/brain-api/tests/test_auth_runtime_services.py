from __future__ import annotations

from aion_brain.auth_runtime import (
    AuthRuntimeGateService,
    AuthRuntimeQueryService,
    MockClaimsPreviewService,
)
from aion_brain.contracts.auth_runtime import MockClaimsPreviewRequest


def test_auth_runtime_gate_reports_disabled_status() -> None:
    status = AuthRuntimeGateService().status(["workspace:main"])

    assert status.production_auth_enabled is False
    assert status.auth_runtime_enabled is False
    assert status.token_issuance_enabled is False
    assert status.cookie_issuance_enabled is False
    assert status.session_persistence_enabled is False
    assert status.blockers


def test_auth_runtime_query_delegates_to_gate() -> None:
    gate = AuthRuntimeGateService()
    status = AuthRuntimeQueryService(gate).status(["workspace:main"])

    assert status.status_id == "auth-runtime-status-local"


def test_mock_claims_preview_maps_roles_without_authenticating() -> None:
    result = MockClaimsPreviewService().preview(
        MockClaimsPreviewRequest(
            subject="local.operator",
            roles=["operator"],
            claims={"claim_set": "local_demo"},
        )
    )

    assert result.status == "preview"
    assert result.production_identity is False
    assert result.credentials_present is False
    assert result.token_present is False
    assert result.cookie_present is False
    assert result.session_persisted is False
    assert result.actor_context_preview["preview_only"] is True
    assert result.actor_context_preview["authenticated"] is False
    assert result.role_decisions["write_allowed"] is False


def test_mock_claims_preview_blocks_unsafe_claim_payload() -> None:
    request = MockClaimsPreviewRequest.model_construct(
        trace_id=None,
        issuer="mock.local",
        subject="local.operator",
        audience="aion.local",
        roles=["operator"],
        workspace_id="local",
        owner_scope=["workspace:main"],
        claims={},
        mode="preview",
        metadata={"safe": "sk-example"},
        created_by=None,
    )
    result = MockClaimsPreviewService().preview(
        request
    )

    assert result.status == "blocked"
    assert result.blockers[0].blocker_type == "secret_detected"
