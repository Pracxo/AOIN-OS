"""Static local runbook registry for Operator Control Tower."""

from __future__ import annotations

from aion_brain.contracts.operator import OperatorRunbookLink

_RUNBOOKS = (
    ("local_ops", "Local Ops Runbook", "operator", "docs/operations/local-ops-runbook.md"),
    ("troubleshooting", "Troubleshooting", "operator", "docs/operations/troubleshooting.md"),
    ("security", "Security Baseline", "security", "docs/operations/security-baseline.md"),
    ("resilience", "Resilience", "resilience", "docs/operations/resilience.md"),
    (
        "runtime_configuration",
        "Runtime Configuration",
        "runtime_config",
        "docs/operations/runtime-configuration.md",
    ),
    ("audit_integrity", "Audit Integrity", "audit", "docs/operations/audit-integrity.md"),
    ("backup_restore", "Backup Restore", "backups", "docs/operations/local-backup-restore.md"),
    ("release_packaging", "Release Packaging", "release", "docs/operations/release-packaging.md"),
    (
        "performance_benchmarking",
        "Performance Benchmarking",
        "performance",
        "docs/operations/performance-benchmarking.md",
    ),
    (
        "operator_control_tower",
        "Operator Control Tower",
        "operator",
        "docs/operations/operator-control-tower.md",
    ),
    (
        "release_candidate_checklist",
        "Release Candidate Checklist",
        "release",
        "docs/operations/release-candidate-checklist.md",
    ),
    ("quality_gates", "Quality Gates", "release", "docs/operations/quality-gates.md"),
)


class RunbookRegistry:
    """Expose generic local runbook links."""

    def list_runbooks(self) -> list[OperatorRunbookLink]:
        """Return all known local runbooks."""
        return [
            OperatorRunbookLink(
                runbook_id=runbook_id,
                title=title,
                category=category,  # type: ignore[arg-type]
                path=path,
                description=f"Local operator guidance for {title.lower()}.",
                tags=[category, "local", "operator"],
            )
            for runbook_id, title, category, path in _RUNBOOKS
        ]

    def get_by_category(self, category: str) -> list[OperatorRunbookLink]:
        """Return runbooks for one generic operator category."""
        return [runbook for runbook in self.list_runbooks() if runbook.category == category]
