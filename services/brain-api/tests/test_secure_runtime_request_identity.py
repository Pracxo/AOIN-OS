from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_request_identity_is_derived_from_signed_claims_only() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.request_identity.actor_id == "operator-AION-231"
    assert fixture.request_identity.workspace_id == "workspace-AION-231"
    assert fixture.request_identity.header_identity_used is False
    assert fixture.request_identity.cookie_identity_used is False
    assert fixture.request_identity.token_identity_used is False
    assert fixture.request_identity.external_identity_provider_used is False
