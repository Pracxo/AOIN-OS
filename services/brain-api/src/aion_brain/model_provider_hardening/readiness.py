"""Provider readiness gate for model provider hardening."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.model_provider_hardening import (
    ModelProviderBlocker,
    ModelProviderReadiness,
    ModelProviderReadinessRequest,
)
from aion_brain.model_provider_hardening.policy import authorize_model_provider_action
from aion_brain.model_provider_hardening.repository import ModelProviderHardeningRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ModelProviderReadinessService:
    """Assess dry-run provider readiness without enabling provider calls."""

    def __init__(
        self,
        repository: ModelProviderHardeningRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()

    def assess(self, request: ModelProviderReadinessRequest) -> ModelProviderReadiness:
        """Persist a provider readiness assessment."""

        if not self._settings.model_provider_readiness_enabled:
            raise RuntimeError("model_provider_readiness_disabled")
        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.readiness.assess",
            request.owner_scope,
            actor_id=request.actor_id or request.created_by,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="model_provider_readiness",
            risk_level="medium",
            context={"provider_key": request.provider_key},
        )
        blockers = self._setting_blockers(request)
        readiness_level = "blocked" if blockers else (
            "dry_run_ready" if request.simulation_refs else "metadata_only"
        )
        now = datetime.now(UTC)
        saved_blockers = [
            self._repository.save_blocker(
                ModelProviderBlocker(
                    provider_blocker_id=f"model-provider-blocker-{uuid4().hex}",
                    trace_id=request.trace_id,
                    provider_profile_id=request.provider_profile_id,
                    provider_key=request.provider_key,
                    source_type="model_provider_readiness",
                    source_id=request.provider_readiness_id,
                    blocker_type=cast(Any, item["blocker_type"]),
                    severity=cast(Any, item["severity"]),
                    status="open",
                    reason=item["reason"],
                    recommended_action=item["recommended_action"],
                    metadata={"readiness_does_not_enable_provider": True},
                    created_at=now,
                )
            )
            for item in blockers
        ]
        readiness = ModelProviderReadiness(
            provider_readiness_id=(
                request.provider_readiness_id or f"model-provider-readiness-{uuid4().hex}"
            ),
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            provider_profile_id=request.provider_profile_id,
            provider_key=request.provider_key,
            status=cast(Any, "blocked" if blockers else "ready_for_review"),
            readiness_level=cast(Any, readiness_level),
            owner_scope=request.owner_scope,
            external_call_ready=False,
            credentials_ready=False,
            egress_guard_ready=request.require_egress_guard,
            output_governance_ready=request.require_output_governance,
            tool_intent_guard_ready=request.require_tool_intent_guard,
            grounding_ready=request.require_grounding,
            policy_ready=True,
            audit_ready=True,
            blocker_refs=[item.provider_blocker_id for item in saved_blockers],
            warning_refs=[],
            simulation_refs=request.simulation_refs,
            recommendations=_recommendations(bool(blockers)),
            score=0.4 if blockers else 0.8 if request.simulation_refs else 0.6,
            metadata={
                **request.metadata,
                "provider_enabled": False,
                "readiness_is_not_enablement": True,
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        saved = self._repository.save_readiness(readiness)
        self._emit(saved)
        self._record_audit(saved)
        return saved

    def _setting_blockers(self, request: ModelProviderReadinessRequest) -> list[dict[str, str]]:
        blockers: list[dict[str, str]] = []
        if self._settings.external_model_calls_enabled:
            blockers.append(
                {
                    "blocker_type": "external_calls_disabled",
                    "severity": "critical",
                    "reason": "External model calls must remain disabled in AION-086.",
                    "recommended_action": "disable external model calls",
                }
            )
        if self._settings.model_provider_credentials_enabled:
            blockers.append(
                {
                    "blocker_type": "credential_storage_forbidden",
                    "severity": "critical",
                    "reason": "Provider credentials are not enabled in AION-086.",
                    "recommended_action": "keep model provider credentials disabled",
                }
            )
        if not request.require_grounding:
            blockers.append(
                {
                    "blocker_type": "grounding_required",
                    "severity": "medium",
                    "reason": "Grounding is required before provider enablement.",
                    "recommended_action": "require grounding in readiness requests",
                }
            )
        return blockers

    def _emit(self, readiness: ModelProviderReadiness) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type="model_provider_readiness_assessed",
            node_type="model_provider_readiness",
            node_id=readiness.provider_readiness_id,
            scope=readiness.owner_scope,
            intensity=readiness.score,
            payload={"status": readiness.status, "external_call_ready": False},
        )

    def _record_audit(self, readiness: ModelProviderReadiness) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="model_provider.readiness.assess",
            resource_type="model_provider_readiness",
            resource_id=readiness.provider_readiness_id,
            event_type="model_provider_readiness_assessed",
            outcome=_audit_outcome(readiness.status),
            source_component="model_provider_hardening",
            trace_id=readiness.trace_id,
            actor_id=readiness.actor_id,
            workspace_id=readiness.workspace_id,
            risk_level="medium",
            payload={
                "external_call_ready": False,
                "provider_enablement_state": "disabled",
            },
        )


def _recommendations(blocked: bool) -> list[str]:
    base = [
        "keep external model calls disabled",
        "keep provider credentials disabled",
        "continue prompt egress previews before any provider work",
    ]
    if blocked:
        return ["resolve provider hardening blockers", *base]
    return base


def _audit_outcome(status: str) -> str:
    if status == "blocked":
        return "blocked"
    if status == "failed":
        return "failed"
    return "completed"


__all__ = ["ModelProviderReadinessService"]
