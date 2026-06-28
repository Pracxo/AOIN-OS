from __future__ import annotations

from aion_brain.contracts.local_session import LocalSessionPreviewRequest
from aion_brain.local_session.context import LocalSessionContextService
from aion_brain.local_session.preview import LocalSessionPreviewService


def test_local_session_context_uses_roles_without_granting_privilege() -> None:
    preview = LocalSessionPreviewService().create_preview(
        LocalSessionPreviewRequest(roles=["operator"], owner_scope=["workspace:main"])
    )
    context = LocalSessionContextService().build_context(preview)

    assert context.read_allowed is True
    assert context.dry_run_allowed is True
    assert context.write_allowed is False
    assert context.execute_allowed is False
    assert context.activation_allowed is False
    assert context.external_calls_allowed is False
    assert context.session_valid is True
    assert context.session_read_only is True
