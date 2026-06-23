"""Query service for module activation gate records."""

from __future__ import annotations

from aion_brain.contracts.module_activation import (
    ModuleActivationQuery,
    ModuleActivationQueryResult,
)
from aion_brain.module_activation.policy import authorize_module_activation_action
from aion_brain.module_activation.repository import ModuleActivationRepository


class ModuleActivationQueryService:
    """Aggregate metadata-only activation gate records."""

    def __init__(
        self,
        repository: ModuleActivationRepository,
        policy_adapter: object,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, query: ModuleActivationQuery) -> ModuleActivationQueryResult:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.query.read",
            query.scope,
            resource_type="module_activation_query",
            resource_id=query.activation_request_id,
        )
        requests = [
            item
            for item in self._repository.list_requests(
                status=query.status,
                module_slot_id=query.module_slot_id,
                extension_package_id=query.extension_package_id,
                risk_level=query.risk_level,
                include_deleted=query.include_deleted,
                limit=query.limit,
            )
            if _in_scope(item.owner_scope, query.scope)
            and (
                query.activation_request_id is None
                or item.activation_request_id == query.activation_request_id
            )
        ]
        request_ids = {item.activation_request_id for item in requests}
        gate_runs = [
            item
            for item in self._repository.list_gate_runs(limit=query.limit)
            if item.activation_request_id in request_ids
        ]
        blockers = [
            item
            for item in self._repository.list_blockers(limit=query.limit)
            if item.activation_request_id in request_ids
        ]
        reviews = [
            item
            for item in self._repository.list_reviews(limit=query.limit)
            if item.activation_request_id in request_ids
        ]
        plans = [
            item
            for item in self._repository.list_plans(limit=query.limit)
            if item.activation_request_id in request_ids
        ]
        previews = [
            item
            for item in self._repository.list_registration_previews(limit=query.limit)
            if item.activation_request_id in request_ids
        ]
        return ModuleActivationQueryResult(
            activation_requests=requests,
            gate_runs=gate_runs,
            blockers=blockers,
            reviews=reviews,
            plans=plans,
            registration_previews=previews,
            total_count=sum(
                [
                    len(requests),
                    len(gate_runs),
                    len(blockers),
                    len(reviews),
                    len(plans),
                    len(previews),
                ]
            ),
            constraints=[
                "metadata_only",
                "activation_allowed_false",
                "execution_allowed_false",
                "runtime_registration_allowed_false",
            ],
            metadata={"module_activation_execution_enabled": False},
        )


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(requested_scope))


__all__ = ["ModuleActivationQueryService"]
