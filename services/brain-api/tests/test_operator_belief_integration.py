from __future__ import annotations

from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from tests.belief_helpers import AllowPolicy, belief_bundle, create_claim


def test_operator_action_center_surfaces_high_belief_contradiction() -> None:
    belief = belief_bundle()
    claim = create_claim(belief, "A contradiction should surface to the operator.")
    contradiction = belief.contradictions.create_contradiction(
        claim_id=claim.claim_id,
        source_type="generic",
        source_id="source-conflict",
        severity="high",
        reason="conflict",
    )
    action_center = ActionCenterService(
        OperatorRepository(),
        policy_adapter=AllowPolicy(),
        belief_contradiction_service=belief.contradictions,
    )

    items = action_center.build_action_items(["workspace:main"])

    assert any(item.source_id == contradiction.contradiction_id for item in items)
    assert items[0].recommended_action == "review_belief_contradiction"


def test_operator_queue_builder_counts_belief_contradictions() -> None:
    belief = belief_bundle()
    claim = create_claim(belief, "A queue can count an open contradiction.")
    belief.contradictions.create_contradiction(
        claim_id=claim.claim_id,
        source_type="generic",
        source_id="source-conflict",
        severity="high",
        reason="conflict",
    )
    builder = QueueSummaryBuilder(belief_contradiction_service=belief.contradictions)

    queues = builder.build_queues(["workspace:main"])
    belief_queue = next(queue for queue in queues if queue.title == "Belief Contradictions")

    assert belief_queue.metadata["available"] is True
    assert belief_queue.pending_count == 0
    assert belief_queue.metadata["item_count"] == 1
