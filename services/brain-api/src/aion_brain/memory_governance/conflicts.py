"""Deterministic memory conflict detection and resolution."""

import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.attention import AttentionSignalCreateRequest
from aion_brain.contracts.memory import MemoryRecord
from aion_brain.contracts.memory_governance import (
    MemoryConflict,
    MemoryConflictResolutionRequest,
    MemoryConflictScanRequest,
    MemoryConflictSeverity,
    MemoryConflictType,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.policy.base import PolicyAdapter


class MemoryConflictService:
    """Find generic conflicts without treating recall as truth."""

    def __init__(
        self,
        *,
        memory_service: object,
        governance_repository: MemoryGovernanceRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        settings: Settings,
        attention_controller: object | None = None,
    ) -> None:
        self._memory_service = memory_service
        self._repository = governance_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._attention_controller = attention_controller

    def scan(self, request: MemoryConflictScanRequest) -> list[MemoryConflict]:
        """Scan active memories for generic structural conflicts."""
        if not self._settings.memory_conflict_scan_enabled:
            return []
        allowed = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"memory.conflict.scan-{uuid4().hex}",
                trace_id=request.trace_id,
                actor_id=None,
                workspace_id=None,
                action_type="memory.conflict.scan",
                resource_type="memory",
                resource_id=None,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=request.owner_scope,
                context=request.model_dump(mode="json"),
            )
        )
        if not allowed.allow:
            return []
        records = _list_active(
            self._memory_service,
            request.owner_scope,
            request.limit,
            cast(list[Any], request.memory_types) or None,
        )
        requested_types = set(request.conflict_types)
        conflicts = [
            conflict
            for conflict in [
                *self._duplicates(request, records),
                *self._metadata_fact_conflicts(request, records),
                *self._stale_preferences(request, records),
                *self._competing_procedures(request, records),
                *self._scope_conflicts(request, records),
            ]
            if not requested_types or conflict.conflict_type in requested_types
        ]
        saved = [self._repository.save_conflict(conflict) for conflict in conflicts]
        for conflict in saved:
            self._emit("memory_conflict_detected", conflict, 0.75)
            self._create_attention_signal(conflict)
        return saved

    def list_conflicts(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[MemoryConflict]:
        """List persisted conflicts after policy authorization."""
        allowed = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"memory.conflict.read-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type="memory.conflict.read",
                resource_type="memory_conflict",
                resource_id=None,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=scope,
                context={"status": status, "limit": limit},
            )
        )
        if not allowed.allow:
            return []
        return self._repository.list_conflicts(scope, status=status, limit=limit)

    def resolve(self, request: MemoryConflictResolutionRequest) -> MemoryConflict:
        """Resolve or dismiss a generic memory conflict."""
        conflict = self._repository.get_conflict(request.conflict_id)
        if conflict is None:
            raise ValueError("memory_conflict_not_found")
        allowed = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"memory.conflict.resolve-{request.conflict_id}",
                trace_id=conflict.trace_id,
                actor_id=request.actor_id,
                workspace_id=None,
                action_type="memory.conflict.resolve",
                resource_type="memory_conflict",
                resource_id=request.conflict_id,
                risk_level=_resolution_risk(request.resolution),
                approval_present=True,
                requested_permissions=[],
                security_scope=conflict.owner_scope,
                context=request.model_dump(mode="json"),
            )
        )
        if not allowed.allow:
            raise ValueError(f"policy_denied:{allowed.reason}")
        now = datetime.now(UTC)
        status = "dismissed" if request.resolution == "dismiss" else "resolved"
        resolved = conflict.model_copy(
            update={
                "status": status,
                "resolution": request.resolution,
                "metadata": {**conflict.metadata, "resolution_reason": request.reason},
                "resolved_at": now,
            }
        )
        saved = self._repository.save_conflict(resolved)
        self._emit("memory_conflict_resolved", saved, 0.45)
        return saved

    def _duplicates(
        self,
        request: MemoryConflictScanRequest,
        records: list[MemoryRecord],
    ) -> list[MemoryConflict]:
        groups: dict[str, list[MemoryRecord]] = defaultdict(list)
        for record in records:
            groups[_normalized_summary(record.summary)].append(record)
        return [
            _conflict(
                request,
                "duplicate",
                group,
                "Multiple memories have the same normalized summary.",
                "low",
                {"normalized_summary": key},
            )
            for key, group in groups.items()
            if key and len(group) > 1
        ]

    def _metadata_fact_conflicts(
        self,
        request: MemoryConflictScanRequest,
        records: list[MemoryRecord],
    ) -> list[MemoryConflict]:
        grouped: dict[str, dict[str, list[MemoryRecord]]] = defaultdict(lambda: defaultdict(list))
        for record in records:
            key = _metadata_text(record.metadata, "fact_key", "attribute", "key")
            value = _metadata_text(record.metadata, "fact_value", "value")
            if key and value:
                grouped[key][value].append(record)
        conflicts: list[MemoryConflict] = []
        for key, by_value in grouped.items():
            if len(by_value) < 2:
                continue
            memories = [memory for group in by_value.values() for memory in group]
            conflicts.append(
                _conflict(
                    request,
                    "metadata_fact_conflict",
                    memories,
                    "Memories disagree on a shared generic metadata key.",
                    "medium",
                    {"metadata_key": key, "values": sorted(by_value)},
                )
            )
        return conflicts

    def _stale_preferences(
        self,
        request: MemoryConflictScanRequest,
        records: list[MemoryRecord],
    ) -> list[MemoryConflict]:
        grouped: dict[str, list[MemoryRecord]] = defaultdict(list)
        for record in records:
            key = _metadata_text(record.metadata, "preference_key", "rollup_key")
            if record.memory_type == "preference" and key:
                grouped[key].append(record)
        conflicts: list[MemoryConflict] = []
        for key, group in grouped.items():
            values = {
                _metadata_text(record.metadata, "preference_value", "value")
                for record in group
            }
            if len(group) > 1 and len(values - {""}) > 1:
                conflicts.append(
                    _conflict(
                        request,
                        "stale_preference",
                        group,
                        "Preference memories contain competing generic values.",
                        "medium",
                        {"metadata_key": key},
                    )
                )
        return conflicts

    def _competing_procedures(
        self,
        request: MemoryConflictScanRequest,
        records: list[MemoryRecord],
    ) -> list[MemoryConflict]:
        grouped: dict[str, list[MemoryRecord]] = defaultdict(list)
        for record in records:
            key = _metadata_text(record.metadata, "procedure_key", "rollup_key")
            if record.memory_type == "procedural" and key:
                grouped[key].append(record)
        return [
            _conflict(
                request,
                "competing_procedure",
                group,
                "Procedural memories define competing generic procedures.",
                "medium",
                {"metadata_key": key},
            )
            for key, group in grouped.items()
            if len({_normalized_summary(item.summary) for item in group}) > 1
        ]

    def _scope_conflicts(
        self,
        request: MemoryConflictScanRequest,
        records: list[MemoryRecord],
    ) -> list[MemoryConflict]:
        grouped: dict[str, list[MemoryRecord]] = defaultdict(list)
        for record in records:
            key = _metadata_text(record.metadata, "scope_key", "canonical_subject")
            if key:
                grouped[key].append(record)
        conflicts: list[MemoryConflict] = []
        for key, group in grouped.items():
            scopes = {json.dumps(sorted(record.owner_scope)) for record in group}
            if len(group) > 1 and len(scopes) > 1:
                conflicts.append(
                    _conflict(
                        request,
                        "scope_conflict",
                        group,
                        "Related memories have incompatible owner scopes.",
                        "high",
                        {"metadata_key": key},
                    )
                )
        return conflicts

    def _emit(self, event_type: str, conflict: MemoryConflict, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{conflict.conflict_id}-{event_type}",
            trace_id=conflict.trace_id or conflict.conflict_id,
            event_type=cast(Any, event_type),
            node_type="conflict",
            node_id=conflict.conflict_id,
            edge_from=None,
            edge_to=conflict.memory_ids[0],
            intensity=intensity,
            payload=conflict.model_dump(mode="json"),
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return

    def _create_attention_signal(self, conflict: MemoryConflict) -> None:
        if conflict.severity not in {"high", "critical"}:
            return
        create_signal = getattr(self._attention_controller, "create_signal", None)
        if not callable(create_signal):
            return
        try:
            create_signal(
                AttentionSignalCreateRequest(
                    attention_signal_id=None,
                    trace_id=conflict.trace_id,
                    actor_id=None,
                    workspace_id=None,
                    signal_type="memory_conflict",
                    source_type="memory",
                    source_id=conflict.conflict_id,
                    title="High priority memory conflict",
                    payload={
                        "conflict_id": conflict.conflict_id,
                        "conflict_type": conflict.conflict_type,
                        "severity": conflict.severity,
                    },
                    urgency=0.85 if conflict.severity == "critical" else 0.75,
                    importance=0.80,
                    confidence=0.8,
                    risk_level=conflict.severity,
                    owner_scope=conflict.owner_scope,
                    metadata={"detected_by": conflict.detected_by},
                )
            )
        except Exception:
            return


def _list_active(
    memory_service: object,
    scope: list[str],
    limit: int,
    memory_types: list[Any] | None,
) -> list[MemoryRecord]:
    list_active = getattr(memory_service, "list_active", None)
    if not callable(list_active):
        return []
    result = list_active(scope, limit=limit, memory_types=memory_types)
    if not isinstance(result, list):
        return []
    return [item for item in result if isinstance(item, MemoryRecord)]


def _conflict(
    request: MemoryConflictScanRequest,
    conflict_type: MemoryConflictType,
    records: list[MemoryRecord],
    description: str,
    severity: MemoryConflictSeverity,
    metadata: dict[str, Any],
) -> MemoryConflict:
    return MemoryConflict(
        conflict_id=f"memory-conflict-{uuid4().hex}",
        trace_id=request.trace_id,
        conflict_type=conflict_type,
        memory_ids=sorted({record.memory_id for record in records}),
        evidence_ids=sorted(_evidence_ids(records)),
        owner_scope=request.owner_scope,
        severity=_highest_sensitivity_severity(records, severity),
        status="open",
        description=description,
        detected_by="memory_governance_conflict_service",
        resolution=None,
        metadata=metadata,
        created_at=datetime.now(UTC),
        resolved_at=None,
    )


def _evidence_ids(records: list[MemoryRecord]) -> set[str]:
    evidence_ids: set[str] = set()
    for record in records:
        if record.content_ref:
            evidence_ids.add(record.content_ref)
        refs = record.metadata.get("evidence_refs")
        if isinstance(refs, list):
            evidence_ids.update(str(ref) for ref in refs)
    return evidence_ids


def _highest_sensitivity_severity(
    records: list[MemoryRecord],
    fallback: MemoryConflictSeverity,
) -> MemoryConflictSeverity:
    if any(record.sensitivity == "restricted" for record in records):
        return "high"
    if any(record.sensitivity == "confidential" for record in records):
        return "medium" if fallback == "low" else fallback
    return fallback


def _normalized_summary(summary: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", summary.lower()))


def _metadata_text(metadata: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _resolution_risk(resolution: str) -> str:
    if resolution in {"manual_review", "keep_evidence_grounded"}:
        return "medium"
    return "low"
