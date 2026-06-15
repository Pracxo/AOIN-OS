"""Runtime permission grant tests."""

from tests.sandbox_fakes import make_sandbox_service, profile_request, runtime_permission_request


def test_runtime_permission_grant_and_revoke_work() -> None:
    service = make_sandbox_service()
    service.create_profile(profile_request())

    grant = service.grant_runtime_permission(runtime_permission_request())
    listed = service.list_runtime_permissions(target_type="capability", target_id="test.echo")
    revoked = service.revoke_runtime_permission(
        grant.runtime_permission_id,
        "dev",
        "no longer required",
    )

    assert grant.status == "active"
    assert listed[0].runtime_permission_id == grant.runtime_permission_id
    assert revoked.status == "revoked"
