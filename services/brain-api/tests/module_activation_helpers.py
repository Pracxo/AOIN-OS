"""Shared helpers for module activation tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.module_activation import ModuleActivationCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.module_activation import (
    ActivationBlockerService,
    ActivationGateService,
    ActivationPlanService,
    ActivationReviewService,
    ModuleActivationQueryService,
    ModuleActivationRepository,
    ModuleActivationRequestService,
    RuntimeRegistrationPreviewService,
)
from tests.kernel_fakes import AllowPolicy, FakeTelemetry
from tests.module_binding_helpers import binding_request, module_binding_services, slot_request


class DenyPolicy:
    """Always deny module activation tests."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="test_denied",
            constraints=[],
            audit_level="standard",
        )


def module_activation_repository() -> ModuleActivationRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ModuleActivationRepository(engine=engine)


def module_activation_services(policy: object | None = None) -> dict[str, object]:
    repository = module_activation_repository()
    policy_adapter = policy or AllowPolicy()
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    telemetry = FakeTelemetry()
    binding_services = module_binding_services(policy=AllowPolicy(), settings=settings)
    slot = binding_services["slot_service"].create_slot(slot_request())  # type: ignore[attr-defined]
    binding = binding_services["binding_service"].create_binding(  # type: ignore[attr-defined]
        binding_request(slot.module_slot_id)
    )
    blocker_service = ActivationBlockerService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
    )
    return {
        "repository": repository,
        "policy": policy_adapter,
        "settings": settings,
        "telemetry": telemetry,
        "slot": slot,
        "binding": binding,
        "request_service": ModuleActivationRequestService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=settings,
        ),
        "blocker_service": blocker_service,
        "gate_service": ActivationGateService(
            repository,
            policy_adapter,
            module_binding_repository=binding_services["repository"],
            telemetry_service=telemetry,
            settings=settings,
            blocker_service=blocker_service,
        ),
        "review_service": ActivationReviewService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=settings,
        ),
        "plan_service": ActivationPlanService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=settings,
        ),
        "preview_service": RuntimeRegistrationPreviewService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=settings,
        ),
        "query_service": ModuleActivationQueryService(repository, policy_adapter),
    }


def activation_create_request(
    module_slot_id: str,
    capability_binding_id: str | None = None,
    **overrides: object,
) -> ModuleActivationCreateRequest:
    payload = {
        "module_slot_id": module_slot_id,
        "capability_binding_ids": [capability_binding_id] if capability_binding_id else [],
        "owner_scope": ["workspace:main"],
        "risk_level": "medium",
        "metadata": {
            "required_policy_actions": ["module_activation.query.read"],
            "required_settings": ["module_activation_requests_enabled"],
            "required_sandbox_profiles": ["default.metadata_only"],
        },
    }
    payload.update(overrides)
    return ModuleActivationCreateRequest.model_validate(payload)


def create_activation_request() -> tuple[dict[str, object], str]:
    services = module_activation_services()
    slot = services["slot"]
    binding = services["binding"]
    request = services["request_service"].create_request(  # type: ignore[attr-defined]
        activation_create_request(
            slot.module_slot_id,  # type: ignore[union-attr]
            binding.capability_binding_id,  # type: ignore[union-attr]
        )
    )
    return services, request.activation_request_id
