from __future__ import annotations

from aion_brain.contracts.local_auth import DevIdentitySimulationRequest
from aion_brain.contracts.operator_console import ConsoleViewModelRequest
from aion_brain.local_auth.access_matrix import ConsoleRoleFilter
from aion_brain.local_auth.context import build_local_auth_context
from aion_brain.local_auth.identity import build_local_operator_identity
from aion_brain.operator_console.service import ConsoleViewModelService
from tests.kernel_fakes import AllowPolicy


def test_operator_console_applies_local_role_filter_from_request_metadata() -> None:
    identity = build_local_operator_identity(
        DevIdentitySimulationRequest(
            actor_id="local.viewer",
            workspace_id="local",
            roles=["viewer"],
            owner_scope=["workspace:main"],
        )
    )
    context = build_local_auth_context(identity)
    service = ConsoleViewModelService(
        container=object(),
        policy_adapter=AllowPolicy(),
        local_role_filter=ConsoleRoleFilter(),
    )

    model = service.get_view_model(
        ConsoleViewModelRequest(
            view="overview",
            owner_scope=["workspace:main"],
            metadata={"local_auth_context": context.model_dump(mode="json")},
        )
    )

    assert model.read_only is True
    assert model.metadata["local_auth_role_filter_applied"] is True
    assert {action.action_type for action in model.global_actions} == {"read"}
