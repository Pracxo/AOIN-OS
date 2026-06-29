"""Mock connector ingress preview service."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.connector_runtime.blockers import blockers_for_findings
from aion_brain.connector_runtime.redaction import (
    payload_findings,
    redact_connector_runtime_payload,
)
from aion_brain.contracts.connector_runtime import (
    ConnectorIngressPreviewRequest,
    ConnectorIngressPreviewResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorIngressPreviewService:
    """Create local mock ingress previews without trusting connector data."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def preview(self, request: ConnectorIngressPreviewRequest) -> ConnectorIngressPreviewResult:
        """Return an untrusted ingress preview for synthetic connector response data."""

        preview_id = f"connector-ingress-preview-{uuid4().hex}"
        findings = [
            *payload_findings(request.response_summary),
            *payload_findings(request.metadata),
        ]
        redacted = redact_connector_runtime_payload(request.response_summary)
        result = ConnectorIngressPreviewResult(
            connector_ingress_preview_id=preview_id,
            trace_id=request.trace_id,
            connector_key=request.connector_key,
            status="blocked" if findings else "preview",
            trusted=False,
            provenance_required=True,
            redaction_applied=True,
            prompt_injection_scan_required=True,
            normalized_response_summary=redacted if isinstance(redacted, dict) else {},
            blockers=blockers_for_findings(findings, source_id=preview_id),
            warnings=[
                {"code": "connector_ingress_untrusted", "status": "open"},
                {"code": "prompt_injection_scan_required", "status": "open"},
            ],
            metadata={
                "preview_type": request.preview_type,
                "mock_only": True,
                "trusted_data_created": False,
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_ingress_preview_created",
            node_type="connector_ingress_preview",
            node_id=result.connector_ingress_preview_id,
            intensity=0.75,
            trace_id=result.trace_id,
            payload={"status": result.status, "trusted": False},
        )
        return result


__all__ = ["ConnectorIngressPreviewService"]
