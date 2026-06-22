"""Module binding service tests."""

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.capability_bindings import (
    BindingMutationRequest,
    BindingValidationRequest,
    ModuleBindingQuery,
    RoutePreviewCreateRequest,
)
from tests.module_binding_helpers import (
    DenyPolicy,
    binding_request,
    create_slot_and_binding,
    module_binding_services,
    mount_plan_request,
    slot_request,
)


def test_module_slot_service_creates_and_archives_slot() -> None:
    services = module_binding_services()
    slot_service = services["slot_service"]

    slot = slot_service.create_slot(slot_request())  # type: ignore[attr-defined]
    archived = slot_service.archive_slot(  # type: ignore[attr-defined]
        slot.module_slot_id,
        ["workspace:main"],
        BindingMutationRequest(reason="done"),
    )

    assert slot.status == "proposed"
    assert archived.status == "archived"


def test_policy_deny_blocks_slot_create() -> None:
    services = module_binding_services(policy=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        services["slot_service"].create_slot(slot_request())  # type: ignore[attr-defined]


def test_capability_binding_service_creates_and_disables_binding() -> None:
    services = module_binding_services()
    slot = services["slot_service"].create_slot(slot_request())  # type: ignore[attr-defined]
    binding = services["binding_service"].create_binding(  # type: ignore[attr-defined]
        binding_request(slot.module_slot_id)
    )

    disabled = services["binding_service"].disable_binding(  # type: ignore[attr-defined]
        binding.capability_binding_id,
        ["workspace:main"],
        BindingMutationRequest(reason="not needed"),
    )

    assert binding.status == "proposed"
    assert disabled.status == "disabled"


def test_conflict_service_detects_duplicate_capability_key() -> None:
    services = module_binding_services()
    slot = services["slot_service"].create_slot(slot_request())  # type: ignore[attr-defined]
    services["binding_service"].create_binding(binding_request(slot.module_slot_id))  # type: ignore[attr-defined]
    services["binding_service"].create_binding(  # type: ignore[attr-defined]
        binding_request(
            slot.module_slot_id,
            capability_binding_id="capability-binding-two",
            capability_key="test.echo.respond",
        )
    )

    conflicts = services["conflict_service"].detect_conflicts(  # type: ignore[attr-defined]
        ["workspace:main"],
        module_slot_id=slot.module_slot_id,
    )

    assert any(conflict.conflict_type == "duplicate_capability_key" for conflict in conflicts)


def test_binding_validator_persists_run_and_controlled_conflicts() -> None:
    services, slot_id, binding_id = create_slot_and_binding()

    run = services["validator"].validate(  # type: ignore[attr-defined]
        BindingValidationRequest(
            mode="controlled",
            owner_scope=["workspace:main"],
            module_slot_id=slot_id,
            capability_binding_ids=[binding_id],
        )
    )
    conflicts = services["repository"].list_conflicts(limit=100)  # type: ignore[attr-defined]

    assert run.binding_validation_id
    assert run.result["source_records_mutated"] is False
    assert conflicts


def test_mount_plan_is_non_executable() -> None:
    services, slot_id, _binding_id = create_slot_and_binding()

    plan = services["mount_plan_service"].create_plan(mount_plan_request(slot_id))  # type: ignore[attr-defined]

    assert plan.executable is False
    assert plan.execution_allowed is False
    assert plan.blocked is True


def test_route_preview_never_registers() -> None:
    services, _slot_id, binding_id = create_slot_and_binding()

    preview = services["route_preview_service"].create_preview(  # type: ignore[attr-defined]
        RoutePreviewCreateRequest(
            capability_binding_id=binding_id,
            scope=["workspace:main"],
        )
    )

    assert preview.registration_allowed is False
    assert preview.status == "blocked"


def test_module_binding_query_returns_aggregate_records() -> None:
    services, slot_id, binding_id = create_slot_and_binding()
    services["mount_plan_service"].create_plan(mount_plan_request(slot_id))  # type: ignore[attr-defined]
    services["validator"].validate(  # type: ignore[attr-defined]
        BindingValidationRequest(
            owner_scope=["workspace:main"],
            module_slot_id=slot_id,
            capability_binding_ids=[binding_id],
        )
    )

    result = services["query_service"].query(  # type: ignore[attr-defined]
        ModuleBindingQuery(scope=["workspace:main"], query="echo")
    )

    assert result.module_slots
    assert result.capability_bindings
    assert result.total_count >= 2
