"""Read-only Operator Console view-model services."""

from __future__ import annotations

from aion_brain.contracts.local_auth import ConsoleRoleFilterRequest, LocalAuthContext
from aion_brain.contracts.operator_console import (
    ConsoleAuditRequest,
    ConsoleAuditResult,
    ConsoleViewModel,
    ConsoleViewModelRequest,
    ConsoleWorkflowMap,
)
from aion_brain.operator_console.audit import ConsoleContractAuditService, _authorize, _emit
from aion_brain.operator_console.data_sources import list_console_views, view_data_sources
from aion_brain.operator_console.extractors import extract_sections
from aion_brain.operator_console.view_models import build_view_model
from aion_brain.operator_console.workflows import console_demo_map, console_workflows


class ConsoleViewModelService:
    """Create read-only redacted console view models."""

    def __init__(
        self,
        *,
        container: object | None = None,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
        local_role_filter: object | None = None,
    ) -> None:
        self._container = container
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._local_role_filter = local_role_filter

    def list_views(self, scope: list[str]) -> list[dict[str, object]]:
        """List available console views."""
        _authorize(self._policy_adapter, "operator_console.view.read", scope)
        return [{"view": view, "read_only": True} for view in list_console_views()]

    def get_view_model(self, request: ConsoleViewModelRequest) -> ConsoleViewModel:
        """Return a redacted read-only view model."""
        _authorize(
            self._policy_adapter,
            "operator_console.view.read",
            request.owner_scope,
            actor_id=request.actor_id,
            trace_id=request.trace_id,
        )
        sources = view_data_sources(
            request.view,
            owner_scope=request.owner_scope,
            container=self._container,
        )
        sections = extract_sections(request, sources, container=self._container)
        model = build_view_model(request, sections=sections, data_sources=sources)
        model = self._apply_local_role_filter(model, request)
        _emit(
            self._telemetry_service,
            "operator_console_view_model_created",
            "operator_console_view",
            model.console_view_model_id,
            request.owner_scope,
            {"view": model.view, "status": model.status},
        )
        return model

    def get_workflows(self, scope: list[str]) -> list[ConsoleWorkflowMap]:
        """Return read-only console workflow maps."""
        _authorize(self._policy_adapter, "operator_console.workflow.read", scope)
        return console_workflows(scope)

    def get_demo_map(self, scope: list[str]) -> dict[str, object]:
        """Return the local console demo map."""
        _authorize(self._policy_adapter, "operator_console.query", scope)
        return console_demo_map(scope)

    def _apply_local_role_filter(
        self,
        model: ConsoleViewModel,
        request: ConsoleViewModelRequest,
    ) -> ConsoleViewModel:
        if self._local_role_filter is None:
            return model
        raw_context = request.metadata.get("local_auth_context") or request.metadata.get(
            "auth_context"
        )
        if not isinstance(raw_context, dict):
            return model
        auth_context = LocalAuthContext.model_validate(raw_context)
        filter_call = getattr(self._local_role_filter, "filter", None)
        if not callable(filter_call):
            return model
        result = filter_call(
            ConsoleRoleFilterRequest(
                trace_id=request.trace_id,
                view_model=model.model_dump(mode="json"),
                auth_context=auth_context,
                metadata={"source": "operator_console_view_model_service"},
            )
        )
        return ConsoleViewModel.model_validate(result.filtered_view_model)


class OperatorConsoleQueryService:
    """Small facade for query-style access."""

    def __init__(
        self,
        view_model_service: ConsoleViewModelService,
        audit_service: ConsoleContractAuditService,
    ) -> None:
        self._view_model_service = view_model_service
        self._audit_service = audit_service

    def audit(self, request: ConsoleAuditRequest) -> ConsoleAuditResult:
        return self._audit_service.audit(request)


__all__ = [
    "ConsoleContractAuditService",
    "ConsoleViewModelService",
    "OperatorConsoleQueryService",
]
