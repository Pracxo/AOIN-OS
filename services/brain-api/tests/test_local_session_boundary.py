from __future__ import annotations

from aion_brain.contracts.local_session import LocalSessionPreviewRequest
from aion_brain.local_session.boundary import LocalSessionBoundaryService
from aion_brain.local_session.preview import LocalSessionPreviewService


def test_local_session_boundary_passes_safe_preview() -> None:
    preview = LocalSessionPreviewService().create_preview(
        LocalSessionPreviewRequest(owner_scope=["workspace:main"])
    )
    result = LocalSessionBoundaryService().check(preview)

    assert result.status == "passed"
    assert result.read_only_passed is True
    assert result.dev_only_passed is True
    assert result.no_credentials_passed is True
    assert result.no_tokens_passed is True
    assert result.no_cookies_passed is True
    assert result.no_persistence_passed is True
    assert result.no_execution_passed is True
    assert result.no_activation_passed is True
    assert result.no_external_calls_passed is True
