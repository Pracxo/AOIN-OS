"""AION-189 workspace closeout and memory-consolidation authorization tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aion_brain.contracts.workspace import (
    CognitiveCycleState,
    SalienceVector,
    SpecialistBid,
    SpecialistResponse,
    WorkspaceBroadcast,
    WorkspaceItem,
)
from aion_brain.workspace import (
    AntiStarvationController,
    AttentionArbiter,
    CognitiveCycleCoordinator,
    WorkspaceCapacityController,
)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION187_AUTHORIZATION_ID,
    AION188_MERGE_COMMIT,
    AION188_PR,
    AION188_TASK_ID,
    AION189_AUTHORIZATION_ID,
    AION189_EVALUATION_ID,
    AION190_SCOPE,
    AION190_TASK_ID,
    AION191_AUTHORIZATION_ID,
    AION191_EVALUATION_ID,
    AION193_AUTHORIZATION_ID,
    AION195_AUTHORIZATION_ID,
    AION198_AUTHORIZATION_ID,
    PROGRAM_ID,
    validate_aion189_authorization_payload,
    validate_aion189_evaluation_payload,
    validate_workspace_closeout,
    validate_workspace_closeout_no_go,
)

NOW = datetime(2026, 7, 21, 15, 50, tzinfo=UTC)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-189.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-189-workspace-evaluation.json",
    "examples/cognitive-architecture/aion-189-consolidation-authorization.json",
    "scripts/cognitive-workspace-closeout-check.sh",
    "scripts/cognitive-workspace-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _salience(
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


def _item(
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
        content_summary=f"bounded AION-189 workspace evidence for {item_id}",
        evidence_refs=(f"aion://aion-189/workspace/item/{item_id}",),
        metadata={"source": "aion-189-synthetic"},
        safety_critical=safety_critical,
        created_at=NOW,
    )


def _bid(
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
        item=workspace_item or _item(f"item-{bid_id}", specialist_id),
        salience=vector or _salience(),
        bid_kind=bid_kind,
        requested_capacity_units=units,
        evidence_refs=(f"aion://aion-189/workspace/bid/{bid_id}",),
        submitted_at=NOW,
    )


@dataclass
class _RecordingSpecialist:
    specialist_id: str
    approved: bool = True
    observed_count: int = 0

    def observe_broadcast(self, broadcast: WorkspaceBroadcast) -> SpecialistResponse:
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


def _deterministic_arbitration_passes() -> bool:
    vector = _salience(goal_relevance=0.7, confidence=0.9)
    alpha = _bid("bid-alpha", "specialist-alpha", vector=vector)
    beta = _bid("bid-beta", "specialist-beta", vector=vector)
    capacity = WorkspaceCapacityController(max_items=1, max_capacity_units=1)
    first = AttentionArbiter(capacity_controller=capacity).arbitrate(
        (beta, alpha),
        cycle_id="cycle-aion-189-deterministic",
    )
    second = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=1, max_capacity_units=1)
    ).arbitrate((alpha, beta), cycle_id="cycle-aion-189-deterministic")
    return (
        [bid.bid_id for bid in first.selected_bids] == ["bid-alpha"]
        and first.deterministic_replay_hash == second.deterministic_replay_hash
    )


def _safety_preemption_passes() -> bool:
    ordinary = _bid(
        "bid-ordinary",
        "specialist-planning",
        vector=_salience(goal_relevance=1.0, urgency=1.0, confidence=1.0, resource_cost=0.0),
    )
    safety = _bid(
        "bid-safety",
        "specialist-safety",
        workspace_item=_item(
            "item-safety",
            "specialist-safety",
            item_type="safety_finding",
            safety_critical=True,
        ),
        vector=_salience(safety_risk=0.8, confidence=0.6, resource_cost=1.0),
        bid_kind="critical_safety",
    )
    decision = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=1, max_capacity_units=1)
    ).arbitrate((ordinary, safety), cycle_id="cycle-aion-189-safety")
    return (
        [bid.bid_id for bid in decision.selected_bids] == ["bid-safety"]
        and decision.safety_preemption_applied is True
    )


def _anti_starvation_passes() -> bool:
    starvation = AntiStarvationController(
        deferred_counts={"specialist-waiting": 2},
        threshold=2,
        boost=4.0,
    )
    arbiter = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=1, max_capacity_units=1),
        starvation_controller=starvation,
    )
    waiting = _bid(
        "bid-waiting",
        "specialist-waiting",
        vector=_salience(goal_relevance=0.1, confidence=0.7),
    )
    current = _bid(
        "bid-current",
        "specialist-current",
        vector=_salience(goal_relevance=1.0, urgency=1.0, confidence=0.9),
    )
    decision = arbiter.arbitrate((current, waiting), cycle_id="cycle-aion-189-starvation")
    return (
        [bid.bid_id for bid in decision.selected_bids] == ["bid-waiting"]
        and decision.starvation_protection_applied is True
        and starvation.deferred_counts["specialist-waiting"] == 0
    )


def _bounded_capacity_passes() -> bool:
    bids = (
        _bid("bid-one", "specialist-one", units=2),
        _bid("bid-two", "specialist-two", units=1),
        _bid("bid-three", "specialist-three", units=2),
        _bid("bid-too-large", "specialist-large", units=4),
    )
    decision = AttentionArbiter(
        capacity_controller=WorkspaceCapacityController(max_items=2, max_capacity_units=3)
    ).arbitrate(bids, cycle_id="cycle-aion-189-capacity")
    return (
        len(decision.selected_bids) == 2
        and decision.used_capacity_units == 3
        and [bid.bid_id for bid in decision.deferred_bids] == ["bid-three"]
        and [bid.bid_id for bid in decision.rejected_bids] == ["bid-too-large"]
    )


def _duplicate_bid_handling_passes() -> bool:
    shared_item = _item("item-duplicate", "specialist-alpha")
    low = _bid(
        "bid-low",
        "specialist-alpha",
        workspace_item=shared_item,
        vector=_salience(goal_relevance=0.1, confidence=0.6),
    )
    high = _bid(
        "bid-high",
        "specialist-alpha",
        workspace_item=shared_item,
        vector=_salience(goal_relevance=1.0, confidence=0.9),
    )
    decision = AttentionArbiter().arbitrate((low, high), cycle_id="cycle-aion-189-duplicate")
    return (
        [bid.bid_id for bid in decision.selected_bids] == ["bid-high"]
        and [bid.bid_id for bid in decision.rejected_bids] == ["bid-low"]
    )


def _broadcast_consistency_and_provenance_pass() -> tuple[bool, bool, bool]:
    approved = _RecordingSpecialist("specialist-approved", approved=True)
    blocked = _RecordingSpecialist("specialist-blocked", approved=False)
    outside = _RecordingSpecialist("specialist-outside", approved=True)
    coordinator = CognitiveCycleCoordinator(specialists=(blocked, outside, approved))
    snapshot, decision, broadcast, responses = coordinator.run_cycle(
        cycle_id="cycle-aion-189-broadcast",
        sequence=1,
        bids=(_bid("bid-approved", "specialist-approved"),),
        approved_specialist_ids=("specialist-approved", "specialist-blocked"),
    )
    state = coordinator.cycle_state(
        cycle_id="cycle-aion-189-state",
        sequence=2,
        bids=(_bid("bid-state", "specialist-approved"),),
        approved_specialist_ids=("specialist-approved",),
    )
    broadcast_ok = (
        broadcast.approved_specialist_ids == ("specialist-approved", "specialist-blocked")
        and [response.specialist_id for response in responses] == ["specialist-approved"]
        and approved.observed_count == 2
        and blocked.observed_count == 0
        and outside.observed_count == 0
        and snapshot.selected_item_ids == ("item-bid-approved",)
        and decision.selected_bids[0].specialist_id == "specialist-approved"
    )
    provenance_ok = (
        snapshot.snapshot_hash is not None
        and decision.deterministic_replay_hash is not None
        and broadcast.broadcast_hash is not None
        and all(event.evidence_refs for event in snapshot.audit_events)
    )
    no_direct_actions = all(
        record.runtime_effect is False
        and record.direct_action_execution is False
        and record.network_calls == 0
        and record.connector_calls == 0
        and record.model_provider_calls == 0
        and record.model_call_made is False
        and record.production_exposure is False
        and record.model_weights_changed is False
        for record in (snapshot, decision, broadcast, *responses, state)
    )
    return broadcast_ok, provenance_ok and isinstance(state, CognitiveCycleState), no_direct_actions


def _concurrency_replay_passes() -> bool:
    bids = (
        _bid("bid-alpha", "specialist-alpha", vector=_salience(goal_relevance=0.8)),
        _bid("bid-beta", "specialist-beta", vector=_salience(goal_relevance=0.6)),
        _bid("bid-gamma", "specialist-gamma", vector=_salience(goal_relevance=0.4)),
    )

    def replay(index: int) -> str:
        ordered = bids if index % 2 == 0 else tuple(reversed(bids))
        decision = AttentionArbiter(
            capacity_controller=WorkspaceCapacityController(max_items=2, max_capacity_units=2)
        ).arbitrate(ordered, cycle_id="cycle-aion-189-concurrency")
        return decision.deterministic_replay_hash or ""

    with ThreadPoolExecutor(max_workers=4) as executor:
        hashes = tuple(executor.map(replay, range(8)))
    return len(set(hashes)) == 1 and hashes[0] != ""


def _workspace_evaluation_metrics() -> dict[str, float | int]:
    broadcast_ok, provenance_ok, no_direct_actions = _broadcast_consistency_and_provenance_pass()
    checks = {
        "deterministic_arbitration_rate": _deterministic_arbitration_passes(),
        "safety_preemption_rate": _safety_preemption_passes(),
        "anti_starvation_coverage": _anti_starvation_passes(),
        "bounded_capacity_rate": _bounded_capacity_passes(),
        "broadcast_consistency_rate": broadcast_ok,
        "duplicate_bid_handling_rate": _duplicate_bid_handling_passes(),
        "concurrency_replay_rate": _concurrency_replay_passes(),
        "cycle_provenance_coverage": provenance_ok,
    }
    return {
        **{key: 1.0 if value else 0.0 for key, value in checks.items()},
        "direct_action_count": 0 if no_direct_actions else 1,
        "forbidden_side_effects": 0,
    }


def test_aion_189_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative


def test_aion_189_ledgers_examples_and_no_go_validate() -> None:
    validate_workspace_closeout(ROOT)
    validate_workspace_closeout_no_go(ROOT)

    evaluation = _json("examples/cognitive-architecture/aion-189-workspace-evaluation.json")
    authorization = _json(
        "examples/cognitive-architecture/aion-189-consolidation-authorization.json"
    )
    validate_aion189_evaluation_payload(evaluation)
    validate_aion189_authorization_payload(authorization)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    auth_ledger = _json("docs/cognitive-architecture/authorization-ledger.json")

    assert program["program_id"] == PROGRAM_ID
    allowed_authorizations = {
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
        AION195_AUTHORIZATION_ID,
        AION198_AUTHORIZATION_ID,
    }
    active_authorization = program["active_cognitive_implementation_authorization"]
    assert active_authorization is None or active_authorization in allowed_authorizations
    assert (
        auth_ledger["active_cognitive_implementation_authorization"] is None
        or auth_ledger["active_cognitive_implementation_authorization"] in allowed_authorizations
    )
    assert auth_ledger["active_cognitive_implementation_authorization_count"] == (
        0 if active_authorization is None else 1
    )

    workspace_implementation = next(
        item
        for item in program["records"]
        if item.get("implementation_task") == AION188_TASK_ID
    )
    assert workspace_implementation["pr"] == AION188_PR
    assert workspace_implementation["merge_commit"] == AION188_MERGE_COMMIT
    assert workspace_implementation["task_state"] == "merged_evaluated_passed"

    closed = next(
        item
        for item in auth_ledger["records"]
        if item["authorization_id"] == AION187_AUTHORIZATION_ID
    )
    active = next(
        item
        for item in auth_ledger["records"]
        if item["authorization_id"] == AION189_AUTHORIZATION_ID
    )
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_closeout_evaluation"] == AION189_EVALUATION_ID
    assert closed["implementation_pr"] == AION188_PR
    assert closed["implementation_merge_commit"] == AION188_MERGE_COMMIT
    assert active["implementation_task"] == AION190_TASK_ID
    assert active["scope"] == AION190_SCOPE
    if auth_ledger["active_cognitive_implementation_authorization"] == AION189_AUTHORIZATION_ID:
        assert active["authorization_active"] is True
    else:
        assert active["authorization_active"] is False
        assert active["authorization_consumed"] is True
        assert active["authorization_closeout_evaluation"] == AION191_EVALUATION_ID


def test_aion_189_workspace_evaluation_meets_hard_pass_conditions() -> None:
    metrics = _workspace_evaluation_metrics()
    evidence = _json("examples/cognitive-architecture/aion-189-workspace-evaluation.json")

    assert metrics == evidence["hard_pass_conditions"]
    assert evidence["evaluation_matrix"] == {
        "deterministic_arbitration": "PASS",
        "safety_preemption": "PASS",
        "anti_starvation": "PASS",
        "bounded_capacity": "PASS",
        "broadcast_consistency": "PASS",
        "duplicate_bid_handling": "PASS",
        "concurrency": "PASS",
        "cycle_provenance": "PASS",
        "zero_direct_actions": "PASS",
    }
    assert evidence["side_effects"]["runtime_effect"] is False
    assert evidence["side_effects"]["network_calls"] == 0
    assert evidence["side_effects"]["model_provider_calls"] == 0
    assert evidence["side_effects"]["forbidden_side_effects"] == 0


def test_aion_189_does_not_implement_aion_190_runtime_surface() -> None:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    implementation_exists = any(
        item.get("implementation_task") == AION190_TASK_ID for item in program["records"]
    )
    if not implementation_exists:
        assert not (ROOT / "services/brain-api/src/aion_brain/memory_consolidation").exists()
        assert not (
            ROOT / "services/brain-api/src/aion_brain/contracts/memory_consolidation.py"
        ).exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/api/memory_consolidation.py").exists()


def test_aion_189_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = "aion-189-workspace-closeout"
    for script in (
        "scripts/cognitive-workspace-closeout-no-go-regression.sh",
        "scripts/cognitive-workspace-closeout-check.sh",
    ):
        path = ROOT / script
        assert os.access(path, os.X_OK), script
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
