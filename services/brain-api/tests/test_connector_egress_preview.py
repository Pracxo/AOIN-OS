from __future__ import annotations

from aion_brain.connector_runtime import ConnectorEgressPreviewService
from aion_brain.contracts.connector_runtime import ConnectorEgressPreviewRequest


def test_connector_egress_preview_is_always_blocked() -> None:
    result = ConnectorEgressPreviewService().preview(
        ConnectorEgressPreviewRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            payload_summary={"fields": ["case_id"]},
        )
    )

    assert result.egress_allowed is False
    assert result.external_call_allowed is False
    assert result.credentials_present is False
    assert result.status == "blocked"
