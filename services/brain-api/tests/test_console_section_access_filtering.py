from __future__ import annotations

from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService


def test_role_filter_removes_disallowed_sections_but_keeps_blockers() -> None:
    result = RolePermissionMatrixService().filter_view_for_roles(
        {
            "view": "overview",
            "sections": [
                {
                    "section_key": "admin_settings",
                    "metadata": {"required_roles": ["admin"]},
                    "items": [{"summary": "hidden"}],
                    "blockers": [{"blocker_key": "settings_read_only"}],
                    "forbidden_actions": [{"action_key": "hard_delete"}],
                },
                {
                    "section_key": "overview",
                    "items": [{"summary": "visible"}],
                    "allowed_actions": [],
                    "forbidden_actions": [{"action_key": "execute_tool"}],
                },
            ],
            "global_actions": [],
            "forbidden_actions": [{"action_key": "activate_module"}],
        },
        ["viewer"],
    )

    sections = result["sections"]
    assert result["metadata"]["removed_sections"] == ["admin_settings"]
    assert sections[0]["section_key"] == "admin_settings"
    assert sections[0]["status"] == "unavailable"
    assert sections[0]["items"] == []
    assert sections[0]["blockers"]
