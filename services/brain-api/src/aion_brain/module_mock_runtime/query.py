"""Module mock runtime query service."""

from __future__ import annotations

from aion_brain.contracts.module_mock_runtime import ModuleMockQuery, ModuleMockQueryResult
from aion_brain.module_mock_runtime.policy import authorize_module_mock_action
from aion_brain.module_mock_runtime.repository import ModuleMockRuntimeRepository


class ModuleMockQueryService:
    """Aggregate module mock runtime metadata."""

    def __init__(self, repository: ModuleMockRuntimeRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, request: ModuleMockQuery) -> ModuleMockQueryResult:
        """Return aggregate dry-run records."""

        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.query",
            request.scope,
            resource_type="module_mock_runtime",
            risk_level="low",
            context=request.model_dump(mode="json"),
        )
        profiles = self._repository.list_profiles(
            status=request.status if request.status in {"active", "disabled"} else None,
            limit=request.limit,
        )
        requests = self._repository.list_requests(
            mock_profile_id=request.mock_profile_id,
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            limit=request.limit,
        )
        runs = self._repository.list_runs(
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            status=request.status,
            limit=request.limit,
        )
        outputs = self._repository.list_outputs(
            capability_binding_id=request.capability_binding_id,
            limit=request.limit,
        )
        findings = self._repository.list_findings(
            capability_binding_id=request.capability_binding_id,
            status=request.status,
            limit=request.limit,
        )
        return ModuleMockQueryResult(
            profiles=profiles,
            requests=requests,
            runs=runs,
            outputs=outputs,
            findings=findings,
            total_count=len(profiles) + len(requests) + len(runs) + len(outputs) + len(findings),
            constraints=["metadata_only", "dry_run_only", "no_execution"],
            metadata={
                "activation_allowed": False,
                "execution_allowed": False,
                "external_calls_made": False,
                "code_loaded": False,
            },
        )


__all__ = ["ModuleMockQueryService"]
