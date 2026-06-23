"""Non-executable activation plan service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.module_activation import ActivationMutationRequest, ActivationPlan
from aion_brain.module_activation.policy import authorize_module_activation_action
from aion_brain.module_activation.repository import ModuleActivationRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry

_PLAN_STEPS = [
    "validate_request_metadata",
    "run_activation_gate",
    "verify_policy_actions",
    "verify_runtime_settings",
    "verify_sandbox_profile",
    "generate_registration_preview",
    "require_operator_review",
    "stop_before_activation",
]


class ActivationPlanService:
    """Create and query plans that stop before activation."""

    def __init__(
        self,
        repository: ModuleActivationRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_plan(
        self,
        activation_request_id: str,
        scope: list[str],
        *,
        created_by: str | None = None,
    ) -> ActivationPlan:
        if not self._settings.module_activation_plans_enabled:
            raise RuntimeError("module_activation_plans_disabled")
        request = self._repository.get_request(activation_request_id)
        if request is None or not _in_scope(request.owner_scope, scope):
            raise AIONNotFoundException("module_activation_request_not_found")
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.plan.create",
            scope,
            actor_id=created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="module_activation_plan",
            resource_id=activation_request_id,
            risk_level=request.risk_level,
            context={"executable": False, "execution_allowed": False},
        )
        blockers = self._repository.list_blockers(
            activation_request_id=activation_request_id,
            status="open",
            limit=100,
        )
        plan = ActivationPlan(
            activation_plan_id=f"activation-plan-{uuid4().hex}",
            trace_id=request.trace_id,
            activation_request_id=request.activation_request_id,
            module_slot_id=request.module_slot_id,
            status="blocked" if blockers else "created",
            plan_type="future_activation",
            owner_scope=request.owner_scope,
            steps=[
                {
                    "step_id": step,
                    "action_type": _action_for_step(step),
                    "status": "blocked" if step == "stop_before_activation" else "planned",
                    "metadata_only": True,
                    "execution_allowed": False,
                }
                for step in _PLAN_STEPS
            ],
            required_contracts=[],
            required_policy_actions=request.required_policy_actions,
            required_settings=request.required_settings,
            required_sandbox_profiles=request.required_sandbox_profiles,
            required_approvals=request.required_approvals,
            rollback_plan=[
                {
                    "step_id": "rollback_preview_only",
                    "status": "not_executable",
                    "runtime_mutation_allowed": False,
                }
            ],
            blocked=True,
            blockers=[blocker.model_dump(mode="json") for blocker in blockers],
            warnings=[
                {
                    "message": "Activation plan is metadata-only in AION-083.",
                    "execution_allowed": False,
                }
            ],
            executable=False,
            execution_allowed=False,
            metadata={"metadata_only": True, "no_runtime_mutation": True},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_plan(plan)
        self._repository.save_request(
            request.model_copy(
                update={
                    "activation_plan_id": saved.activation_plan_id,
                    "activation_allowed": False,
                    "execution_allowed": False,
                }
            )
        )
        self._emit("module_activation_plan_created", saved)
        return saved

    def get_plan(self, activation_plan_id: str, scope: list[str]) -> ActivationPlan:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.plan.read",
            scope,
            resource_type="module_activation_plan",
            resource_id=activation_plan_id,
        )
        plan = self._repository.get_plan(activation_plan_id)
        if plan is None or not _in_scope(plan.owner_scope, scope):
            raise AIONNotFoundException("module_activation_plan_not_found")
        return plan

    def list_plans(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> list[ActivationPlan]:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.plan.read",
            scope,
            resource_type="module_activation_plan",
        )
        return [
            item
            for item in self._repository.list_plans(
                status=status,
                module_slot_id=module_slot_id,
                limit=limit,
            )
            if _in_scope(item.owner_scope, scope)
        ]

    def archive_plan(
        self,
        activation_plan_id: str,
        scope: list[str],
        request: ActivationMutationRequest,
    ) -> ActivationPlan:
        plan = self.get_plan(activation_plan_id, scope)
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.plan.update",
            scope,
            actor_id=request.actor_id,
            resource_type="module_activation_plan",
            resource_id=activation_plan_id,
            context={"reason": request.reason, "execution_allowed": False},
        )
        return self._repository.save_plan(
            plan.model_copy(
                update={
                    "status": "archived",
                    "archived_at": datetime.now(UTC),
                    "metadata": {**plan.metadata, "archive_reason": request.reason},
                }
            )
        )

    def _emit(self, event_type: str, plan: ActivationPlan) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="module_activation_plan",
            node_id=plan.activation_plan_id,
            intensity=0.6,
            scope=plan.owner_scope,
            payload={"status": plan.status, "executable": False},
        )


def _action_for_step(step: str) -> str:
    return {
        "validate_request_metadata": "module_activation.request.read",
        "run_activation_gate": "module_activation.gate.run",
        "verify_policy_actions": "policy.coverage.read",
        "verify_runtime_settings": "runtime_config.status.read",
        "verify_sandbox_profile": "sandbox.profile.read",
        "generate_registration_preview": "runtime.registration.preview.create",
        "require_operator_review": "module_activation.review.create",
        "stop_before_activation": "module_activation.gate.read",
    }[step]


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(requested_scope))


__all__ = ["ActivationPlanService"]
