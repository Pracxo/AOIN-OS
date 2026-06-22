"""Operator contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.operator import (
    OperatorActionItem,
    OperatorOverviewRequest,
    OperatorQueueSummary,
    OperatorSnapshotRequest,
    OperatorStatusCard,
)


def test_operator_status_card_validates_category() -> None:
    with pytest.raises(ValidationError):
        OperatorStatusCard(
            card_id="card-1",
            title="Bad",
            category="not_generic",
            status="healthy",
            severity="low",
            summary="bad",
            metric={},
            source_type="test",
            updated_at=datetime.now(UTC),
            metadata={},
        )


def test_operator_status_card_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        OperatorStatusCard(
            card_id="card-1",
            title=" ",
            category="kernel",
            status="healthy",
            severity="low",
            summary="ok",
            metric={},
            source_type="test",
            updated_at=datetime.now(UTC),
            metadata={},
        )


def test_operator_queue_summary_validates_non_negative_counts() -> None:
    with pytest.raises(ValidationError):
        OperatorQueueSummary(
            queue_id="queue-1",
            queue_type="approvals",
            title="Approvals",
            pending_count=-1,
            running_count=0,
            blocked_count=0,
            failed_count=0,
            status="warning",
            severity="medium",
            metadata={},
        )


def test_operator_action_item_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        OperatorActionItem(
            action_item_id="action-1",
            source_type="approval",
            category="approvals",
            severity="medium",
            status="open",
            title="Review",
            description="Review item",
            recommended_action="review_pending_approval",
            owner_scope=[],
            metadata={},
        )


def test_operator_overview_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        OperatorOverviewRequest(owner_scope=[])


def test_operator_snapshot_request_validates_snapshot_type() -> None:
    with pytest.raises(ValidationError):
        OperatorSnapshotRequest(snapshot_type="bad", owner_scope=["workspace:main"])
