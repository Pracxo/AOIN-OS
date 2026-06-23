from __future__ import annotations

from aion_brain.local_auth.roles import LocalRoleService


def test_local_auth_roles_are_non_executing() -> None:
    service = LocalRoleService()

    viewer = service.permissions_for_roles(["viewer"])
    operator = service.permissions_for_roles(["operator"])
    reviewer = service.permissions_for_roles(["reviewer"])

    assert viewer["read_views"]
    assert viewer["dry_run_actions"] == []
    assert operator["dry_run_actions"] == [
        "acknowledge_notification",
        "dismiss_non_blocking_finding_with_reason",
        "run_dry_run_check",
    ]
    assert reviewer["review_actions"] == ["create_review_record"]
    assert operator["execute_allowed"] is False
    assert operator["activation_allowed"] is False
    assert reviewer["external_calls_allowed"] is False
