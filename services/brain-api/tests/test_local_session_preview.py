from __future__ import annotations

from aion_brain.contracts.local_session import LocalSessionPreviewRequest
from aion_brain.local_session.preview import LocalSessionPreviewService
from tests.kernel_fakes import FakeTelemetry


def test_local_session_preview_service_creates_safe_synthetic_preview() -> None:
    telemetry = FakeTelemetry()
    preview = LocalSessionPreviewService(telemetry_service=telemetry).create_preview(
        LocalSessionPreviewRequest(roles=["operator"], owner_scope=["workspace:main"])
    )

    assert preview.read_only is True
    assert preview.dev_only is True
    assert preview.production_session is False
    assert preview.credential_backed is False
    assert preview.token_issued is False
    assert preview.cookie_issued is False
    assert preview.persistent is False
    assert preview.write_allowed is False
    assert preview.execute_allowed is False
    assert preview.activation_allowed is False
    assert preview.external_calls_allowed is False
    assert telemetry.events[0].event_type == "local_session_preview_created"
