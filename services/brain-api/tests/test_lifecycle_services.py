"""Lifecycle service tests."""

from __future__ import annotations

import pytest

from aion_brain.contracts.retention import LifecyclePolicyCreateRequest
from aion_brain.lifecycle.archive_planner import ArchivePlanner
from aion_brain.lifecycle.classifier import RetentionClassifier
from aion_brain.lifecycle.policies import LifecyclePolicyService
from aion_brain.lifecycle.purge_preview import PurgePreviewService
from aion_brain.lifecycle.redaction import sensitive_metadata_paths
from aion_brain.lifecycle.redaction_planner import RedactionPlanner
from aion_brain.lifecycle.reports import LifecycleReportService
from tests.kernel_fakes import AllowPolicy
from tests.lifecycle_helpers import old_descriptor, policy, repository
from tests.resource_registry_helpers import DenyPolicy, descriptor


def test_policy_deny_blocks_lifecycle_policy_create() -> None:
    service = LifecyclePolicyService(repository(), DenyPolicy())

    with pytest.raises(PermissionError):
        service.create_policy(
            LifecyclePolicyCreateRequest(
                name="blocked-policy",
                description="Generic policy blocked by policy.",
                owner_scope=["workspace:main"],
            )
        )


def test_retention_classifier_creates_advisory_classification() -> None:
    repo = repository()
    service = RetentionClassifier(repo, AllowPolicy())
    resource = old_descriptor()

    classification = service.classify_resource(resource, [policy()])

    assert classification.resource_uri == resource.resource_uri
    assert classification.lifecycle_state == "review_due"
    assert classification.metadata["source_records_mutated"] is False


def test_archive_candidate_conversion_requires_backup_verification() -> None:
    repo = repository()
    classifier = RetentionClassifier(repo, AllowPolicy())
    resource = old_descriptor()
    lifecycle_policy = policy(
        action_on_match="create_archive_candidate",
        archive_after_days=0,
    )
    classification = classifier.classify_resource(resource, [lifecycle_policy])
    planner = ArchivePlanner(repo, AllowPolicy())
    candidate = planner.create_candidate(
        resource,
        classification,
        lifecycle_policy,
        "Archive review is due.",
    )

    with pytest.raises(ValueError, match="backup_verification_required"):
        planner.convert_to_action_proposal(
            candidate.archive_candidate_id,
            actor_id="actor",
            approval_present=True,
            reason="approved for proposal",
        )


def test_redaction_planner_uses_sensitive_metadata_paths() -> None:
    repo = repository()
    classifier = RetentionClassifier(repo, AllowPolicy())
    resource = descriptor("res-sensitive").model_copy(
        update={"metadata": {"credential_ref": "secret-ref-1"}}
    )
    lifecycle_policy = policy(action_on_match="create_redaction_candidate")
    classification = classifier.classify_resource(resource, [lifecycle_policy])
    planner = RedactionPlanner(repo, AllowPolicy())

    candidate = planner.create_candidate(
        resource,
        classification,
        "Sensitive metadata requires review.",
    )

    assert sensitive_metadata_paths(resource.metadata) == ["metadata.credential_ref"]
    assert candidate.sensitive_paths == ["metadata.credential_ref"]
    assert candidate.metadata["redaction_executed"] is False


def test_purge_preview_is_blocked_and_does_not_delete() -> None:
    service = PurgePreviewService(repository(), AllowPolicy())

    preview = service.create_preview(
        ["aion://generic/res-1"],
        ["workspace:main"],
    )

    assert preview.status == "blocked"
    assert preview.hard_delete_allowed is False
    assert preview.result["purge_executed"] is False
    assert preview.blocked_count == 1


def test_lifecycle_report_is_local_and_advisory() -> None:
    repo = repository()
    service = LifecycleReportService(repo, AllowPolicy())

    report = service.generate(["workspace:main"])

    assert report.status == "passed"
    assert report.metadata["source_records_mutated"] is False
