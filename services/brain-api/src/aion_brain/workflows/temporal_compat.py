"""Temporal SDK compatibility boundary."""

from importlib import import_module
from typing import Any

from aion_brain.contracts.workflows import WorkflowDefinition, WorkflowRunRequest


class TemporalCompat:
    """Contain all optional Temporal SDK import and API shape handling."""

    def is_available(self) -> bool:
        """Return whether the Temporal SDK package can be imported."""
        try:
            import_module("temporalio")
        except Exception:
            return False
        return True

    def availability_reason(self) -> str | None:
        """Return the unavailability reason for the optional package."""
        return None if self.is_available() else "temporal_package_unavailable"

    async def create_client(self, endpoint_ref: str, namespace: str) -> Any:
        """Create a Temporal client if the SDK is available."""
        try:
            client_module = import_module("temporalio.client")
            client_class = client_module.Client
            connect = client_class.connect
        except Exception as exc:
            raise RuntimeError(f"temporal_api_incompatible:{exc}") from exc
        return await connect(endpoint_ref, namespace=namespace)

    async def start_workflow(
        self,
        client: Any,
        workflow: WorkflowDefinition,
        request: WorkflowRunRequest,
    ) -> dict[str, Any]:
        """Start a Temporal workflow through a compatible client."""
        start_workflow = getattr(client, "start_workflow", None)
        if not callable(start_workflow):
            raise RuntimeError("temporal_api_incompatible:start_workflow_missing")
        result = await start_workflow(
            workflow.workflow_id,
            request.model_dump(mode="json"),
            id=request.workflow_run_id,
        )
        return {"workflow_run_id": getattr(result, "id", request.workflow_run_id)}

    async def get_workflow_status(self, client: Any, workflow_run_id: str) -> dict[str, Any]:
        """Return a Temporal workflow status through a compatible client."""
        get_handle = getattr(client, "get_workflow_handle", None)
        if not callable(get_handle):
            raise RuntimeError("temporal_api_incompatible:get_workflow_handle_missing")
        handle = get_handle(workflow_run_id)
        describe = getattr(handle, "describe", None)
        if not callable(describe):
            return {"workflow_run_id": workflow_run_id, "status": "unknown"}
        description = await describe()
        return {
            "workflow_run_id": workflow_run_id,
            "status": str(getattr(description, "status", "unknown")),
        }

    async def cancel_workflow(
        self,
        client: Any,
        workflow_run_id: str,
        reason: str | None,
    ) -> dict[str, Any]:
        """Cancel a Temporal workflow through a compatible client."""
        get_handle = getattr(client, "get_workflow_handle", None)
        if not callable(get_handle):
            raise RuntimeError("temporal_api_incompatible:get_workflow_handle_missing")
        handle = get_handle(workflow_run_id)
        cancel = getattr(handle, "cancel", None)
        if not callable(cancel):
            raise RuntimeError("temporal_api_incompatible:cancel_missing")
        await cancel(reason=reason)
        return {"workflow_run_id": workflow_run_id, "status": "cancelled"}

    async def close(self, client: Any) -> None:
        """Close a Temporal client when supported."""
        close = getattr(client, "close", None)
        if callable(close):
            result = close()
            if hasattr(result, "__await__"):
                await result
