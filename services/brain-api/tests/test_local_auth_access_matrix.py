from __future__ import annotations

from aion_brain.contracts.local_auth import ConsoleRoleFilterRequest, DevIdentitySimulationRequest
from aion_brain.local_auth.access_matrix import ConsoleRoleFilter
from aion_brain.local_auth.context import build_local_auth_context
from aion_brain.local_auth.identity import build_local_operator_identity


def test_console_role_filter_removes_disallowed_actions_and_redacts_payload() -> None:
    identity = build_local_operator_identity(
        DevIdentitySimulationRequest(
            actor_id="local.viewer",
            workspace_id="local",
            roles=["viewer"],
            owner_scope=["workspace:main"],
        )
    )
    context = build_local_auth_context(identity)

    result = ConsoleRoleFilter().filter(
        ConsoleRoleFilterRequest(
            view_model={
                "console_view_model_id": "console-view-1",
                "view": "overview",
                "status": "ready",
                "sections": [
                    {
                        "section_key": "safe",
                        "items": [{"summary": "visible", "raw_prompt": "private"}],
                        "allowed_actions": [
                            {"action_key": "run_dry_run_check", "action_type": "dry_run"},
                            {"action_key": "inspect_refs", "action_type": "read"},
                        ],
                    },
                    {
                        "section_key": "admin",
                        "metadata": {"required_roles": ["admin"]},
                    },
                ],
                "global_actions": [
                    {"action_key": "run_dry_run_check", "action_type": "dry_run"},
                    {"action_key": "inspect_refs", "action_type": "read"},
                ],
                "forbidden_actions": [{"action_key": "activate_module"}],
            },
            auth_context=context,
        )
    )

    assert result.read_only is True
    assert result.redaction_applied is True
    assert "admin" in result.removed_sections
    assert "run_dry_run_check" in result.removed_actions
    assert result.forbidden_actions == ["activate_module"]
    assert "raw_prompt" not in str(result.filtered_view_model)
