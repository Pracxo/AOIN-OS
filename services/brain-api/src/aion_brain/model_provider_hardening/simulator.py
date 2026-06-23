"""Deterministic dry-run model provider simulator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.model_provider_hardening import (
    ModelProviderBlocker,
    ModelProviderSimulation,
    ModelProviderSimulationRequest,
)
from aion_brain.model_provider_hardening.hash import hash_provider_payload
from aion_brain.model_provider_hardening.policy import authorize_model_provider_action
from aion_brain.model_provider_hardening.redaction import (
    detect_provider_safety_issues,
    payload_has_tool_intent,
    redact_provider_payload,
)
from aion_brain.model_provider_hardening.repository import ModelProviderHardeningRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ModelProviderSimulator:
    """Simulate provider response shape without credentials, network, or model calls."""

    def __init__(
        self,
        repository: ModelProviderHardeningRepository,
        policy_adapter: object,
        *,
        output_governance_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        notification_router: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._output_governance_service = output_governance_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._notification_router = notification_router
        self._settings = settings or get_settings()

    def set_output_governance_service(self, service: object | None) -> None:
        """Attach model output governance after kernel assembly."""

        self._output_governance_service = service

    def simulate(self, request: ModelProviderSimulationRequest) -> ModelProviderSimulation:
        """Persist a deterministic synthetic provider simulation."""

        self._guard_settings()
        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.simulate",
            request.owner_scope,
            actor_id=request.actor_id or request.created_by,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="model_provider_simulation",
            risk_level="medium",
            context={"provider_key": request.provider_key, "dry_run": True},
        )
        redacted_request, blocked_fields = redact_provider_payload(request.simulated_request)
        issues = detect_provider_safety_issues(request.simulated_request)
        tool_intent_status = (
            "blocked" if payload_has_tool_intent(request.simulated_request) else "none"
        )
        grounding_status = (
            "synthetic"
            if _has_grounding_marker(request.expected_response_shape)
            else "required"
        )
        blockers = [_blocker_payload(issue) for issue in issues]
        if grounding_status == "required":
            blockers.append(
                {
                    "blocker_type": "grounding_required",
                    "severity": "medium",
                    "reason": "Grounding must be present before real provider enablement.",
                    "recommended_action": "add evidence references or grounding metadata",
                }
            )
        synthetic_response = _synthetic_response(
            request.provider_key,
            request.expected_response_shape,
            tool_intent_status=tool_intent_status,
            grounding_status=grounding_status,
        )
        status = "blocked" if _has_high_blocker(blockers) else "warning" if blockers else "passed"
        now = datetime.now(UTC)
        simulation = ModelProviderSimulation(
            provider_simulation_id=(
                request.provider_simulation_id or f"model-provider-simulation-{uuid4().hex}"
            ),
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            provider_profile_id=request.provider_profile_id,
            provider_key=request.provider_key,
            status=cast(Any, status),
            simulation_type=request.simulation_type,
            owner_scope=request.owner_scope,
            input_manifest_ref=request.input_manifest_ref,
            egress_preview_id=request.egress_preview_id,
            simulated_request_hash=hash_provider_payload(request.simulated_request),
            simulated_response_hash=hash_provider_payload(synthetic_response),
            redacted_simulated_request=redacted_request,
            redacted_simulated_response=synthetic_response,
            output_governance_status="passed",
            tool_intent_status=tool_intent_status,
            grounding_status=grounding_status,
            external_calls_made=False,
            credentials_used=False,
            model_invoked=False,
            score=0.5 if blockers else 1.0,
            blockers=blockers,
            warnings=[
                {
                    "code": "dry_run_only",
                    "message": "Provider simulation did not invoke a model.",
                }
            ],
            metadata={
                **request.metadata,
                "blocked_fields": blocked_fields,
                "external_calls_made": False,
                "credentials_used": False,
                "model_invoked": False,
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        saved = self._repository.save_simulation(simulation)
        for blocker in blockers:
            self._repository.save_blocker(
                ModelProviderBlocker(
                    provider_blocker_id=f"model-provider-blocker-{uuid4().hex}",
                    trace_id=request.trace_id,
                    provider_profile_id=request.provider_profile_id,
                    provider_key=request.provider_key,
                    source_type="model_provider_simulation",
                    source_id=saved.provider_simulation_id,
                    blocker_type=cast(Any, blocker["blocker_type"]),
                    severity=cast(Any, blocker["severity"]),
                    status="open",
                    reason=str(blocker["reason"]),
                    recommended_action=str(blocker["recommended_action"]),
                    metadata={"model_invoked": False},
                    created_at=now,
                )
            )
        self._emit(saved)
        self._record_audit(saved)
        self._record_provenance(saved)
        self._maybe_notify(saved, request.create_notifications)
        return saved

    def _guard_settings(self) -> None:
        if not self._settings.model_provider_hardening_enabled:
            raise RuntimeError("model_provider_hardening_disabled")
        if not self._settings.model_provider_simulation_enabled:
            raise RuntimeError("model_provider_simulation_disabled")
        if self._settings.external_model_calls_enabled:
            raise RuntimeError("external_model_calls_must_remain_disabled")
        if self._settings.model_provider_credentials_enabled:
            raise RuntimeError("model_provider_credentials_must_remain_disabled")

    def _emit(self, simulation: ModelProviderSimulation) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type="model_provider_simulation_completed",
            node_type="model_provider_simulation",
            node_id=simulation.provider_simulation_id,
            scope=simulation.owner_scope,
            intensity=simulation.score,
            payload={"status": simulation.status, "model_invoked": False},
        )

    def _record_audit(self, simulation: ModelProviderSimulation) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="model_provider.simulate",
            resource_type="model_provider_simulation",
            resource_id=simulation.provider_simulation_id,
            event_type="model_provider_simulation_completed",
            outcome=_audit_outcome(simulation.status),
            source_component="model_provider_hardening",
            trace_id=simulation.trace_id,
            actor_id=simulation.actor_id,
            workspace_id=simulation.workspace_id,
            risk_level="medium",
            payload={"external_calls_made": False, "model_invoked": False},
        )

    def _record_provenance(self, simulation: ModelProviderSimulation) -> None:
        record = getattr(self._provenance_service, "record", None)
        if callable(record):
            record(
                "model_provider_simulation",
                simulation.provider_simulation_id,
                simulation.owner_scope,
                metadata={"synthetic": True, "model_invoked": False},
            )

    def _maybe_notify(self, simulation: ModelProviderSimulation, requested: bool) -> None:
        if not requested and not self._settings.model_provider_create_notifications_default:
            return
        publish = getattr(self._notification_router, "publish", None)
        if callable(publish):
            publish(
                {
                    "topic": "model_provider_hardening",
                    "title": "Model provider simulation completed",
                    "source_id": simulation.provider_simulation_id,
                    "metadata": {"model_invoked": False},
                }
            )


def _synthetic_response(
    provider_key: str,
    expected_shape: dict[str, Any],
    *,
    tool_intent_status: str,
    grounding_status: str,
) -> dict[str, Any]:
    return {
        "synthetic": True,
        "provider_key": provider_key,
        "generated_by": "aion.model_provider_simulator",
        "external_calls_made": False,
        "model_invoked": False,
        "credentials_used": False,
        "tool_intent_status": tool_intent_status,
        "grounding_status": grounding_status,
        "shape": expected_shape or {"type": "object"},
    }


def _has_grounding_marker(payload: dict[str, Any]) -> bool:
    keys = {str(key).lower() for key in payload}
    return bool(keys & {"evidence_refs", "citations", "grounded", "grounding"})


def _blocker_payload(issue: dict[str, str]) -> dict[str, str]:
    blocker_type = issue.get("type", "generic")
    return {
        "blocker_type": blocker_type,
        "severity": "high" if blocker_type == "tool_intent_guard_missing" else "medium",
        "reason": _safe_reason(blocker_type),
        "recommended_action": "remove unsafe provider simulation metadata and retry",
        "field": issue.get("field", ""),
    }


def _safe_reason(blocker_type: str) -> str:
    if blocker_type == "raw_prompt_detected":
        return "Unsafe prompt body metadata is not allowed in simulations."
    if blocker_type == "hidden_reasoning_detected":
        return "Internal reasoning metadata is not allowed in simulations."
    if blocker_type == "tool_intent_guard_missing":
        return "Tool intent must be blocked before provider simulation."
    if blocker_type == "credential_storage_forbidden":
        return "Secret-like provider metadata is not allowed."
    return "Provider simulation found unsafe metadata."


def _has_high_blocker(blockers: list[dict[str, str]]) -> bool:
    return any(item.get("severity") in {"high", "critical"} for item in blockers)


def _audit_outcome(status: str) -> str:
    if status == "blocked":
        return "blocked"
    if status == "failed":
        return "failed"
    return "completed"


__all__ = ["ModelProviderSimulator"]
