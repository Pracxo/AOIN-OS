from __future__ import annotations

from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService


def test_forbidden_activation_and_execution_actions_remain_visible() -> None:
    service = RolePermissionMatrixService()
    activation = service.decide(
        "viewer",
        "module_activation",
        action_key="activate_module",
    )
    execution = service.decide(
        "operator",
        "operator_actions",
        action_key="execute_tool",
    )

    assert activation.decision == "visible_forbidden"
    assert activation.activation_allowed is False
    assert execution.decision == "visible_forbidden"
    assert execution.execute_allowed is False

    result = service.filter_view_for_roles(
        {
            "view": "module_activation",
            "sections": [],
            "global_actions": [],
            "forbidden_actions": [
                {"action_key": "activate_module"},
                {"action_key": "execute_tool"},
            ],
        },
        ["viewer"],
    )
    assert {item["action_key"] for item in result["forbidden_actions"]} == {
        "activate_module",
        "execute_tool",
    }
    assert result["metadata"]["forbidden_actions_visible"] is True
