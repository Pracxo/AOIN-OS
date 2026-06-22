"""Operator runbook tests."""

from aion_brain.operator.runbooks import RunbookRegistry


def test_runbook_registry_returns_expected_runbook_links() -> None:
    paths = {runbook.path for runbook in RunbookRegistry().list_runbooks()}

    assert "docs/operations/operator-control-tower.md" in paths
    assert "docs/operations/audit-integrity.md" in paths
