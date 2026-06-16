from __future__ import annotations

from tests.self_model_helpers import bundle


def test_capability_awareness_marks_optional_adapter_unavailable() -> None:
    services = bundle()

    records = services.capabilities.refresh(["workspace:main"], dry_run=True)
    graphiti = next(item for item in records if item.capability_key == "aion.optional.graphiti")

    assert graphiti.capability_type == "optional_adapter"
    assert graphiti.availability == "optional_unavailable"


def test_capability_awareness_marks_sandbox_execution_dry_run_only() -> None:
    services = bundle()

    sandbox = services.capabilities.get_capability(
        "aion.sandbox.execution",
        ["workspace:main"],
    )

    assert sandbox is not None
    assert sandbox.dry_run_only is True
    assert sandbox.status == "dry_run_only"
