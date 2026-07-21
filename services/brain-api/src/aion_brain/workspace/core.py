"""Deterministic local global-workspace services."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol

from aion_brain.contracts.workspace import (
    AttentionDecision,
    CognitiveCycleState,
    SpecialistBid,
    SpecialistResponse,
    WorkspaceAuditEvent,
    WorkspaceBroadcast,
    WorkspaceSnapshot,
)

GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)


class CognitiveSpecialist(Protocol):
    """Protocol for approved in-process workspace specialists."""

    @property
    def specialist_id(self) -> str: ...

    @property
    def approved(self) -> bool: ...

    def observe_broadcast(self, broadcast: WorkspaceBroadcast) -> SpecialistResponse: ...


class AntiStarvationController:
    """Track deferred specialists and add a deterministic ordinary-bid boost."""

    def __init__(
        self,
        *,
        deferred_counts: dict[str, int] | None = None,
        threshold: int = 2,
        boost: float = 4.0,
    ) -> None:
        if threshold < 1:
            raise ValueError("threshold must be positive")
        if boost < 0.0:
            raise ValueError("boost must be non-negative")
        self._deferred_counts = dict(deferred_counts or {})
        self._threshold = threshold
        self._boost = boost

    @property
    def deferred_counts(self) -> dict[str, int]:
        """Return a copy of specialist deferral counts."""

        return dict(self._deferred_counts)

    def boost_for(self, specialist_id: str) -> float:
        """Return the deterministic anti-starvation boost for a specialist."""

        if self._deferred_counts.get(specialist_id, 0) >= self._threshold:
            return self._boost
        return 0.0

    def record_decision(self, decision: AttentionDecision) -> None:
        """Update counts after one attention decision."""

        selected = {bid.specialist_id for bid in decision.selected_bids}
        deferred = {bid.specialist_id for bid in decision.deferred_bids}
        for specialist_id in selected:
            self._deferred_counts[specialist_id] = 0
        for specialist_id in deferred - selected:
            self._deferred_counts[specialist_id] = (
                self._deferred_counts.get(specialist_id, 0) + 1
            )


class WorkspaceCapacityController:
    """Apply bounded item and capacity-unit limits."""

    def __init__(self, *, max_items: int = 5, max_capacity_units: int = 16) -> None:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        if max_capacity_units < 1:
            raise ValueError("max_capacity_units must be positive")
        self.max_items = max_items
        self.max_capacity_units = max_capacity_units

    def select(
        self,
        bids: tuple[SpecialistBid, ...],
    ) -> tuple[tuple[SpecialistBid, ...], tuple[SpecialistBid, ...], tuple[SpecialistBid, ...]]:
        """Return selected, deferred, and capacity-rejected bids."""

        selected: list[SpecialistBid] = []
        deferred: list[SpecialistBid] = []
        rejected: list[SpecialistBid] = []
        used_units = 0
        for bid in bids:
            if bid.requested_capacity_units > self.max_capacity_units:
                rejected.append(bid)
                continue
            if (
                len(selected) < self.max_items
                and used_units + bid.requested_capacity_units <= self.max_capacity_units
            ):
                selected.append(bid)
                used_units += bid.requested_capacity_units
                continue
            deferred.append(bid)
        return tuple(selected), tuple(deferred), tuple(rejected)


class AttentionArbiter:
    """Select a deterministic bounded working set from specialist bids."""

    def __init__(
        self,
        *,
        capacity_controller: WorkspaceCapacityController | None = None,
        starvation_controller: AntiStarvationController | None = None,
    ) -> None:
        self._capacity_controller = capacity_controller or WorkspaceCapacityController()
        self._starvation_controller = starvation_controller or AntiStarvationController()

    def arbitrate(
        self,
        bids: Iterable[SpecialistBid],
        *,
        cycle_id: str,
        decision_id: str | None = None,
    ) -> AttentionDecision:
        """Return an attention decision without side effects outside this process."""

        unique_bids, duplicate_bids = self._deduplicate(tuple(bids))
        ranked = tuple(sorted(unique_bids, key=self._rank_key))
        selected, deferred, capacity_rejected = self._capacity_controller.select(ranked)
        reason_codes = ["deterministic_attention_arbitration"]
        if duplicate_bids:
            reason_codes.append("duplicate_bid_rejected")
        if capacity_rejected or deferred:
            reason_codes.append("capacity_limit_applied")
        safety_preemption = bool(selected and selected[0].is_safety_critical)
        if safety_preemption:
            reason_codes.append("critical_safety_preemption")
        starvation_protection = any(
            self._starvation_controller.boost_for(bid.specialist_id) > 0
            for bid in selected
        )
        if starvation_protection:
            reason_codes.append("anti_starvation_boost")
        decision = AttentionDecision(
            decision_id=decision_id or f"attention-decision-{cycle_id}",
            cycle_id=cycle_id,
            selected_bids=selected,
            deferred_bids=tuple(sorted(deferred, key=lambda bid: bid.bid_id)),
            rejected_bids=tuple(
                sorted((*duplicate_bids, *capacity_rejected), key=lambda bid: bid.bid_id)
            ),
            capacity_limit=self._capacity_controller.max_items,
            capacity_units_limit=self._capacity_controller.max_capacity_units,
            used_capacity_units=sum(bid.requested_capacity_units for bid in selected),
            safety_preemption_applied=safety_preemption,
            starvation_protection_applied=starvation_protection,
            reason_codes=tuple(reason_codes),
            created_at=GENERATED_AT,
        )
        self._starvation_controller.record_decision(decision)
        return decision

    def _deduplicate(
        self,
        bids: tuple[SpecialistBid, ...],
    ) -> tuple[tuple[SpecialistBid, ...], tuple[SpecialistBid, ...]]:
        by_key: dict[str, SpecialistBid] = {}
        duplicates: list[SpecialistBid] = []
        for bid in bids:
            existing = by_key.get(bid.dedupe_key)
            if existing is None:
                by_key[bid.dedupe_key] = bid
                continue
            winner, loser = sorted((existing, bid), key=self._rank_key)[:2]
            by_key[bid.dedupe_key] = winner
            duplicates.append(loser)
        return tuple(by_key.values()), tuple(duplicates)

    def _rank_key(self, bid: SpecialistBid) -> tuple[int, float, float, str, str]:
        safety_rank = 0 if bid.is_safety_critical else 1
        starvation_boost = self._starvation_controller.boost_for(bid.specialist_id)
        score = bid.salience.weighted_score() + starvation_boost
        return (
            safety_rank,
            -score,
            -bid.salience.confidence,
            bid.specialist_id,
            bid.bid_id,
        )


class WorkspaceBroadcastService:
    """Create deterministic broadcasts from attention decisions."""

    def create_broadcast(
        self,
        decision: AttentionDecision,
        *,
        cycle_id: str,
        approved_specialist_ids: Iterable[str],
        broadcast_id: str | None = None,
    ) -> WorkspaceBroadcast:
        approved = tuple(sorted(set(approved_specialist_ids)))
        return WorkspaceBroadcast(
            broadcast_id=broadcast_id or f"workspace-broadcast-{cycle_id}",
            cycle_id=cycle_id,
            decision_id=decision.decision_id,
            selected_items=tuple(bid.item for bid in decision.selected_bids),
            approved_specialist_ids=approved,
            created_at=GENERATED_AT,
        )


class CognitiveCycleCoordinator:
    """Coordinate one local attention-and-broadcast cycle."""

    def __init__(
        self,
        *,
        arbiter: AttentionArbiter | None = None,
        broadcast_service: WorkspaceBroadcastService | None = None,
        specialists: Iterable[CognitiveSpecialist] = (),
    ) -> None:
        self._arbiter = arbiter or AttentionArbiter()
        self._broadcast_service = broadcast_service or WorkspaceBroadcastService()
        self._specialists = tuple(specialists)

    def run_cycle(
        self,
        *,
        cycle_id: str,
        sequence: int,
        bids: Iterable[SpecialistBid],
        approved_specialist_ids: Iterable[str],
    ) -> tuple[
        WorkspaceSnapshot,
        AttentionDecision,
        WorkspaceBroadcast,
        tuple[SpecialistResponse, ...],
    ]:
        """Run one deterministic local cycle and return its records."""

        approved = tuple(sorted(set(approved_specialist_ids)))
        decision = self._arbiter.arbitrate(
            tuple(bids),
            cycle_id=cycle_id,
            decision_id=f"attention-decision-{cycle_id}",
        )
        broadcast = self._broadcast_service.create_broadcast(
            decision,
            cycle_id=cycle_id,
            approved_specialist_ids=approved,
            broadcast_id=f"workspace-broadcast-{cycle_id}",
        )
        responses = self._collect_responses(broadcast, approved)
        audit_events = self._audit_events(cycle_id, decision, broadcast, responses)
        snapshot = WorkspaceSnapshot(
            snapshot_id=f"workspace-snapshot-{cycle_id}",
            cycle_id=cycle_id,
            sequence=sequence,
            active_items=broadcast.selected_items,
            selected_item_ids=tuple(item.item_id for item in broadcast.selected_items),
            deferred_item_ids=tuple(bid.item.item_id for bid in decision.deferred_bids),
            approved_specialist_ids=approved,
            audit_events=audit_events,
            created_at=GENERATED_AT,
        )
        return snapshot, decision, broadcast, responses

    def cycle_state(
        self,
        *,
        cycle_id: str,
        sequence: int,
        bids: Iterable[SpecialistBid],
        approved_specialist_ids: Iterable[str],
    ) -> CognitiveCycleState:
        """Return complete cycle state for callers that need a single record."""

        snapshot, decision, broadcast, responses = self.run_cycle(
            cycle_id=cycle_id,
            sequence=sequence,
            bids=bids,
            approved_specialist_ids=approved_specialist_ids,
        )
        return CognitiveCycleState(
            cycle_id=cycle_id,
            sequence=snapshot.sequence,
            status="complete",
            decision=decision,
            broadcast=broadcast,
            responses=responses,
            audit_events=snapshot.audit_events,
            created_at=GENERATED_AT,
        )

    def _collect_responses(
        self,
        broadcast: WorkspaceBroadcast,
        approved_specialist_ids: tuple[str, ...],
    ) -> tuple[SpecialistResponse, ...]:
        approved = set(approved_specialist_ids)
        responses: list[SpecialistResponse] = []
        for specialist in sorted(self._specialists, key=lambda item: item.specialist_id):
            if not specialist.approved or specialist.specialist_id not in approved:
                continue
            responses.append(specialist.observe_broadcast(broadcast))
        return tuple(responses)

    def _audit_events(
        self,
        cycle_id: str,
        decision: AttentionDecision,
        broadcast: WorkspaceBroadcast,
        responses: tuple[SpecialistResponse, ...],
    ) -> tuple[WorkspaceAuditEvent, ...]:
        events = [
            WorkspaceAuditEvent(
                event_id=f"workspace-audit-{cycle_id}-attention",
                event_type="attention_selected",
                cycle_id=cycle_id,
                item_refs=tuple(bid.item.item_id for bid in decision.selected_bids),
                evidence_refs=(decision.deterministic_replay_hash or "",),
                created_at=GENERATED_AT,
            ),
            WorkspaceAuditEvent(
                event_id=f"workspace-audit-{cycle_id}-broadcast",
                event_type="broadcast_created",
                cycle_id=cycle_id,
                item_refs=tuple(item.item_id for item in broadcast.selected_items),
                evidence_refs=(broadcast.broadcast_hash or "",),
                created_at=GENERATED_AT,
            ),
        ]
        for response in responses:
            events.append(
                WorkspaceAuditEvent(
                    event_id=f"workspace-audit-{cycle_id}-response-{response.specialist_id}",
                    event_type="specialist_response_recorded",
                    cycle_id=cycle_id,
                    specialist_id=response.specialist_id,
                    item_refs=response.accepted_item_ids,
                    evidence_refs=(response.response_id,),
                    created_at=GENERATED_AT,
                )
            )
        events.append(
            WorkspaceAuditEvent(
                event_id=f"workspace-audit-{cycle_id}-complete",
                event_type="cycle_completed",
                cycle_id=cycle_id,
                item_refs=tuple(item.item_id for item in broadcast.selected_items),
                evidence_refs=(decision.decision_id, broadcast.broadcast_id),
                created_at=GENERATED_AT,
            )
        )
        return tuple(events)
