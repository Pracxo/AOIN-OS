"""Recurrence evaluator tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.scheduler import RecurrenceRule
from aion_brain.scheduler.recurrence import RecurrenceEvaluator


def test_once_rule_is_due_once() -> None:
    evaluator = RecurrenceEvaluator()
    start = datetime(2026, 1, 1, 9, tzinfo=UTC)

    assert evaluator.due_between(
        RecurrenceRule(frequency="once"),
        start,
        datetime(2026, 1, 1, 8, tzinfo=UTC),
        datetime(2026, 1, 1, 10, tzinfo=UTC),
    ) == [start]


def test_monthly_overflow_clamps_to_last_day() -> None:
    evaluator = RecurrenceEvaluator()
    start = datetime(2026, 1, 31, 9, tzinfo=UTC)

    next_due = evaluator.next_due(
        RecurrenceRule(frequency="monthly", day_of_month=31),
        datetime(2026, 2, 1, tzinfo=UTC),
        start,
    )

    assert next_due == datetime(2026, 2, 28, 9, tzinfo=UTC)


def test_manual_rule_has_no_due_items() -> None:
    evaluator = RecurrenceEvaluator()
    assert (
        evaluator.due_between(
            RecurrenceRule(frequency="manual"),
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        )
        == []
    )
