"""Temporal workflow adapter boundary tests."""

import ast
from pathlib import Path

from aion_brain.contracts.workflows import WorkflowRunRequest
from aion_brain.workflows.temporal_adapter import TemporalAdapter


class FakeTemporalCompat:
    """Temporal compatibility fake."""

    def is_available(self) -> bool:
        return False

    def availability_reason(self) -> str:
        return "temporal_package_unavailable"


def test_temporal_adapter_reports_disabled_without_sdk_dependency() -> None:
    """Temporal status is available without importing or installing Temporal."""
    adapter = TemporalAdapter(
        enabled=False,
        endpoint_ref=None,
        namespace="default",
        task_queue="aion-brain",
        compat=FakeTemporalCompat(),  # type: ignore[arg-type]
    )

    status = adapter.temporal_status()

    assert status.enabled is False
    assert status.package_available is False
    assert status.reason == "temporal_disabled"


def test_temporal_adapter_run_returns_structured_unavailable_run() -> None:
    """Temporal run path returns an AION-owned contract instead of SDK objects."""
    adapter = TemporalAdapter(
        enabled=True,
        endpoint_ref="temporal:7233",
        namespace="default",
        task_queue="aion-brain",
        compat=FakeTemporalCompat(),  # type: ignore[arg-type]
    )

    run = adapter.run_workflow(WorkflowRunRequest(workflow_id="workflow-1"))

    assert run.status == "failed"
    assert run.error["reason"] == "temporal_unavailable"


def test_no_direct_temporalio_imports_outside_python_imports() -> None:
    """Temporal SDK is not directly imported by Brain source modules."""
    source_root = Path(__file__).parents[1] / "src" / "aion_brain"
    offenders = []
    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            if any(
                module == "temporalio" or module.startswith("temporalio.")
                for module in modules
            ):
                offenders.append(path.relative_to(source_root).as_posix())

    assert offenders == []
