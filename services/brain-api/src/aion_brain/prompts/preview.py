"""Safe prompt preview service."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.prompts import (
    PromptCompileResult,
    PromptPacket,
    PromptPreview,
    PromptPreviewRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class PromptPreviewService:
    """Create safe prompt previews without exposing provider prompts."""

    def __init__(
        self,
        compiler: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._compiler = compiler
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> PromptPreviewService:
        return PromptPreviewService(
            self._compiler,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def preview(self, request: PromptPreviewRequest) -> PromptPreview:
        """Build a redacted, metadata-only, or hashes-only preview."""

        authorize(
            self._policy_adapter,
            action_type="prompt.preview",
            resource_type="prompt_packet",
            resource_id=request.prompt_packet_id,
            scope=request.owner_scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        packet: PromptPacket | None = None
        if request.compile_request is not None:
            compile_call = getattr(self._compiler, "compile", None)
            if callable(compile_call):
                result = compile_call(
                    request.compile_request.model_copy(update={"store_packet": False})
                )
                if isinstance(result, PromptCompileResult):
                    packet = result.prompt_packet
        elif request.prompt_packet_id:
            get_packet = getattr(self._compiler, "get_packet", None)
            if callable(get_packet):
                candidate = get_packet(request.prompt_packet_id, request.owner_scope)
                if isinstance(candidate, PromptPacket):
                    packet = candidate
        if packet is None:
            raise ValueError("prompt_packet_not_found")
        preview = _render_preview(packet, request.redaction_level)
        result = PromptPreview(
            preview_id=f"prompt-preview-{uuid4().hex}",
            prompt_packet_id=packet.prompt_packet_id,
            redaction_level=request.redaction_level,
            preview=preview,
            section_count=len(packet.section_manifests),
            token_estimate=packet.token_estimate,
            warnings=[],
            created_at=datetime.now(UTC),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="prompt_preview_created",
            node_type="prompt_packet",
            node_id=result.preview_id,
            trace_id=getattr(packet, "trace_id", None),
            intensity=0.35,
            payload={
                "prompt_packet_id": packet.prompt_packet_id,
                "redaction_level": request.redaction_level,
            },
        )
        return result


def _render_preview(packet: PromptPacket, redaction_level: str) -> str:
    if redaction_level == "hashes_only":
        return json.dumps(
            {
                "prompt_packet_id": packet.prompt_packet_id,
                "rendered_hash": packet.rendered_hash,
                "section_hashes": [
                    manifest.get("content_hash") for manifest in packet.section_manifests
                ],
            },
            sort_keys=True,
        )
    if redaction_level == "metadata_only":
        return json.dumps(
            {
                "prompt_packet_id": packet.prompt_packet_id,
                "status": packet.status,
                "packet_type": packet.packet_type,
                "section_count": len(packet.section_manifests),
                "token_estimate": packet.token_estimate,
            },
            sort_keys=True,
        )
    if packet.redacted_preview:
        return packet.redacted_preview
    if packet.sections:
        return "\n\n".join(section.content for section in packet.sections)
    return json.dumps(
        {"prompt_packet_id": packet.prompt_packet_id, "rendered_hash": packet.rendered_hash},
        sort_keys=True,
    )


__all__ = ["PromptPreviewService"]
