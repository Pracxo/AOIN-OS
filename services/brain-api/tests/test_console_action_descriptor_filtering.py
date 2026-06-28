from __future__ import annotations

from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService


def test_role_filter_removes_disallowed_actions() -> None:
    service = RolePermissionMatrixService()
    result = service.filter_view_for_roles(
        {
            "view": "operator_actions",
            "sections": [
                {
                    "section_key": "actions",
                    "allowed_actions": [
                        {"action_key": "run_dry_run_check", "action_type": "dry_run"},
                        {"action_key": "create_review_record", "action_type": "review_record"},
                        {"action_key": "inspect_refs", "action_type": "read"},
                    ],
                    "forbidden_actions": [{"action_key": "execute_tool"}],
                }
            ],
            "global_actions": [
                {"action_key": "run_dry_run_check", "action_type": "dry_run"},
                {"action_key": "inspect_refs", "action_type": "read"},
            ],
            "forbidden_actions": [{"action_key": "activate_module"}],
        },
        ["operator"],
    )

    section_actions = {item["action_key"] for item in result["sections"][0]["allowed_actions"]}
    global_actions = {item["action_key"] for item in result["global_actions"]}

    assert "run_dry_run_check" in section_actions
    assert "inspect_refs" in section_actions
    assert "create_review_record" not in section_actions
    assert global_actions == {"run_dry_run_check", "inspect_refs"}
    assert "create_review_record" in result["metadata"]["removed_actions"]
