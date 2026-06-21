"""Tool intent capture service for model output governance."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.model_outputs import ModelOutputSegment, ToolIntentCandidate
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.model_outputs.hash import hash_model_output
from aion_brain.model_outputs.redaction import redact_output_payload


class ToolIntentCaptureService:
    """Capture model-suggested tool intents without executing them."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ToolIntentCaptureService:
        return ToolIntentCaptureService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def capture_from_segments(
        self,
        model_output_id: str,
        segments: list[ModelOutputSegment],
    ) -> list[ToolIntentCandidate]:
        """Capture tool-intent-looking segments as blocked candidate records."""

        if self._settings is not None and not bool(
            getattr(self._settings, "tool_intent_capture_enabled", True)
        ):
            return []
        authorize(
            self._policy_adapter,
            action_type="model_output.tool_intent.create",
            resource_type="tool_intent",
            resource_id=model_output_id,
            scope=["workspace:main"],
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
        )
        intents: list[ToolIntentCandidate] = []
        for segment in segments:
            if segment.segment_type != "tool_intent":
                continue
            payload = _parse_tool_payload(segment.content)
            arguments, findings = redact_output_payload(payload.get("arguments", {}))
            intent_type = _intent_type(segment.content)
            execution_enabled = bool(
                getattr(self._settings, "tool_intent_execution_enabled", False)
            )
            intent = ToolIntentCandidate(
                tool_intent_id=f"tool-intent-{uuid4().hex}",
                model_output_id=model_output_id,
                trace_id=segment.trace_id,
                prompt_packet_id=_str_or_none(segment.metadata.get("prompt_packet_id")),
                status="captured" if execution_enabled else "blocked",
                intent_type=intent_type,  # type: ignore[arg-type]
                tool_name=_str_or_none(payload.get("tool_name")),
                action_type=_str_or_none(payload.get("action_type")),
                target_type=_str_or_none(payload.get("target_type")),
                target_id=_str_or_none(payload.get("target_id")),
                arguments_redacted=arguments,
                raw_arguments_hash=hash_model_output(
                    json.dumps(payload.get("arguments", {}), sort_keys=True)
                ),
                risk_level=_risk_for_intent(intent_type),  # type: ignore[arg-type]
                policy_decision_id=None,
                autonomy_decision_id=None,
                approval_request_id=None,
                blocked_reason="tool_intent_execution_disabled"
                if not execution_enabled
                else "captured_for_review",
                metadata={
                    "redaction_findings": findings,
                    "source_segment_id": segment.output_segment_id,
                },
                created_at=datetime.now(UTC),
            )
            intents.append(intent)
        save = getattr(self._repository, "save_tool_intents", None)
        stored = save(intents) if callable(save) else intents
        result = [item for item in stored if isinstance(item, ToolIntentCandidate)]
        for intent in result:
            emit_telemetry(
                self._telemetry_service,
                event_type="tool_intent_captured",
                node_type="tool_intent",
                node_id=intent.tool_intent_id,
                intensity=0.8,
                trace_id=intent.trace_id,
                payload={"status": intent.status, "intent_type": intent.intent_type},
            )
            if intent.status == "blocked":
                emit_telemetry(
                    self._telemetry_service,
                    event_type="tool_intent_blocked",
                    node_type="tool_intent",
                    node_id=intent.tool_intent_id,
                    intensity=1.0,
                    trace_id=intent.trace_id,
                    payload={"blocked_reason": intent.blocked_reason},
                )
        return result

    def list_tool_intents(
        self,
        scope: list[str],
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[ToolIntentCandidate]:
        """List captured tool intents."""

        authorize(
            self._policy_adapter,
            action_type="model_output.tool_intent.read",
            resource_type="tool_intent",
            resource_id=trace_id,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_intents = getattr(self._repository, "list_tool_intents", None)
        if not callable(list_intents):
            return []
        result = list_intents(status=status, trace_id=trace_id, limit=limit)
        return [item for item in result if isinstance(item, ToolIntentCandidate)]

    def reject_tool_intent(
        self,
        tool_intent_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ToolIntentCandidate:
        """Reject a captured tool intent without executing it."""

        authorize(
            self._policy_adapter,
            action_type="model_output.tool_intent.update",
            resource_type="tool_intent",
            resource_id=tool_intent_id,
            scope=["workspace:main"],
            trace_id=self._actor_context.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        get_intent = getattr(self._repository, "get_tool_intent", None)
        intent = get_intent(tool_intent_id) if callable(get_intent) else None
        if not isinstance(intent, ToolIntentCandidate):
            raise ValueError("tool_intent_not_found")
        rejected = intent.model_copy(
            update={
                "status": "rejected",
                "blocked_reason": reason,
                "resolved_at": datetime.now(UTC),
            }
        )
        update = getattr(self._repository, "update_tool_intent", None)
        stored = update(rejected) if callable(update) else rejected
        return stored if isinstance(stored, ToolIntentCandidate) else rejected


def _parse_tool_payload(content: str) -> dict[str, Any]:
    first, _, rest = content.partition(":")
    name = rest.strip().split()[0] if rest.strip() else first.strip()
    arguments: dict[str, Any] = {}
    match = re.search(r"\{.*\}", content)
    if match:
        try:
            loaded = json.loads(match.group(0))
            if isinstance(loaded, dict):
                arguments = loaded
        except json.JSONDecodeError:
            arguments = {"raw": "[unparsed]"}
    return {
        "tool_name": name.strip() or None,
        "action_type": first.strip().lower() or None,
        "arguments": arguments,
    }


def _intent_type(content: str) -> str:
    lowered = content.lower()
    if lowered.startswith("mcp:"):
        return "mcp_tool"
    if lowered.startswith("capability:"):
        return "capability_invoke"
    if lowered.startswith("command:"):
        return "command_dispatch"
    if lowered.startswith("action:"):
        return "external_request"
    if lowered.startswith("tool:") or lowered.startswith("function_call:"):
        return "tool_call"
    return "unknown"


def _risk_for_intent(intent_type: str) -> str:
    if intent_type in {"external_request", "mcp_tool", "unknown"}:
        return "high"
    if intent_type in {"capability_invoke", "memory_write", "command_dispatch", "workflow_run"}:
        return "medium"
    return "low"


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


__all__ = ["ToolIntentCaptureService"]
