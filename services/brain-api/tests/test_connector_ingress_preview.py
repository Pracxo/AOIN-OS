from __future__ import annotations

from aion_brain.connector_runtime import ConnectorIngressPreviewService
from aion_brain.contracts.connector_runtime import ConnectorIngressPreviewRequest


def test_connector_ingress_preview_is_untrusted_with_provenance() -> None:
    result = ConnectorIngressPreviewService().preview(
        ConnectorIngressPreviewRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            response_summary={"fields": ["case_id"]},
        )
    )

    assert result.trusted is False
    assert result.provenance_required is True
    assert result.redaction_applied is True
    assert result.prompt_injection_scan_required is True
