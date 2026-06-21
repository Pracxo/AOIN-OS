"""Lifecycle contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.lifecycle import (
    ArchiveCandidate,
    PurgePreview,
    RedactionCandidate,
)
from aion_brain.contracts.retention import LifecyclePolicyCreateRequest


def test_lifecycle_policy_allows_disabled_hard_delete_marker() -> None:
    request = LifecyclePolicyCreateRequest(
        name="safe-policy",
        description="Safe generic lifecycle policy.",
        owner_scope=["workspace:main"],
        rule={"hard_delete_allowed": False},
        metadata={"hard_delete_enabled": False},
    )

    assert request.rule["hard_delete_allowed"] is False


def test_lifecycle_policy_rejects_enabled_hard_delete_marker() -> None:
    with pytest.raises(ValidationError):
        LifecyclePolicyCreateRequest(
            name="unsafe-policy",
            description="Unsafe generic lifecycle policy.",
            owner_scope=["workspace:main"],
            rule={"hard_delete_allowed": True},
        )


def test_archive_candidate_requires_backup_before_conversion() -> None:
    with pytest.raises(ValidationError):
        ArchiveCandidate(
            archive_candidate_id="archive-1",
            resource_uri="aion://generic/res-1",
            resource_type="generic",
            resource_id="res-1",
            source_system="test",
            status="converted_to_action_proposal",
            severity="medium",
            reason="Review archive candidate.",
            backup_required=True,
            backup_verified=False,
            owner_scope=["workspace:main"],
        )


def test_purge_preview_never_allows_hard_delete() -> None:
    with pytest.raises(ValidationError):
        PurgePreview(
            purge_preview_id="purge-1",
            status="created",
            owner_scope=["workspace:main"],
            resource_uris=["aion://generic/res-1"],
            resource_count=1,
            blocked_count=0,
            allowed_count=1,
            requires_backup=True,
            backup_verified=True,
            hard_delete_allowed=True,
            created_at=datetime.now(UTC),
        )


def test_redaction_candidate_rejects_secret_values_in_paths() -> None:
    with pytest.raises(ValidationError):
        RedactionCandidate(
            redaction_candidate_id="redaction-1",
            resource_uri="aion://generic/res-1",
            resource_type="generic",
            resource_id="res-1",
            source_system="test",
            status="proposed",
            severity="high",
            reason="Review sensitive metadata.",
            sensitive_paths=["metadata.sk-test-secret"],
            suggested_redaction_mode="manual_review",
            owner_scope=["workspace:main"],
        )
