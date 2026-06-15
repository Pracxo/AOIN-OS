"""Operator queue builder tests."""

from __future__ import annotations

from aion_brain.operator.queues import QueueSummaryBuilder
from tests.operator_fakes import SCOPE, FakeListService, FakeRecord, now


def test_queue_summary_builder_builds_approvals_queue() -> None:
    builder = QueueSummaryBuilder(
        approval_service=FakeListService([FakeRecord("approval-1", "pending", created_at=now())])
    )

    queue = next(item for item in builder.build_queues(SCOPE) if item.queue_type == "approvals")

    assert queue.pending_count == 1


def test_queue_summary_builder_builds_outbox_queue() -> None:
    builder = QueueSummaryBuilder(
        outbox_service=FakeListService([FakeRecord("outbox-1", "failed", created_at=now())])
    )

    queue = next(item for item in builder.build_queues(SCOPE) if item.queue_type == "outbox")

    assert queue.failed_count == 1
