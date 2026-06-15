"""Policy catalog coverage analysis."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.policy_catalog import PolicyCoverageReport, is_domain_specific
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy_catalog.defaults import DEFAULT_ACTION_SPECS
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.telemetry import emit_policy_telemetry

CRITICAL_TEST_CATEGORIES = {
    "policy",
    "autonomy",
    "risk",
    "approval",
    "execution",
    "workflow",
    "memory",
    "sandbox",
    "mcp",
    "model",
}


class PolicyCoverageAnalyzer:
    """Analyze policy catalog, permissions, roles, and tests."""

    def __init__(
        self,
        *,
        repository: PolicyCatalogRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        policy_files: list[Path] | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._policy_files = policy_files or []

    def generate(self) -> PolicyCoverageReport:
        """Generate a deterministic coverage report."""
        self._authorize()
        referenced_actions = self._referenced_actions()
        catalog = self._repository.list_actions(status=None)
        permissions = self._repository.list_permissions(status=None)
        roles = self._repository.list_role_templates(status=None)
        tests = self._repository.list_test_cases(status=None)
        catalogued_actions = {entry.action_type for entry in catalog}
        permission_values = [entry.permission for entry in permissions]
        test_actions = {test_case.action_type for test_case in tests}
        uncatalogued = sorted(referenced_actions - catalogued_actions)
        untested = sorted(
            entry.action_type
            for entry in catalog
            if entry.category in CRITICAL_TEST_CATEGORIES and entry.action_type not in test_actions
        )
        duplicate_permissions = sorted(
            permission
            for permission in set(permission_values)
            if permission_values.count(permission) > 1
        )
        known_permissions = set(permission_values)
        missing_role_permissions = sorted(
            permission
            for role in roles
            for permission in role.permissions
            if permission not in known_permissions
        )
        domain_violations = sorted(
            value
            for value in [
                *(entry.action_type for entry in catalog),
                *(entry.permission for entry in permissions),
            ]
            if is_domain_specific(value)
        )
        if missing_role_permissions:
            domain_violations.extend(
                f"unknown_role_permission:{item}" for item in missing_role_permissions
            )
        status = (
            "failed"
            if domain_violations
            else "warning"
            if uncatalogued or untested
            else "passed"
        )
        report = PolicyCoverageReport(
            report_id=f"policy-coverage-{uuid4().hex}",
            action_count=len(referenced_actions),
            catalogued_action_count=len(catalogued_actions.intersection(referenced_actions)),
            uncatalogued_actions=uncatalogued,
            permission_count=len(permissions),
            role_template_count=len(roles),
            test_case_count=len(tests),
            untested_actions=untested,
            duplicate_permissions=duplicate_permissions,
            domain_specific_violations=domain_violations,
            status=cast(Any, status),
            generated_at=datetime.now(UTC),
        )
        self._emit(
            "policy_coverage_generated",
            "policy",
            report.report_id,
            0.7 if report.status == "passed" else 1.0,
            {"status": report.status},
        )
        return report

    def _referenced_actions(self) -> set[str]:
        actions = {action for action, *_ in DEFAULT_ACTION_SPECS}
        pattern = re.compile(r'"([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)"')
        for path in self._policy_files:
            try:
                actions.update(pattern.findall(path.read_text(encoding="utf-8")))
            except OSError:
                continue
        return {
            action
            for action in actions
            if not any(action.startswith(prefix) for prefix in ("reason.", "audit."))
        }

    def _authorize(self) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"policy.coverage.read-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type="policy.coverage.read",
                resource_type="policy_coverage",
                resource_id=None,
                risk_level="low",
                approval_present=True,
                requested_permissions=["policy.coverage.read"],
                security_scope=["workspace:main"],
                context={},
            )
        )
        if not decision.allow:
            raise PermissionError(f"policy_denied:{decision.reason}")

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_policy_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=intensity,
            payload=payload,
        )
