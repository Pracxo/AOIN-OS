"""Deterministic context budget allocation."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.attention.repository import AttentionRepository
from aion_brain.contracts.attention import ContextBudget, ContextBudgetRequest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.retrieval import RetrievedContextItem
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.policy.base import PolicyAdapter

_DEFAULT_ALLOCATION = {
    "evidence_vault": 0.25,
    "semantic_memory": 0.20,
    "graph_memory": 0.15,
    "skill_registry": 0.10,
    "capability_registry": 0.10,
    "working_memory": 0.15,
    "recent_trace": 0.05,
}


class ContextBudgeter:
    """Allocate and apply deterministic context budgets."""

    def __init__(
        self,
        repository: AttentionRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def allocate(self, request: ContextBudgetRequest) -> ContextBudget:
        """Create a persisted context budget."""
        self._authorize(request)
        allocation = _allocation(request)
        budget = ContextBudget(
            context_budget_id=f"context-budget-{uuid4().hex}",
            trace_id=request.trace_id,
            focus_session_id=request.focus_session_id,
            intent_id=request.intent_id,
            context_id=request.context_id,
            max_items=request.max_items,
            max_chars=request.max_chars,
            allocation=allocation,
            used_items=0,
            used_chars=0,
            overflow_items=[],
            constraints=[],
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_context_budget(budget)
        self._emit_budget("context_budget_allocated", stored, 0.5)
        return stored

    def apply_budget(
        self,
        items: list[RetrievedContextItem],
        budget: ContextBudget,
    ) -> tuple[list[RetrievedContextItem], list[dict[str, object]]]:
        """Apply source item quotas and max character limits."""
        selected: list[RetrievedContextItem] = []
        overflow: list[dict[str, object]] = []
        source_counts: dict[str, int] = {}
        used_chars = 0
        ranked_items = sorted(
            items,
            key=lambda candidate: (
                -candidate.score,
                candidate.source,
                candidate.source_id,
            ),
        )
        for item in ranked_items:
            source = str(item.source)
            allowed = budget.allocation.get(source, 0)
            if source_counts.get(source, 0) >= allowed:
                overflow.append(_overflow_item(item, "source_quota_exceeded"))
                continue
            next_chars = len(item.content)
            if selected and used_chars + next_chars > budget.max_chars:
                overflow.append(_overflow_item(item, "max_chars_exceeded"))
                continue
            if not selected and next_chars > budget.max_chars:
                item = item.model_copy(update={"content": item.content[: budget.max_chars]})
                next_chars = len(item.content)
            selected.append(item)
            source_counts[source] = source_counts.get(source, 0) + 1
            used_chars += next_chars
            if len(selected) >= budget.max_items:
                break
        for item in items:
            already_overflowed = any(
                entry["item_id"] == item.item_id for entry in overflow
            )
            if item not in selected and not already_overflowed:
                overflow.append(_overflow_item(item, "max_items_exceeded"))
        updated = budget.model_copy(
            update={
                "used_items": len(selected),
                "used_chars": used_chars,
                "overflow_items": overflow,
                "constraints": (
                    [*budget.constraints, "context_budget_overflow"]
                    if overflow
                    else budget.constraints
                ),
            }
        )
        self._repository.save_context_budget(updated)
        if overflow:
            self._emit_budget(
                "context_budget_overflow_recorded",
                updated,
                min(1.0, len(overflow) / max(1, len(items))),
            )
        return selected, overflow

    def _authorize(self, request: ContextBudgetRequest) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"context.budget.allocate-{request.context_id or uuid4().hex}",
                trace_id=request.trace_id,
                actor_id=None,
                workspace_id=None,
                action_type="context.budget.allocate",
                resource_type="context_budget",
                resource_id=request.context_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=request.scope,
                context={"requested_sources": request.requested_sources},
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _emit_budget(self, event_type: str, budget: ContextBudget, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{budget.context_budget_id}-{event_type}",
            trace_id=budget.trace_id or budget.context_budget_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="budget",
            node_id=budget.context_budget_id,
            edge_from=budget.focus_session_id,
            edge_to=budget.context_id,
            intensity=max(0.0, min(1.0, intensity)),
            payload={
                "context_budget_id": budget.context_budget_id,
                "allocation": budget.allocation,
                "used_items": budget.used_items,
                "overflow_count": len(budget.overflow_items),
            },
            created_at=datetime.now(UTC),
        )
        _emit(self._telemetry_service, event)


def _allocation(request: ContextBudgetRequest) -> dict[str, int]:
    sources = request.requested_sources or list(_DEFAULT_ALLOCATION)
    weights = {
        source: request.priority_weights.get(source, _DEFAULT_ALLOCATION.get(source, 1.0))
        for source in sources
    }
    total = sum(weights.values()) or 1.0
    allocation = {
        source: int(request.max_items * (weight / total))
        for source, weight in weights.items()
    }
    remaining = request.max_items - sum(allocation.values())
    for source in sorted(sources):
        if remaining <= 0:
            break
        allocation[source] = allocation.get(source, 0) + 1
        remaining -= 1
    return allocation


def _overflow_item(item: RetrievedContextItem, reason: str) -> dict[str, object]:
    return {
        "item_id": item.item_id,
        "source": item.source,
        "source_id": item.source_id,
        "reason": reason,
        "score": item.score,
    }


def _emit(telemetry_service: object, event: VisualTelemetryEvent) -> None:
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
            return
        save = getattr(telemetry_service, "save_visual_telemetry", None)
        if callable(save):
            save(event.trace_id, [event])
    except Exception:
        return
