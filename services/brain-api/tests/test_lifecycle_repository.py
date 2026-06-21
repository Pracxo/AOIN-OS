"""Lifecycle repository tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.lifecycle import LifecycleEvaluationRun
from aion_brain.contracts.retention import RetentionClassification
from tests.lifecycle_helpers import policy, repository


def test_lifecycle_repository_persists_policy_and_classification() -> None:
    repo = repository()
    saved_policy = repo.save_policy(policy())
    classification = RetentionClassification(
        classification_id="classification-1",
        resource_uri="aion://generic/res-1",
        resource_type="generic",
        resource_id="res-1",
        source_system="test",
        status="active",
        retention_class="unknown",
        lifecycle_state="current",
        sensitivity="internal",
        policy_refs=[saved_policy.lifecycle_policy_id],
        reasons=["test"],
        owner_scope=["workspace:main"],
    )

    repo.save_classification(classification)

    stored_policy = repo.get_policy(saved_policy.lifecycle_policy_id)
    assert stored_policy is not None
    assert stored_policy.lifecycle_policy_id == saved_policy.lifecycle_policy_id
    assert stored_policy.rule["hard_delete_allowed"] is False
    stored = repo.get_classification_by_uri("aion://generic/res-1", ["workspace:main"])
    assert stored is not None
    assert stored.classification_id == classification.classification_id
    assert stored.retention_class == "unknown"


def test_lifecycle_repository_persists_evaluation_run_counts() -> None:
    repo = repository()
    run = LifecycleEvaluationRun(
        lifecycle_evaluation_id="evaluation-1",
        status="dry_run",
        mode="dry_run",
        owner_scope=["workspace:main"],
        resources_evaluated=2,
        classifications_created=2,
        archive_candidates_created=1,
        redaction_candidates_created=1,
        purge_previews_created=1,
        reviews_created=1,
        created_at=datetime.now(UTC),
    )

    repo.save_evaluation_run(run)
    stored = repo.get_evaluation_run("evaluation-1")

    assert stored is not None
    assert stored.classifications_created == 2
    assert stored.archive_candidates_created == 1
    assert stored.redaction_candidates_created == 1
    assert stored.purge_previews_created == 1
    assert stored.reviews_created == 1
