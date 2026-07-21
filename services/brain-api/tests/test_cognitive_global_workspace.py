"""AION-188 global cognitive workspace service tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.workspace import (
    CognitiveCycleState,
    SalienceVector,
    SpecialistBid,
    SpecialistResponse,
    WorkspaceItem,
)
from aion_brain.workspace import (
    AntiStarvationController,
    AttentionArbiter,
    CognitiveCycleCoordinator,
    WorkspaceCapacityController,
)

NOW = datetime(2026, 7, 21, 14, 0, tzinfo=UTC)


def salience(
    *,
    goal_relevance: float = 0.5,
    urgency: float = 0.5,
    novelty: float = 0.5,
    recurrence: float = 0.0,
    uncertainty: float = 0.4,
    expected_uncertainty_reduction: float = 0.4,
    information_gain: float = 0.4,
    expected_goal_progress: float = 0.4,
    safety_risk: float = 0.0,
    resource_cost: float = 0.2,
    irreversibility: float = 0.0,
    confidence: float = 0.8,
) -> SalienceVector:
    return SalienceVector(
        goal_relevance=goal_relevance,
        urgency=urgency,
        novelty=novelty,
        recurrence=recurrence,
        uncertainty=uncertainty,
        expected_uncertainty_reduction=expected_uncertainty_reduction,
        information_gain=information_gain,
        expected_goal_progress=expected_goal_progress,
        safety_risk=safety_risk,
        resource_cost=resource_cost,
        irreversibility=irreversibility,
        confidence=confidence,
    )


def item(
    item_id: str,
    specialist_id: str,
    *,
    item_type: str = "belief",
    safety_critical: bool = False,
) -> WorkspaceItem:
    return WorkspaceItem(
        item_id=item_id,
        source_specialist_id=specialist_id,
        item_type=item_type,
        content_summary=f"bounded summary for {item_id}",
        evidence_refs=(f"aion://workspace/item/{item_id}",),
        metadata={"source": "synthetic"},
        safety_critical=safety_critical,
        created_at=NOW,
    )


def bid(
    bid_id: str,
    specialist_id: str,
    *,
    workspace_item: WorkspaceItem | None = None,
    vector: SalienceVector | None = None,
    bid_kind: str = "ordinary",
    units: int = 1,
) -> SpecialistBid:
    return SpecialistBid(
        bid_id=bid_id,
        specialist_id=specialist_id,
        item=workspace_item or item(f"item-{bid_id}", specialist_id),
        salience=vector or salience(),
        bid_kind=bid_kind,
        requested_capacity_units=units,
        evidence_refs=(f"aion://workspace/bid/{bid_id}",),
        submitted_at=NOW,
    )


@dataclass
class RecordingSpecialist:
    specialist_id: str
    approved: bool = True
    observed_count: int = 0

    def observe_broadcast(self, broadcast) -> SpecialistResponse:
        self.observed_count += 1
        return SpecialistResponse(
            response_id=f"response-{self.specialist_id}-{broadcast.broadcast_id}",
            cycle_id=broadcast.cycle_id,
            broadcast_id=broadcast.broadcast_id,
            specialist_id=self.specialist_id,
            accepted_item_ids=tuple(item.item_id for item in broadcast.selected_items),
            evidence_refs=(broadcast.broadcast_hash or "",),
            created_at=NOW,
        )


def test_contracts_are_immutable_bounded_and_fingerprinted() -> None:
    workspace_item = item("item-contract", "specialist-alpha")
    same_item = item("item-contract", "specialist-alpha")

    assert workspace_item.fingerprint == same_item.fingerprint
    assert workspace_item.metadata["source"] == "synthetic"

    with pytest.raises(ValidationError):
        workspace_item.item_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        workspace_item.metadata["source"] = "changed"
    with pytest.raises(ValidationError):
        salience(goal_relevance=1.1)
    with pytest.raises(ValidationError):
        WorkspaceItem(
            item_id="item-unsafe",
            source_specialist_id="specialist-alpha",
            item_type="belief",
            content_summary="safe summary",
            metadata={"api_key": "sk-test"},
            created_at=NOW,
        )


def test_specialist_bids_are_immutable_and_match_source() -> None:
    workspace_bid = bid("bid-alpha", "specialist-alpha")

    assert workspace_bid.item.source_specialist_id == workspace_bid.specialist_id
    with pytest.raises(ValidationError):
        workspace_bid.bid_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        bid(
            "bid-mismatch",
            "specialist-alpha",
            workspace_item=item("item-beta", "specialist-beta"),
        )
    with pytest.raises(ValidationError):
        bid(
            "bid-low-safety",
            "specialist-alpha",
            workspace_item=item(
                "item-safety",
                "specialist-alpha",
                item_type="safety_finding",
                safety_critical=True,
            ),
            vector=salience(safety_risk=0.5),
            bid_kind="critical_safety",
        )


def test_attention_arbitration_is_deterministic_and_capacity_bounded() -> None:
    vector = salience(goal_relevance=0.7, confidence=0.9)
    alpha = bid("bid-alpha", "specialist-alpha", vector=vector)
    beta = bid("bid-beta", "specialist-beta", vector=vector)
    arbiter = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=1, max_capacity_units=1)
    )

    first = arbiter.arbitrate((beta, alpha), cycle_id="cycle-tie")
    second = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=1, max_capacity_units=1)
    ).arbitrate((alpha, beta), cycle_id="cycle-tie")

    assert [bid.bid_id for bid in first.selected_bids] == ["bid-alpha"]
    assert [bid.bid_id for bid in first.deferred_bids] == ["bid-beta"]
    assert first.deterministic_replay_hash == second.deterministic_replay_hash
    assert first.used_capacity_units == 1
    assert "capacity_limit_applied" in first.reason_codes


def test_critical_safety_findings_preempt_ordinary_bids() -> None:
    ordinary = bid(
        "bid-ordinary",
        "specialist-planning",
        vector=salience(goal_relevance=1.0, urgency=1.0, confidence=1.0, resource_cost=0.0),
    )
    safety = bid(
        "bid-safety",
        "specialist-safety",
        workspace_item=item(
            "item-safety",
            "specialist-safety",
            item_type="safety_finding",
            safety_critical=True,
        ),
        vector=salience(safety_risk=0.8, confidence=0.6, resource_cost=1.0),
        bid_kind="critical_safety",
    )
    arbiter = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=1, max_capacity_units=1)
    )

    decision = arbiter.arbitrate((ordinary, safety), cycle_id="cycle-safety")

    assert [bid.bid_id for bid in decision.selected_bids] == ["bid-safety"]
    assert decision.safety_preemption_applied is True
    assert "critical_safety_preemption" in decision.reason_codes


def test_duplicate_bids_keep_highest_ranked_item() -> None:
    shared_item = item("item-duplicate", "specialist-alpha")
    low = bid(
        "bid-low",
        "specialist-alpha",
        workspace_item=shared_item,
        vector=salience(goal_relevance=0.1, confidence=0.6),
    )
    high = bid(
        "bid-high",
        "specialist-alpha",
        workspace_item=shared_item,
        vector=salience(goal_relevance=1.0, confidence=0.9),
    )

    decision = AttentionArbiter().arbitrate((low, high), cycle_id="cycle-duplicate")

    assert [bid.bid_id for bid in decision.selected_bids] == ["bid-high"]
    assert [bid.bid_id for bid in decision.rejected_bids] == ["bid-low"]
    assert "duplicate_bid_rejected" in decision.reason_codes


def test_anti_starvation_boost_selects_deferred_specialist() -> None:
    starvation = AntiStarvationController(
        deferred_counts={"specialist-waiting": 2},
        threshold=2,
        boost=4.0,
    )
    arbiter = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=1, max_capacity_units=1),
        starvation_controller=starvation,
    )
    waiting = bid(
        "bid-waiting",
        "specialist-waiting",
        vector=salience(goal_relevance=0.1, confidence=0.7),
    )
    current = bid(
        "bid-current",
        "specialist-current",
        vector=salience(goal_relevance=1.0, urgency=1.0, confidence=0.9),
    )

    decision = arbiter.arbitrate((current, waiting), cycle_id="cycle-starvation")

    assert [bid.bid_id for bid in decision.selected_bids] == ["bid-waiting"]
    assert decision.starvation_protection_applied is True
    assert starvation.deferred_counts["specialist-waiting"] == 0


def test_coordinator_broadcasts_only_to_approved_specialists() -> None:
    approved = RecordingSpecialist("specialist-approved", approved=True)
    blocked = RecordingSpecialist("specialist-blocked", approved=False)
    outside = RecordingSpecialist("specialist-outside", approved=True)
    coordinator = CognitiveCycleCoordinator(specialists=(blocked, outside, approved))

    snapshot, decision, broadcast, responses = coordinator.run_cycle(
        cycle_id="cycle-broadcast",
        sequence=1,
        bids=(bid("bid-approved", "specialist-approved"),),
        approved_specialist_ids=("specialist-approved", "specialist-blocked"),
    )
    state = coordinator.cycle_state(
        cycle_id="cycle-state",
        sequence=2,
        bids=(bid("bid-state", "specialist-approved"),),
        approved_specialist_ids=("specialist-approved",),
    )

    assert broadcast.approved_specialist_ids == ("specialist-approved", "specialist-blocked")
    assert [response.specialist_id for response in responses] == ["specialist-approved"]
    assert approved.observed_count == 2
    assert blocked.observed_count == 0
    assert outside.observed_count == 0
    assert snapshot.selected_item_ids == ("item-bid-approved",)
    assert decision.selected_bids[0].specialist_id == "specialist-approved"
    assert isinstance(state, CognitiveCycleState)
    assert state.status == "complete"
    assert state.runtime_effect is False
