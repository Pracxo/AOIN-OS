from __future__ import annotations

from knowledge_verified_memory_test_helpers import fp
from test_governed_learning_memory_contracts import (
    sample_existing_reference,
    sample_planning_components,
)

from aion_brain.contracts import governed_learning_memory as glm


def test_existing_different_candidate_for_same_identity_creates_material_hold():
    components = sample_planning_components(
        transaction_id="promotion-transaction-conflict",
    )
    existing = sample_existing_reference(
        components.identities[0],
        candidate_fingerprint=fp("different-candidate"),
    )
    report = glm.detect_knowledge_duplicates_and_conflicts(
        components.identities,
        existing_references=(existing,),
    )
    plan = glm.plan_knowledge_version(
        identity_plan=components.identities[0],
        snapshot=components.snapshots[0],
        request_kind=components.context.request.request_kind,
        conflict_report=report,
        existing_references=(existing,),
        effective_from=components.context.request.requested_at,
    )

    assert report.conflict_count == 1
    assert report.material_hold is True
    assert plan.disposition is glm.KnowledgeVersionDisposition.BLOCKED
