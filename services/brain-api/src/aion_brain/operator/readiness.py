"""Operator readiness aggregation."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.operator import OperatorReadinessReport
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.status_cards import StatusCardBuilder

_CORE_CATEGORIES = {"kernel", "health", "resilience", "runtime_config"}


class ReadinessAggregator:
    """Build release and local-ops readiness from local status signals."""

    def __init__(
        self,
        status_cards: StatusCardBuilder,
        action_center: ActionCenterService,
        telemetry_service: object | None = None,
    ) -> None:
        self._status_cards = status_cards
        self._action_center = action_center
        self._telemetry_service = telemetry_service

    def build_report(self, scope: list[str]) -> OperatorReadinessReport:
        """Build readiness report without external calls or remediation."""
        cards = self._status_cards.build_cards(scope)
        actions = self._action_center.build_action_items(scope)
        blockers = [
            item for item in actions if item.severity == "critical" and item.status == "open"
        ]
        warnings = [
            item
            for item in actions
            if item.severity in {"medium", "high"} and item.status == "open"
        ]
        checks = [
            {
                "name": f"{card.category}:{card.card_id}",
                "status": card.status,
                "severity": card.severity,
                "summary": card.summary,
            }
            for card in cards
        ]
        critical_card_failure = any(
            card.severity == "critical" and card.status in {"failed", "blocked"} for card in cards
        )
        core_failures = [
            card
            for card in cards
            if card.category in _CORE_CATEGORIES
            and card.status in {"failed", "blocked", "degraded"}
        ]
        release_ready = not blockers and not critical_card_failure
        local_ops_ready = not core_failures
        report = OperatorReadinessReport(
            readiness_id=f"readiness-{uuid4().hex}",
            overall_status="ready" if release_ready and local_ops_ready else "degraded",
            checks=checks,
            blockers=blockers,
            warnings=warnings,
            release_ready=release_ready,
            local_ops_ready=local_ops_ready,
            generated_at=datetime.now(UTC),
        )
        self._emit(report)
        return report

    def _emit(self, report: OperatorReadinessReport) -> None:
        from aion_brain.operator.action_center import _emit

        _emit(
            self._telemetry_service,
            "operator_readiness_generated",
            "readiness",
            report.readiness_id,
            0.9 if not report.release_ready else 0.5,
            {
                "release_ready": report.release_ready,
                "local_ops_ready": report.local_ops_ready,
            },
            None,
        )
