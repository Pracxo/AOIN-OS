"""Deterministic recurrence evaluation for the local scheduler."""

from __future__ import annotations

import calendar
from datetime import UTC, datetime, timedelta

from aion_brain.contracts.scheduler import RecurrenceRule


class RecurrenceEvaluator:
    """Evaluate simple recurrence rules without external libraries."""

    def next_due(
        self,
        rule: RecurrenceRule,
        after: datetime,
        start_at: datetime,
        end_at: datetime | None = None,
    ) -> datetime | None:
        """Return the next due time after the given instant."""

        window_end = _utc(after) + timedelta(days=3660)
        due = self.due_between(
            rule,
            start_at,
            _utc(after) + timedelta(microseconds=1),
            window_end,
            end_at=end_at,
            max_items=1,
        )
        return due[0] if due else None

    def due_between(
        self,
        rule: RecurrenceRule,
        start_at: datetime,
        window_start: datetime,
        window_end: datetime,
        end_at: datetime | None = None,
        max_items: int = 1000,
    ) -> list[datetime]:
        """Return due instants inside a window, inclusive."""

        start = _utc(start_at)
        lower = _utc(window_start)
        upper = _utc(window_end)
        if upper < lower:
            return []
        rule_end = _utc(rule.until) if rule.until is not None else None
        configured_end = _utc(end_at) if end_at is not None else None
        end_candidates = [upper]
        if configured_end is not None:
            end_candidates.append(configured_end)
        if rule_end is not None:
            end_candidates.append(rule_end)
        effective_end = min(end_candidates)
        if effective_end < start:
            return []
        if rule.frequency == "manual":
            return []
        if rule.frequency == "once":
            return [start] if lower <= start <= effective_end else []

        values: list[datetime] = []
        candidate = start
        emitted = 0
        while candidate <= effective_end and len(values) < max_items:
            emitted += 1
            if rule.count is not None and emitted > rule.count:
                break
            if candidate >= lower and _matches(rule, candidate):
                values.append(candidate)
            candidate = _advance(rule, candidate)
        return values

    def is_due(
        self,
        rule: RecurrenceRule,
        at: datetime,
        start_at: datetime,
        end_at: datetime | None = None,
    ) -> bool:
        """Return whether a recurrence is due at the exact instant."""

        moment = _utc(at)
        due = self.due_between(
            rule,
            start_at,
            moment,
            moment,
            end_at=end_at,
            max_items=1,
        )
        return bool(due)


def _advance(rule: RecurrenceRule, candidate: datetime) -> datetime:
    if rule.frequency == "hourly":
        return candidate + timedelta(hours=rule.interval)
    if rule.frequency == "daily":
        return candidate + timedelta(days=rule.interval)
    if rule.frequency == "weekly":
        return candidate + timedelta(days=1)
    if rule.frequency == "monthly":
        return _add_months(candidate, rule.interval)
    return candidate + timedelta(days=1)


def _matches(rule: RecurrenceRule, candidate: datetime) -> bool:
    if rule.frequency == "weekly" and rule.days_of_week:
        return candidate.weekday() in set(rule.days_of_week)
    if rule.frequency == "monthly" and rule.day_of_month is not None:
        return candidate.day == min(
            rule.day_of_month,
            calendar.monthrange(candidate.year, candidate.month)[1],
        )
    if rule.months:
        return candidate.month in set(rule.months)
    return True


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
