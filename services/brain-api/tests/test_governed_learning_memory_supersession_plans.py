from __future__ import annotations

from test_governed_learning_memory_contracts import (
    sample_existing_reference,
    sample_planning_components,
)

from aion_brain.contracts import governed_learning_memory as glm


def test_supersession_plan_links_to_existing_version_without_writing():
    seed = sample_planning_components(transaction_id="promotion-transaction-supersession-seed")
    existing = sample_existing_reference(seed.identities[0])
    conflict_report = glm.detect_knowledge_duplicates_and_conflicts(
        seed.identities,
        existing_references=(),
    )
    plan = glm.plan_knowledge_version(
        identity_plan=seed.identities[0],
        snapshot=seed.snapshots[0],
        request_kind=glm.PromotionRequestKind.SUPERSESSION,
        conflict_report=conflict_report,
        existing_references=(existing,),
        effective_from=seed.context.request.requested_at,
    )

    assert plan.supersedes_version_id == existing.reference_id
    assert plan.persistent_version_created is False
    assert plan.historical_versions_preserved is True
