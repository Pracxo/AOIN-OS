from __future__ import annotations

from aion_brain.contracts.operator_console import ConsoleViewModelRequest
from aion_brain.local_auth.console_filter import ConsoleRoleFilter
from aion_brain.operator_console.service import ConsoleViewModelService
from tests.kernel_fakes import AllowPolicy


def test_console_view_model_service_applies_roles_metadata() -> None:
    service = ConsoleViewModelService(
        container=object(),
        policy_adapter=AllowPolicy(),
        local_role_filter=ConsoleRoleFilter(),
    )

    model = service.get_view_model(
        ConsoleViewModelRequest(
            view="settings_safety",
            owner_scope=["workspace:main"],
            metadata={"roles": ["viewer"]},
        )
    )

    assert model.read_only is True
    assert model.metadata["role_access_filter_applied"] is True
    assert model.metadata["write_allowed"] is False
    assert model.metadata["execute_allowed"] is False
    assert model.metadata["removed_sections"]
    assert model.forbidden_actions
