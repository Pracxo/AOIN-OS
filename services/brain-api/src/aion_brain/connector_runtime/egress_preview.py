"""Mock connector egress preview service."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.connector_runtime.blockers import blocker, blockers_for_findings
from aion_brain.connector_runtime.redaction import (
    payload_findings,
    redact_connector_runtime_payload,
)
from aion_brain.contracts.connector_runtime import (
    ConnectorEgressPreviewRequest,
    ConnectorEgressPreviewResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorEgressPreviewService:
    """Create local mock egress previews without making external calls."""

    def __init__(
        self,
        *,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._settings = settings
        self._telemetry_service = telemetry_service

    def preview(self, request: ConnectorEgressPreviewRequest) -> ConnectorEgressPreviewResult:
        """Return a blocked egress preview for a mock connector payload."""

        preview_id = f"connector-egress-preview-{uuid4().hex}"
        findings = [
            *payload_findings(request.payload_summary),
            *payload_findings(request.metadata),
        ]
        blockers = blockers_for_findings(findings, source_id=preview_id)
        if bool(getattr(self._settings, "connector_external_calls_enabled", False)):
            blockers.append(
                blocker(
                    "external_calls_disabled",
                    "connector_external_calls_must_remain_disabled",
                    source_type="settings",
                    source_id=preview_id,
                    severity="critical",
                )
            )
        blockers.append(
            blocker(
                "external_calls_disabled",
                "egress_preview_does_not_call_external_systems",
                source_type="connector_egress_preview",
                source_id=preview_id,
                severity="high",
            )
        )
        redacted = redact_connector_runtime_payload(request.payload_summary)
        result = ConnectorEgressPreviewResult(
            connector_egress_preview_id=preview_id,
            trace_id=request.trace_id,
            connector_key=request.connector_key,
            status="blocked",
            egress_allowed=False,
            external_call_allowed=False,
            credentials_present=False,
            blocked_fields=sorted(
                {str(item.get("field")) for item in findings if item.get("field")}
            ),
            blockers=blockers,
            warnings=[{"code": "egress_preview_only", "status": "open"}],
            redacted_payload_summary=redacted if isinstance(redacted, dict) else {},
            metadata={
                "preview_type": request.preview_type,
                "mock_only": True,
                "network_call_performed": False,
                "external_calls_enabled": False,
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_egress_preview_created",
            node_type="connector_egress_preview",
            node_id=result.connector_egress_preview_id,
            intensity=0.8,
            trace_id=result.trace_id,
            payload={"status": result.status, "external_call_allowed": False},
        )
        return result


__all__ = ["ConnectorEgressPreviewService"]
