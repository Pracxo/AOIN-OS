"""Console view model assembly helpers."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.contracts.operator_console import (
    ConsoleDataSource,
    ConsoleView,
    ConsoleViewModel,
    ConsoleViewModelRequest,
    ConsoleViewSection,
    utc_now,
)
from aion_brain.operator_console.action_boundaries import (
    allowed_action_descriptors,
    forbidden_action_descriptors,
)


def build_view_model(
    request: ConsoleViewModelRequest,
    *,
    sections: list[ConsoleViewSection],
    data_sources: list[ConsoleDataSource],
) -> ConsoleViewModel:
    """Build a read-only console view model."""
    unavailable = [source for source in data_sources if not source.available]
    status = "warning" if unavailable else "ready"
    return ConsoleViewModel(
        console_view_model_id=f"console-view-{uuid4().hex}",
        trace_id=request.trace_id,
        view=request.view,
        status=status,
        read_only=True,
        owner_scope=request.owner_scope,
        title=_title(request.view),
        summary=f"Read-only {request.view.replace('_', ' ')} console view model.",
        sections=sections,
        global_actions=allowed_action_descriptors() if request.include_actions else [],
        forbidden_actions=(
            forbidden_action_descriptors() if request.include_forbidden_actions else []
        ),
        data_sources=data_sources,
        generated_at=utc_now(),
        redaction_applied=True,
        safety_findings=[],
        metadata={
            "write_actions_enabled": False,
            "frontend_enabled": False,
            "descriptor_only_actions": True,
        },
    )


def _title(view: ConsoleView) -> str:
    return view.replace("_", " ").title()


__all__ = ["build_view_model"]
