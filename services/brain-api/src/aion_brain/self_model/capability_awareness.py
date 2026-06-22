"""Deterministic capability awareness service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.capability_awareness import CapabilityAwarenessRecord
from aion_brain.outcomes._shared import authorize, emit_telemetry
from aion_brain.self_model.repository import SelfModelRepository


class CapabilityAwarenessService:
    """Build a factual local capability inventory without external calls."""

    def __init__(
        self,
        repository: SelfModelRepository,
        policy_adapter: object,
        *,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._settings = settings
        self._telemetry_service = telemetry_service

    def refresh(self, scope: list[str], dry_run: bool = True) -> list[CapabilityAwarenessRecord]:
        authorize(
            self._policy_adapter,
            action_type="self_model.capability_awareness.refresh",
            resource_type="capability_awareness",
            resource_id=None,
            scope=scope,
            risk_level="low",
            context={"dry_run": dry_run},
        )
        records = [_record(scope, **item) for item in _capability_specs(self._settings)]
        if not dry_run:
            for record in records:
                self._repository.save_capability_awareness(record)
        emit_telemetry(
            self._telemetry_service,
            event_type="capability_awareness_refreshed",
            node_type="capability_awareness",
            node_id="capability_inventory",
            intensity=0.6,
            trace_id=None,
            payload={"owner_scope": scope, "capability_count": len(records), "dry_run": dry_run},
        )
        return records

    def list_capabilities(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        capability_type: str | None = None,
    ) -> list[CapabilityAwarenessRecord]:
        authorize(
            self._policy_adapter,
            action_type="self_model.capability_awareness.read",
            resource_type="capability_awareness",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        records = self._repository.list_capability_awareness(
            status=status,
            capability_type=capability_type,
        )
        if not records:
            records = self.refresh(scope, dry_run=True)
        return [
            record
            for record in records
            if (status is None or record.status == status)
            and (capability_type is None or record.capability_type == capability_type)
        ]

    def get_capability(
        self,
        capability_key: str,
        scope: list[str],
    ) -> CapabilityAwarenessRecord | None:
        records = self.list_capabilities(scope)
        return next((record for record in records if record.capability_key == capability_key), None)

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        records = self.refresh(scope or ["workspace:main"], dry_run=True)
        return {
            "status": "warning"
            if any(record.availability == "optional_unavailable" for record in records)
            else "healthy",
            "capability_count": len(records),
            "active_capability_count": sum(1 for record in records if record.status == "active"),
            "unavailable_capability_count": sum(
                1 for record in records if "unavailable" in record.availability
            ),
        }


def _record(scope: list[str], **values: Any) -> CapabilityAwarenessRecord:
    return CapabilityAwarenessRecord(
        awareness_id=f"awareness-{values['capability_key'].replace('.', '-')}-{uuid4().hex}",
        capability_key=values["capability_key"],
        capability_type=cast(Any, values["capability_type"]),
        status=cast(Any, values["status"]),
        availability=cast(Any, values["availability"]),
        mode=cast(Any, values["mode"]),
        risk_level=cast(Any, values["risk_level"]),
        requires_policy=bool(values.get("requires_policy", True)),
        requires_approval=bool(values.get("requires_approval", False)),
        requires_autonomy=bool(values.get("requires_autonomy", False)),
        dry_run_only=bool(values.get("dry_run_only", False)),
        source_refs=list(values.get("source_refs", [])),
        limitations=list(values.get("limitations", [])),
        metadata={**dict(values.get("metadata", {})), "owner_scope": scope},
        checked_at=datetime.now(UTC),
    )


def _capability_specs(settings: object | None) -> list[dict[str, Any]]:
    model_gateway_enabled = bool(getattr(settings, "model_gateway_enabled", False))
    sandbox_enabled = bool(getattr(settings, "sandbox_execution_enabled", False))
    workflow_controlled = bool(getattr(settings, "workflow_controlled_execution_enabled", False))
    turbovec_enabled = bool(getattr(settings, "turbovec_enabled", False))
    graphiti_enabled = bool(getattr(settings, "graphiti_enabled", False))
    restore_apply_enabled = bool(getattr(settings, "backup_restore_apply_enabled", False))
    return [
        _available("aion.kernel", "kernel", "assist", "low"),
        _available("aion.memory", "memory", "assist", "low"),
        _available("aion.evidence", "evidence", "assist", "low"),
        _available("aion.retrieval", "retrieval", "assist", "low"),
        _available("aion.reasoning", "reasoning", "plan_only", "medium"),
        _available("aion.planning", "planning", "plan_only", "medium"),
        _available("aion.policy", "policy", "observe", "low"),
        _available("aion.autonomy", "autonomy", "observe", "medium"),
        _available("aion.dialogue", "dialogue", "assist", "low"),
        _available("aion.response", "response", "assist", "low"),
        _available("aion.belief", "belief", "assist", "low"),
        _available("aion.entity", "entity", "assist", "low"),
        _available("aion.situation", "situation", "assist", "low"),
        _available("aion.decision", "decision", "plan_only", "medium"),
        _available("aion.outcome", "outcome", "observe", "low"),
        _available("aion.learning", "learning", "dry_run", "medium", dry_run_only=True),
        _available("aion.operator", "operator", "observe", "low"),
        _available("aion.audit", "audit", "observe", "low"),
        _available("aion.visual", "visual", "observe", "low"),
        _available("aion.runtime_config", "runtime_config", "observe", "medium"),
        _available("aion.security", "security", "observe", "high"),
        _available("aion.resilience", "resilience", "observe", "medium"),
        _available("aion.performance", "performance", "observe", "low"),
        _available("aion.release", "release", "dry_run", "medium", dry_run_only=True),
        _available("aion.sdk", "sdk", "metadata_only", "low"),
        _available("aion.cli", "cli", "metadata_only", "low"),
        _conditional(
            "aion.workflow.execution",
            "workflow",
            workflow_controlled,
            "controlled",
            dry_run_only=not workflow_controlled,
            limitation="no_external_delivery_v0_1",
        ),
        _conditional(
            "aion.sandbox.execution",
            "sandbox",
            sandbox_enabled,
            "dry_run",
            dry_run_only=True,
            limitation="sandbox_execution_disabled_default",
            risk_level="high",
        ),
        _conditional(
            "aion.backup.restore.apply",
            "backup",
            restore_apply_enabled,
            "dry_run",
            dry_run_only=True,
            limitation="restore_apply_disabled_default",
            risk_level="high",
        ),
        _optional_adapter("aion.optional.turbovec", "TurboVec", turbovec_enabled),
        _optional_adapter("aion.optional.graphiti", "Graphiti", graphiti_enabled),
        _optional_adapter("aion.optional.langfuse", "Langfuse", False),
        {
            **_available("aion.model_gateway.external_calls", "reasoning", "plan_only", "high"),
            "status": "active" if model_gateway_enabled else "disabled",
            "availability": "available" if model_gateway_enabled else "disabled_by_config",
            "limitations": []
            if model_gateway_enabled
            else ["external_model_calls_disabled_default"],
            "metadata": {"external_calls_enabled": model_gateway_enabled},
        },
    ]


def _available(
    capability_key: str,
    capability_type: str,
    mode: str,
    risk_level: str,
    *,
    dry_run_only: bool = False,
) -> dict[str, Any]:
    return {
        "capability_key": capability_key,
        "capability_type": capability_type,
        "status": "dry_run_only" if dry_run_only else "active",
        "availability": "available",
        "mode": mode,
        "risk_level": risk_level,
        "dry_run_only": dry_run_only,
        "source_refs": ["kernel.container", "runtime_config"],
    }


def _conditional(
    capability_key: str,
    capability_type: str,
    enabled: bool,
    mode: str,
    *,
    dry_run_only: bool,
    limitation: str,
    risk_level: str = "medium",
) -> dict[str, Any]:
    return {
        "capability_key": capability_key,
        "capability_type": capability_type,
        "status": "dry_run_only" if dry_run_only else ("active" if enabled else "disabled"),
        "availability": "available" if enabled else "disabled_by_config",
        "mode": mode,
        "risk_level": risk_level,
        "requires_autonomy": True,
        "dry_run_only": dry_run_only,
        "limitations": [limitation] if not enabled or dry_run_only else [],
        "source_refs": ["runtime_config"],
    }


def _optional_adapter(capability_key: str, label: str, enabled: bool) -> dict[str, Any]:
    return {
        "capability_key": capability_key,
        "capability_type": "optional_adapter",
        "status": "active" if enabled else "unavailable",
        "availability": "available" if enabled else "optional_unavailable",
        "mode": "metadata_only",
        "risk_level": "medium",
        "dry_run_only": not enabled,
        "source_refs": ["adapter_status"],
        "limitations": [] if enabled else ["optional_adapters_disabled_default"],
        "metadata": {"adapter": label, "optional": True},
    }
