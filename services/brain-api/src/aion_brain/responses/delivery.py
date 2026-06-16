"""Local-only response delivery records."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.responses import ResponseDeliveryRecord
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.repository import DialogueRepository


class ResponseDeliveryService:
    """Record local response delivery without external communication."""

    def __init__(
        self,
        repository: DialogueRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def deliver_api_return(
        self,
        response_id: str,
        dialogue_session_id: str | None,
        trace_id: str | None,
    ) -> ResponseDeliveryRecord:
        """Record a local API return delivery."""

        response = self._repository.get_response(response_id)
        if response is None:
            raise ValueError("response_not_found")
        scope = _scope_from_response(response)
        authorize(
            self._policy_adapter,
            action_type="dialogue.response.deliver",
            resource_type="response",
            resource_id=response_id,
            scope=scope,
            trace_id=trace_id or response.trace_id,
            risk_level="low",
            context={"delivery_type": "api_return", "external_delivery": False},
        )
        delivery = ResponseDeliveryRecord(
            delivery_id=f"response-delivery-{uuid4().hex}",
            response_id=response.response_id,
            dialogue_session_id=dialogue_session_id or response.dialogue_session_id,
            trace_id=trace_id or response.trace_id,
            delivery_type="api_return",
            status="delivered",
            delivered_to=None,
            output_channel="api",
            payload={"response_id": response.response_id, "status": response.status},
            metadata={"local_record_only": True},
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_delivery(delivery)
        self._repository.save_response(
            response.model_copy(update={"status": "delivered", "updated_at": datetime.now(UTC)})
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="response_delivered",
            node_type="response",
            node_id=response.response_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            payload={"owner_scope": scope, "delivery_type": stored.delivery_type},
        )
        return stored

    def list_deliveries(
        self,
        response_id: str | None = None,
        dialogue_session_id: str | None = None,
    ) -> list[ResponseDeliveryRecord]:
        """List local delivery records."""

        return self._repository.list_deliveries(
            response_id=response_id,
            dialogue_session_id=dialogue_session_id,
        )


def _scope_from_response(response: object) -> list[str]:
    metadata = getattr(response, "metadata", {})
    if isinstance(metadata, dict):
        raw = metadata.get("owner_scope") or metadata.get("scope")
        if isinstance(raw, list):
            values = [str(item) for item in raw]
            if values:
                return values
    return ["workspace:main"]
