"""Deterministic memory compaction service."""

import re
from collections import defaultdict
from datetime import UTC, datetime
from statistics import fmean
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.approvals import ApprovalCreateRequest
from aion_brain.contracts.memory import MemoryRecord
from aion_brain.contracts.memory_governance import (
    MemoryCompactedRecord,
    MemoryCompactionRequest,
    MemoryCompactionResult,
    MemoryCompactionRunRecord,
    MemoryCompactionStrategy,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.policy.base import PolicyAdapter


class MemoryCompactionService:
    """Compact low-level memories into deterministic higher-level records."""

    def __init__(
        self,
        *,
        memory_service: object,
        governance_repository: MemoryGovernanceRepository,
        policy_adapter: PolicyAdapter,
        approval_service: object | None,
        telemetry_service: object | None,
        settings: Settings,
    ) -> None:
        self._memory_service = memory_service
        self._repository = governance_repository
        self._policy_adapter = policy_adapter
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def compact(self, request: MemoryCompactionRequest) -> MemoryCompactionResult:
        """Run deterministic compaction with policy and optional approval."""
        run_id = request.compaction_run_id or f"memory-compaction-{uuid4().hex}"
        if not self._settings.memory_compaction_enabled:
            result = _result(
                run_id,
                request,
                status="failed",
                input_ids=[],
                output_ids=[],
                approval_required=False,
                approval_request_id=None,
                details={"reason": "memory_compaction_disabled"},
            )
            self._save_run(request, result)
            return result

        allowed = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"memory.compact-{run_id}",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="memory.compact",
                resource_type="memory",
                resource_id=None,
                risk_level="medium",
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=request.owner_scope,
                context=request.model_dump(mode="json"),
            )
        )
        if not allowed.allow:
            result = _result(
                run_id,
                request,
                status="blocked_by_policy",
                input_ids=[],
                output_ids=[],
                approval_required=False,
                approval_request_id=None,
                details={"reason": allowed.reason, "constraints": allowed.constraints},
            )
            self._save_run(request, result)
            return result

        if self._settings.memory_compaction_requires_approval and not request.approval_present:
            approval_id = self._create_approval(request, run_id)
            result = _result(
                run_id,
                request,
                status="pending_approval",
                input_ids=[],
                output_ids=[],
                approval_required=True,
                approval_request_id=approval_id,
                details={"reason": "approval_required"},
            )
            self._save_run(request, result)
            return result

        records = _load_memories(self._memory_service, request)
        input_ids = [record.memory_id for record in records]
        self._emit("memory_compaction_started", run_id, 0.55, {"input_memory_ids": input_ids})
        groups = _groups_for_strategy(records, request.strategy)
        outputs = [
            _output_memory(run_id, request, group)
            for group in groups
            if len(group) > 1 or request.strategy == "deterministic_extract"
        ]
        if not request.dry_run:
            for output in outputs:
                _create_memory(self._memory_service, output)
                self._repository.save_compacted_record(
                    MemoryCompactedRecord(
                        compacted_record_id=f"memory-compacted-record-{uuid4().hex}",
                        compaction_run_id=run_id,
                        output_memory_id=output.memory_id,
                        input_memory_ids=cast(list[str], output.metadata["input_memory_ids"]),
                        compaction_type=request.strategy,
                        confidence=output.confidence,
                        metadata={"strategy": request.strategy},
                        created_at=datetime.now(UTC),
                    )
                )
            for record in records:
                _update_metadata(
                    self._memory_service,
                    record,
                    {
                        **record.metadata,
                        "compacted_by": run_id,
                        "governance_status": "compacted",
                    },
                )
        output_ids = [output.memory_id for output in outputs]
        result = _result(
            run_id,
            request,
            status="completed",
            input_ids=input_ids,
            output_ids=output_ids,
            approval_required=False,
            approval_request_id=None,
            details={
                "input_count": len(input_ids),
                "output_count": len(output_ids),
                "dry_run": request.dry_run,
            },
        )
        self._save_run(request, result)
        self._emit("memory_compaction_completed", run_id, 0.35, result.model_dump(mode="json"))
        return result

    def get_run(self, compaction_run_id: str) -> MemoryCompactionResult | None:
        """Return one persisted compaction run as a public result."""
        run = self._repository.get_compaction_run(compaction_run_id)
        if run is None:
            return None
        return MemoryCompactionResult(
            compaction_run_id=run.compaction_run_id,
            status=run.status,
            dry_run=bool(run.result.get("dry_run", False)),
            strategy=run.strategy,
            input_memory_ids=run.input_memory_ids,
            output_memory_ids=run.output_memory_ids,
            compacted_count=len(run.output_memory_ids),
            skipped_count=int(run.result.get("skipped_count", 0)),
            failed_count=int(run.result.get("failed_count", 0)),
            approval_required=run.status == "pending_approval",
            approval_request_id=str(run.result.get("approval_request_id"))
            if run.result.get("approval_request_id")
            else None,
            result=run.result,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )

    def _create_approval(self, request: MemoryCompactionRequest, run_id: str) -> str | None:
        create = getattr(self._approval_service, "create_request", None)
        if not callable(create):
            return None
        approval = create(
            ApprovalCreateRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                requested_by=request.actor_id,
                action_type="memory.compact",
                resource_type="memory",
                resource_id=run_id,
                title=f"Approval required for memory compaction {run_id}",
                description="AION requires approval before this memory compaction run.",
                risk_assessment_id=None,
                priority="normal",
                approval_scope=request.owner_scope,
                payload={"compaction_run_id": run_id, "strategy": request.strategy},
                constraints=["memory_compaction_requires_approval"],
            )
        )
        return str(getattr(approval, "approval_request_id", "")) or None

    def _save_run(
        self,
        request: MemoryCompactionRequest,
        result: MemoryCompactionResult,
    ) -> None:
        self._repository.save_compaction_run(
            MemoryCompactionRunRecord(
                compaction_run_id=result.compaction_run_id,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                owner_scope=request.owner_scope,
                memory_types=[str(memory_type) for memory_type in request.memory_types],
                status=result.status,
                input_memory_ids=result.input_memory_ids,
                output_memory_ids=result.output_memory_ids,
                strategy=result.strategy,
                result={
                    **result.result,
                    "dry_run": result.dry_run,
                    "approval_request_id": result.approval_request_id,
                    "skipped_count": result.skipped_count,
                    "failed_count": result.failed_count,
                },
                created_by=request.actor_id,
                created_at=result.created_at,
                completed_at=result.completed_at,
            )
        )

    def _emit(
        self,
        event_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=node_id,
            event_type=cast(Any, event_type),
            node_type="compaction",
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=max(0.0, min(1.0, intensity)),
            payload=payload,
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


def _result(
    run_id: str,
    request: MemoryCompactionRequest,
    *,
    status: str,
    input_ids: list[str],
    output_ids: list[str],
    approval_required: bool,
    approval_request_id: str | None,
    details: dict[str, Any],
) -> MemoryCompactionResult:
    completed_at = (
        datetime.now(UTC)
        if status in {"completed", "failed", "blocked_by_policy"}
        else None
    )
    return MemoryCompactionResult(
        compaction_run_id=run_id,
        status=cast(Any, status),
        dry_run=request.dry_run,
        strategy=request.strategy,
        input_memory_ids=input_ids,
        output_memory_ids=output_ids,
        compacted_count=len(output_ids),
        skipped_count=max(0, len(input_ids) - len(output_ids)),
        failed_count=0 if status in {"completed", "pending_approval"} else 1,
        approval_required=approval_required,
        approval_request_id=approval_request_id,
        result=details,
        created_at=datetime.now(UTC),
        completed_at=completed_at,
    )


def _load_memories(
    memory_service: object,
    request: MemoryCompactionRequest,
) -> list[MemoryRecord]:
    if request.memory_ids:
        get = getattr(memory_service, "get", None)
        if not callable(get):
            return []
        records = [get(memory_id) for memory_id in request.memory_ids]
        return [record for record in records if isinstance(record, MemoryRecord)]
    list_active = getattr(memory_service, "list_active", None)
    if not callable(list_active):
        return []
    result = list_active(
        request.owner_scope,
        limit=request.max_input_records,
        memory_types=cast(list[Any], request.memory_types) or None,
    )
    if not isinstance(result, list):
        return []
    return [record for record in result if isinstance(record, MemoryRecord)]


def _groups_for_strategy(
    records: list[MemoryRecord],
    strategy: MemoryCompactionStrategy,
) -> list[list[MemoryRecord]]:
    if not records:
        return []
    if strategy == "deterministic_extract":
        return [records]
    key_names = {
        "merge_duplicates": ("summary",),
        "summarize_by_metadata_key": ("compaction_key", "rollup_key", "memory_type"),
        "preference_rollup": ("preference_key", "rollup_key", "memory_type"),
        "procedure_rollup": ("procedure_key", "rollup_key", "memory_type"),
    }
    groups: dict[str, list[MemoryRecord]] = defaultdict(list)
    for record in records:
        groups[_group_key(record, key_names[strategy])].append(record)
    return [group for group in groups.values() if group]


def _group_key(record: MemoryRecord, names: tuple[str, ...]) -> str:
    if names == ("summary",):
        return _normalized(record.summary)
    for name in names:
        if name == "memory_type":
            return record.memory_type
        value = record.metadata.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return record.memory_type


def _output_memory(
    run_id: str,
    request: MemoryCompactionRequest,
    group: list[MemoryRecord],
) -> MemoryRecord:
    confidence = max(0.0, min(1.0, fmean(record.confidence for record in group)))
    output_type = _output_type(request.strategy, group[0].memory_type)
    memory_id = f"memory-compacted-{uuid4().hex}"
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=cast(Any, output_type),
        owner_scope=request.owner_scope,
        source_event_id=None,
        content_ref=None,
        summary=_deterministic_summary(group),
        confidence=confidence,
        sensitivity=_highest_sensitivity(group),
        created_at=datetime.now(UTC),
        expires_at=None,
        metadata={
            "governance": "memory_compaction",
            "compaction_run_id": run_id,
            "strategy": request.strategy,
            "input_memory_ids": [record.memory_id for record in group],
            "source_count": len(group),
            "recall_only": True,
        },
    )


def _deterministic_summary(group: list[MemoryRecord]) -> str:
    unique = []
    seen: set[str] = set()
    for record in sorted(
        group,
        key=lambda item: (-item.confidence, item.created_at, item.memory_id),
    ):
        normalized = _normalized(record.summary)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(record.summary.strip())
    if len(unique) == 1:
        return unique[0]
    return " | ".join(unique[:5])


def _output_type(strategy: MemoryCompactionStrategy, fallback: str) -> str:
    if strategy == "procedure_rollup":
        return "procedural"
    if strategy == "preference_rollup":
        return "preference"
    if fallback in {"working", "episodic"}:
        return "semantic"
    return fallback


def _highest_sensitivity(records: list[MemoryRecord]) -> str:
    order = {"public": 0, "internal": 1, "low": 1, "medium": 2, "confidential": 2, "restricted": 3}
    return max((record.sensitivity for record in records), key=lambda value: order.get(value, 1))


def _create_memory(memory_service: object, memory: MemoryRecord) -> None:
    create = getattr(memory_service, "create", None)
    if callable(create):
        create(memory)


def _update_metadata(
    memory_service: object,
    record: MemoryRecord,
    metadata: dict[str, Any],
) -> None:
    update_metadata = getattr(memory_service, "update_metadata", None)
    if callable(update_metadata):
        update_metadata(record.memory_id, metadata)


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))
