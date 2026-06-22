"""Bootstrap query aggregation."""

from __future__ import annotations

from typing import Any

from aion_brain.bootstrap.policy import authorize_bootstrap_action
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.contracts.setup_doctor import SetupFinding


class BootstrapQueryService:
    """Aggregate bootstrap records for local operator and SDK queries."""

    def __init__(self, repository: BootstrapRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(
        self, scope: list[str], *, limit: int = 50, status: str | None = None
    ) -> dict[str, Any]:
        """Return bootstrap records."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.query",
            scope,
            resource_type="bootstrap",
        )
        return {
            "profiles": [
                item.model_dump(mode="json")
                for item in self._repository.list_profiles(status=status, limit=limit)
            ],
            "seed_bundles": [
                item.model_dump(mode="json")
                for item in self._repository.list_bundles(status=status, limit=limit)
            ],
            "runs": [
                item.model_dump(mode="json")
                for item in self._repository.list_runs(status=status, limit=limit)
            ],
            "reports": [
                item.model_dump(mode="json")
                for item in self._repository.list_reports(status=status, limit=limit)
            ],
            "constraints": [
                "local_only",
                "dry_run_default",
                "no_external_calls",
                "no_package_install",
                "no_production_provisioning",
            ],
        }

    def list_findings(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[SetupFinding]:
        """List setup findings."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.finding.read",
            scope,
            resource_type="setup_finding",
        )
        return self._repository.list_findings(
            status=status,
            severity=severity,
            category=category,
            limit=limit,
        )

    def dismiss_finding(
        self,
        setup_finding_id: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        reason: str = "dismissed",
    ) -> SetupFinding | None:
        """Dismiss one setup finding."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.finding.update",
            scope,
            actor_id=actor_id,
            resource_type="setup_finding",
            resource_id=setup_finding_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return self._repository.dismiss_finding(setup_finding_id, reason)


__all__ = ["BootstrapQueryService"]
