"""Shared helpers for module binding tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.capability_bindings import (
    CapabilityBindingCreateRequest,
    MountPlanCreateRequest,
)
from aion_brain.contracts.module_slots import ModuleSlotCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.module_bindings import (
    BindingConflictService,
    BindingValidator,
    CapabilityBindingService,
    ModuleBindingQueryService,
    ModuleBindingRepository,
    ModuleMountPlanService,
    ModuleSlotService,
    RouteBindingPreviewService,
)
from tests.kernel_fakes import AllowPolicy, FakeTelemetry


class DenyPolicy:
    """Always deny module binding tests."""

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


def module_binding_repository() -> ModuleBindingRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ModuleBindingRepository(engine=engine)


def module_binding_services(
    policy: object | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    repository = module_binding_repository()
    policy_adapter = policy or AllowPolicy()
    resolved_settings = settings or Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
    )
    telemetry = FakeTelemetry()
    conflict_service = BindingConflictService(
        repository,
        policy_adapter,
        settings=resolved_settings,
        telemetry_service=telemetry,
    )
    return {
        "repository": repository,
        "settings": resolved_settings,
        "telemetry": telemetry,
        "slot_service": ModuleSlotService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=resolved_settings,
        ),
        "binding_service": CapabilityBindingService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=resolved_settings,
        ),
        "conflict_service": conflict_service,
        "validator": BindingValidator(
            repository,
            policy_adapter,
            conflict_service=conflict_service,
            telemetry_service=telemetry,
            settings=resolved_settings,
        ),
        "mount_plan_service": ModuleMountPlanService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=resolved_settings,
        ),
        "route_preview_service": RouteBindingPreviewService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=resolved_settings,
        ),
        "query_service": ModuleBindingQueryService(repository, policy_adapter),
    }


def slot_request(**overrides: object) -> ModuleSlotCreateRequest:
    payload = {
        "slot_key": "test.echo",
        "name": "Echo Slot",
        "description": "Generic metadata slot.",
        "version": "0.1.0",
        "slot_type": "module",
        "owner_scope": ["workspace:main"],
        "declared_capability_refs": ["test.echo.respond"],
        "contract_refs": ["aion.contract.generic"],
        "policy_action_refs": ["module_binding.query"],
        "setting_refs": ["module_slots_enabled"],
    }
    payload.update(overrides)
    return ModuleSlotCreateRequest.model_validate(payload)


def binding_request(module_slot_id: str, **overrides: object) -> CapabilityBindingCreateRequest:
    payload = {
        "module_slot_id": module_slot_id,
        "capability_key": "test.echo.respond",
        "capability_type": "generic",
        "binding_type": "declared",
        "route_key": "test.echo.respond",
        "target_runtime": "metadata_only",
        "risk_level": "medium",
        "allowed_modes": ["dry_run"],
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "required_policy_actions": ["module_binding.query"],
        "required_settings": ["module_slots_enabled"],
        "required_contracts": [],
        "requires_approval": True,
        "requires_sandbox": True,
        "dry_run_supported": True,
        "controlled_supported": False,
    }
    payload.update(overrides)
    return CapabilityBindingCreateRequest.model_validate(payload)


def create_slot_and_binding() -> tuple[dict[str, object], str, str]:
    services = module_binding_services()
    slot = services["slot_service"].create_slot(slot_request())  # type: ignore[union-attr]
    binding = services["binding_service"].create_binding(  # type: ignore[union-attr]
        binding_request(slot.module_slot_id)
    )
    return services, slot.module_slot_id, binding.capability_binding_id


def mount_plan_request(module_slot_id: str) -> MountPlanCreateRequest:
    return MountPlanCreateRequest(module_slot_id=module_slot_id, scope=["workspace:main"])
