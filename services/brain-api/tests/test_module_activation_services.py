"""Module activation service tests."""

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.module_activation import (
    ActivationReviewRequest,
    ModuleActivationQuery,
)
from tests.module_activation_helpers import (
    DenyPolicy,
    activation_create_request,
    create_activation_request,
    module_activation_services,
)


def test_activation_request_service_creates_metadata_only_request() -> None:
    services = module_activation_services()
    slot = services["slot"]
    binding = services["binding"]

    request = services["request_service"].create_request(  # type: ignore[attr-defined]
        activation_create_request(
            slot.module_slot_id,  # type: ignore[union-attr]
            binding.capability_binding_id,  # type: ignore[union-attr]
        )
    )

    assert request.activation_allowed is False
    assert request.execution_allowed is False
    assert request.status == "requested"


def test_policy_deny_blocks_activation_request_create() -> None:
    services = module_activation_services(policy=DenyPolicy())
    slot = services["slot"]

    with pytest.raises(AIONPolicyDeniedException):
        services["request_service"].create_request(  # type: ignore[attr-defined]
            activation_create_request(slot.module_slot_id)  # type: ignore[union-attr]
        )


def test_activation_gate_creates_blockers_and_never_allows_activation() -> None:
    services, activation_request_id = create_activation_request()

    run = services["gate_service"].run_gate(  # type: ignore[attr-defined]
        activation_request_id,
        ["workspace:main"],
    )

    blocker_types = {blocker.blocker_type for blocker in run.blockers}
    assert run.status == "blocked"
    assert run.activation_allowed is False
    assert "activation_disabled" in blocker_types
    assert "dynamic_route_registration_disabled" in blocker_types


def test_activation_plan_and_registration_preview_are_non_executable() -> None:
    services, activation_request_id = create_activation_request()
    services["gate_service"].run_gate(activation_request_id, ["workspace:main"])  # type: ignore[attr-defined]

    plan = services["plan_service"].create_plan(  # type: ignore[attr-defined]
        activation_request_id,
        ["workspace:main"],
    )
    preview = services["preview_service"].create_preview(  # type: ignore[attr-defined]
        activation_request_id,
        ["workspace:main"],
    )

    assert plan.executable is False
    assert plan.execution_allowed is False
    assert preview.registration_allowed is False
    assert preview.would_register is False


def test_activation_review_and_query_records_metadata() -> None:
    services, activation_request_id = create_activation_request()

    review = services["review_service"].review(  # type: ignore[attr-defined]
        ActivationReviewRequest(
            activation_request_id=activation_request_id,
            decision="approve_for_future_activation",
            reason="Reviewed for a future controlled task.",
            approval_present=True,
        ),
        ["workspace:main"],
    )
    result = services["query_service"].query(  # type: ignore[attr-defined]
        ModuleActivationQuery(scope=["workspace:main"], activation_request_id=activation_request_id)
    )

    assert review.status == "approved"
    assert result.activation_requests
    assert result.total_count >= 2
