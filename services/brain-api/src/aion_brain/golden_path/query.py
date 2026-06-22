"""Golden path query aggregation."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.golden_path import GoldenPathQuery
from aion_brain.golden_path.policy import authorize_golden_path_action
from aion_brain.golden_path.repository import GoldenPathRepository


class GoldenPathQueryService:
    """Aggregate golden path records for local operator and SDK queries."""

    def __init__(self, repository: GoldenPathRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, query: GoldenPathQuery) -> dict[str, Any]:
        """Return scenario, fixture, run, and report records."""

        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.query",
            query.scope,
            resource_type="golden_path",
        )
        scenarios = self._repository.list_scenarios(
            status=query.status if query.status in {"active", "disabled"} else None,
            scenario_type=query.scenario_type,
            limit=query.limit,
        )
        runs = self._repository.list_runs(
            status=query.status if query.status not in {"active", "disabled"} else None,
            trace_id=query.trace_id,
            limit=query.limit,
        )
        reports = self._repository.list_reports(
            status=query.status if query.status in {"passed", "warning", "failed"} else None,
            limit=query.limit,
        )
        fixture_packs = self._repository.list_fixture_packs(limit=query.limit)
        return {
            "scenarios": [item.model_dump(mode="json") for item in scenarios],
            "fixture_packs": [item.model_dump(mode="json") for item in fixture_packs],
            "runs": [item.model_dump(mode="json") for item in runs],
            "reports": [item.model_dump(mode="json") for item in reports],
            "total_count": len(scenarios) + len(fixture_packs) + len(runs) + len(reports),
            "constraints": [
                "dry_run_default",
                "no_external_calls",
                "no_tool_execution",
                "scenario_owned_records_only",
            ],
        }


__all__ = ["GoldenPathQueryService"]
