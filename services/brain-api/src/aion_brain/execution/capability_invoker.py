"""Capability invocation boundary for execution."""

from datetime import UTC, datetime
from typing import Any

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.contracts.execution import CapabilityInvocationRecord, CapabilityInvocationStatus
from aion_brain.contracts.modules import (
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    InvocationMode,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway
from aion_brain.policy.base import PolicyAdapter


class CapabilityInvoker:
    """Policy-gated, side-effect-free capability invocation boundary."""

    def __init__(
        self,
        *,
        capability_registry: CapabilityRegistry | object | None = None,
        policy_adapter: PolicyAdapter,
        execution_repository: object | None = None,
        telemetry_service: object | None = None,
        runtime_gateway: CapabilityRuntimeGateway | None = None,
    ) -> None:
        self._capability_registry = capability_registry or CapabilityRegistry()
        self._policy_adapter = policy_adapter
        self._execution_repository = execution_repository
        self._telemetry_service = telemetry_service
        self._runtime_gateway = runtime_gateway

    def invoke(
        self,
        capability_id: str,
        payload: dict[str, Any],
        execution_id: str | None,
        step_run_id: str | None,
        trace_id: str | None,
    ) -> CapabilityInvocationRecord:
        """Create a capability invocation record without external side effects."""
        if self._runtime_gateway is not None:
            invocation_id = f"invocation-{execution_id or 'adhoc'}-{step_run_id or capability_id}"
            result = self._runtime_gateway.invoke(
                CapabilityInvocationRequest(
                    invocation_id=invocation_id,
                    trace_id=trace_id,
                    execution_id=execution_id,
                    step_run_id=step_run_id,
                    capability_id=capability_id,
                    actor_id=_str_or_none(payload.get("actor_id")),
                    workspace_id=_str_or_none(payload.get("workspace_id")),
                    mode=_mode(payload),
                    payload=payload,
                    approval_present=bool(payload.get("approval_present", False)),
                    metadata={"risk_level": payload.get("risk_level", "medium")},
                )
            )
            return self._persist_and_emit(_record_from_result(result, payload))

        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"capability.invoke-{capability_id}-{execution_id or 'adhoc'}",
                trace_id=trace_id,
                actor_id=None,
                workspace_id=None,
                action_type="capability.invoke",
                resource_type="capability",
                resource_id=capability_id,
                risk_level="medium",
                approval_present=False,
                requested_permissions=[],
                security_scope=_scope(payload),
                context={"capability_id": capability_id, "execution_id": execution_id},
            )
        )
        if not decision.allow:
            record = _record(
                capability_id=capability_id,
                payload=payload,
                execution_id=execution_id,
                step_run_id=step_run_id,
                trace_id=trace_id,
                status="blocked_by_policy",
                output={"invoked": False, "reason": decision.reason},
                policy_decision_id=decision.decision_id,
            )
            return self._persist_and_emit(record)

        if not _capability_exists(self._capability_registry, capability_id):
            record = _record(
                capability_id=capability_id,
                payload=payload,
                execution_id=execution_id,
                step_run_id=step_run_id,
                trace_id=trace_id,
                status="failed",
                output={"invoked": False, "reason": "capability_not_found"},
                policy_decision_id=decision.decision_id,
            )
            return self._persist_and_emit(record)

        record = _record(
            capability_id=capability_id,
            payload=payload,
            execution_id=execution_id,
            step_run_id=step_run_id,
            trace_id=trace_id,
            status="not_implemented",
            output={
                "invoked": False,
                "reason": (
                    "Capability invocation is reserved for future module runtime integration."
                ),
            },
            policy_decision_id=decision.decision_id,
        )
        return self._persist_and_emit(record)

    def _persist_and_emit(self, record: CapabilityInvocationRecord) -> CapabilityInvocationRecord:
        save = getattr(self._execution_repository, "save_capability_invocation", None)
        if callable(save):
            try:
                save(record)
            except Exception:
                pass
        self._emit(record)
        return record

    def _emit(self, record: CapabilityInvocationRecord) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{record.invocation_id}-capability-invocation-recorded",
            trace_id=record.trace_id or record.invocation_id,
            event_type="capability_invocation_recorded",
            node_type="capability",
            node_id=record.capability_id,
            edge_from=record.step_run_id,
            edge_to=record.invocation_id,
            intensity=0.6,
            payload={"status": record.status},
            created_at=datetime.now(UTC),
        )
        try:
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(record.trace_id or record.invocation_id, [event])
                return
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return


def _record(
    *,
    capability_id: str,
    payload: dict[str, Any],
    execution_id: str | None,
    step_run_id: str | None,
    trace_id: str | None,
    status: CapabilityInvocationStatus,
    output: dict[str, Any],
    policy_decision_id: str | None,
) -> CapabilityInvocationRecord:
    return CapabilityInvocationRecord(
        invocation_id=f"invocation-{execution_id or 'adhoc'}-{step_run_id or capability_id}",
        execution_id=execution_id,
        step_run_id=step_run_id,
        trace_id=trace_id,
        capability_id=capability_id,
        input=payload,
        output=output,
        status=status,
        policy_decision_id=policy_decision_id,
        latency_ms=0,
        created_at=datetime.now(UTC),
    )


def _record_from_result(
    result: CapabilityInvocationResult,
    payload: dict[str, Any],
) -> CapabilityInvocationRecord:
    status = _record_status(result.status)
    output = {
        **result.output,
        "runtime_id": result.runtime_id,
        "gateway_status": result.status,
    }
    if result.error:
        output.setdefault("reason", result.error.get("reason", result.status))
    return CapabilityInvocationRecord(
        invocation_id=result.invocation_id,
        execution_id=_str_or_none(payload.get("execution_id")),
        step_run_id=_str_or_none(payload.get("step_run_id")),
        trace_id=_str_or_none(payload.get("trace_id")),
        capability_id=result.capability_id,
        input=payload,
        output=output,
        status=status,
        policy_decision_id=result.policy_decision_id,
        latency_ms=result.latency_ms,
        created_at=result.created_at,
    )


def _record_status(status: str) -> CapabilityInvocationStatus:
    if status in {"completed", "dry_run"}:
        return "completed"
    if status == "blocked_by_policy":
        return "blocked_by_policy"
    if status in {"not_implemented", "runtime_not_found"}:
        return "not_implemented"
    return "failed"


def _mode(payload: dict[str, Any]) -> InvocationMode:
    value = payload.get("mode")
    if value == "dry_run":
        return "dry_run"
    return "controlled"


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _capability_exists(registry: object, capability_id: str) -> bool:
    list_manifests = getattr(registry, "list_manifests", None)
    if not callable(list_manifests):
        return False
    for manifest in list_manifests():
        for capability in getattr(manifest, "capabilities", []):
            if isinstance(capability, dict) and capability_id in {
                capability.get("capability_id"),
                capability.get("id"),
            }:
                return True
    return False


def _scope(payload: dict[str, Any]) -> list[str]:
    value = payload.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return ["workspace:main"]
