"""Dry-run plan builder for module mock invocations."""

from __future__ import annotations

from aion_brain.contracts.module_mock_runtime import ModuleMockInvocationCreateRequest


class ModuleMockPlanService:
    """Build a deterministic non-executable invocation plan."""

    def create_plan(self, request: ModuleMockInvocationCreateRequest) -> dict[str, object]:
        """Return the static dry-run plan used by the simulator."""

        return {
            "mode": "dry_run",
            "capability_binding_id": request.capability_binding_id,
            "capability_key": request.capability_key,
            "steps": [
                "load_binding_metadata",
                "load_mock_profile_metadata",
                "redact_input",
                "validate_input_shape",
                "produce_synthetic_output",
                "persist_dry_run_records",
            ],
            "activation_allowed": False,
            "execution_allowed": False,
            "external_calls_allowed": False,
            "code_loading_allowed": False,
        }


__all__ = ["ModuleMockPlanService"]
