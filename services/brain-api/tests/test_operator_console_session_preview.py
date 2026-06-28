from __future__ import annotations

from aion_brain.contracts.local_session import LocalSessionPreviewRequest
from aion_brain.contracts.operator_console import ConsoleViewModelRequest
from aion_brain.local_auth.access_matrix import ConsoleRoleFilter
from aion_brain.local_session.context import LocalSessionContextService
from aion_brain.local_session.preview import LocalSessionPreviewService
from aion_brain.operator_console.service import ConsoleViewModelService
from tests.kernel_fakes import AllowPolicy


def test_operator_console_accepts_local_session_context_for_role_filtering() -> None:
    preview = LocalSessionPreviewService().create_preview(
        LocalSessionPreviewRequest(roles=["viewer"], owner_scope=["workspace:main"])
    )
    session_context = LocalSessionContextService().build_context(preview)
    service = ConsoleViewModelService(
        container=object(),
        policy_adapter=AllowPolicy(),
        local_role_filter=ConsoleRoleFilter(),
    )

    model = service.get_view_model(
        ConsoleViewModelRequest(
            view="overview",
            owner_scope=["workspace:main"],
            metadata={"local_session_context": session_context.model_dump(mode="json")},
        )
    )

    assert model.read_only is True
    assert model.metadata["local_auth_role_filter_applied"] is True
    assert model.metadata["write_actions_enabled"] is False
