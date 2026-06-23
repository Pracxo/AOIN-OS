"""Prompt egress guard for model provider hardening."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.model_provider_hardening import (
    ModelProviderBlocker,
    PromptEgressPreview,
    PromptEgressPreviewRequest,
)
from aion_brain.model_provider_hardening.policy import authorize_model_provider_action
from aion_brain.model_provider_hardening.redaction import (
    detect_provider_safety_issues,
    redact_provider_payload,
)
from aion_brain.model_provider_hardening.repository import ModelProviderHardeningRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class PromptEgressGuard:
    """Create redacted prompt egress previews without transmitting prompts."""

    def __init__(
        self,
        repository: ModelProviderHardeningRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        notification_router: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._notification_router = notification_router
        self._settings = settings or get_settings()

    def preview(self, request: PromptEgressPreviewRequest) -> PromptEgressPreview:
        """Persist a redacted prompt egress preview."""

        if not self._settings.prompt_egress_guard_enabled:
            raise RuntimeError("prompt_egress_guard_disabled")
        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.egress.preview",
            request.owner_scope,
            actor_id=request.actor_id or request.created_by,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="prompt_egress_preview",
            risk_level="medium",
            context={"provider_key": request.provider_key, "preview_type": request.preview_type},
        )
        redacted, blocked_fields = redact_provider_payload(request.prompt_summary)
        issues = detect_provider_safety_issues(request.prompt_summary)
        blockers = [_blocker_payload(issue) for issue in issues]
        warnings = [
            {
                "code": "external_model_calls_disabled",
                "severity": "medium",
                "message": "Prompt egress preview is local-only; no prompt is transmitted.",
            }
        ]
        if self._settings.external_model_calls_enabled:
            blockers.append(
                {
                    "blocker_type": "external_calls_disabled",
                    "severity": "critical",
                    "reason": "External model calls must remain disabled in AION-086.",
                    "recommended_action": "set AION_EXTERNAL_MODEL_CALLS_ENABLED=false",
                }
            )
        status = "blocked" if blockers else "warning"
        preview = PromptEgressPreview(
            prompt_egress_preview_id=(
                request.prompt_egress_preview_id or f"prompt-egress-preview-{uuid4().hex}"
            ),
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            provider_profile_id=request.provider_profile_id,
            provider_key=request.provider_key,
            status=cast(Any, status),
            preview_type=request.preview_type,
            owner_scope=request.owner_scope,
            prompt_packet_ref=request.prompt_packet_ref,
            input_manifest_ref=request.input_manifest_ref,
            redacted_prompt_summary=redacted,
            blocked_fields=blocked_fields,
            egress_allowed=False,
            external_call_allowed=False,
            blockers=blockers,
            warnings=warnings,
            metadata={
                **request.metadata,
                "raw_prompt_stored": False,
                "prompt_transmitted": False,
                "external_calls_allowed": False,
            },
            created_by=request.created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_egress_preview(preview)
        for blocker in blockers:
            self._repository.save_blocker(
                ModelProviderBlocker(
                    provider_blocker_id=f"model-provider-blocker-{uuid4().hex}",
                    trace_id=request.trace_id,
                    provider_profile_id=request.provider_profile_id,
                    provider_key=request.provider_key,
                    source_type="prompt_egress_preview",
                    source_id=saved.prompt_egress_preview_id,
                    blocker_type=cast(Any, blocker["blocker_type"]),
                    severity=cast(Any, blocker["severity"]),
                    status="open",
                    reason=str(blocker["reason"]),
                    recommended_action=str(blocker["recommended_action"]),
                    metadata={"prompt_transmitted": False},
                    created_at=datetime.now(UTC),
                )
            )
        self._emit(saved)
        self._record_audit(saved)
        self._maybe_notify(saved, request.create_notifications)
        return saved

    def _emit(self, preview: PromptEgressPreview) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type="prompt_egress_preview_created",
            node_type="prompt_egress_preview",
            node_id=preview.prompt_egress_preview_id,
            scope=preview.owner_scope,
            intensity=0.7 if preview.status == "blocked" else 0.45,
            payload={"status": preview.status, "external_call_allowed": False},
        )

    def _record_audit(self, preview: PromptEgressPreview) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="model_provider.egress.preview",
            resource_type="prompt_egress_preview",
            resource_id=preview.prompt_egress_preview_id,
            event_type="prompt_egress_preview_created",
            outcome=_audit_outcome(preview.status),
            source_component="model_provider_hardening",
            trace_id=preview.trace_id,
            actor_id=preview.actor_id,
            workspace_id=preview.workspace_id,
            risk_level="medium",
            payload={"prompt_transmitted": False, "external_call_allowed": False},
        )

    def _maybe_notify(self, preview: PromptEgressPreview, requested: bool) -> None:
        if not requested and not self._settings.model_provider_create_notifications_default:
            return
        publish = getattr(self._notification_router, "publish", None)
        if callable(publish):
            publish(
                {
                    "topic": "model_provider_hardening",
                    "title": "Prompt egress preview created",
                    "source_id": preview.prompt_egress_preview_id,
                    "metadata": {"external_call_allowed": False},
                }
            )


def _blocker_payload(issue: dict[str, str]) -> dict[str, str]:
    blocker_type = issue.get("type", "generic")
    severity = (
        "critical"
        if blocker_type in {"raw_prompt_detected", "hidden_reasoning_detected"}
        else "high"
    )
    return {
        "blocker_type": blocker_type,
        "severity": severity,
        "reason": _safe_reason(blocker_type),
        "recommended_action": "remove unsafe prompt egress metadata and retry the preview",
        "field": issue.get("field", ""),
    }


def _safe_reason(blocker_type: str) -> str:
    if blocker_type == "raw_prompt_detected":
        return "Unsafe prompt body metadata is not allowed in egress previews."
    if blocker_type == "hidden_reasoning_detected":
        return "Internal reasoning metadata is not allowed in egress previews."
    if blocker_type == "tool_intent_guard_missing":
        return "Tool intent must be blocked before provider egress."
    if blocker_type == "credential_storage_forbidden":
        return "Secret-like provider metadata is not allowed."
    return "Provider egress guard blocked unsafe metadata."


def _audit_outcome(status: str) -> str:
    if status == "blocked":
        return "blocked"
    if status == "failed":
        return "failed"
    return "completed"


__all__ = ["PromptEgressGuard"]
