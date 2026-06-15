"""Policy catalog contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.policy_catalog import (
    OPAStatus,
    PermissionCatalogEntry,
    PolicyActionCatalogEntry,
    PolicySimulationRequest,
    PolicyTestCase,
    RoleTemplate,
)


def test_policy_action_contract_accepts_generic_action() -> None:
    entry = PolicyActionCatalogEntry(
        policy_action_id="action-1",
        action_type="memory.retrieve",
        category="memory",
        resource_type="memory_record",
        default_risk_level="low",
        required_permission="memory.read",
        description="Retrieve memory metadata.",
    )

    assert entry.action_type == "memory.retrieve"


def test_policy_action_rejects_domain_specific_prefix() -> None:
    with pytest.raises(ValidationError):
        PolicyActionCatalogEntry(
            policy_action_id="action-1",
            action_type="finance.trade",
            category="policy",
            resource_type="policy_action",
            default_risk_level="high",
            required_permission="finance.trade",
            description="Not allowed in Brain core.",
        )


def test_permission_and_role_templates_validate_generic_permissions() -> None:
    permission = PermissionCatalogEntry(
        permission_id="permission-1",
        permission="policy.read",
        category="policy",
        resource_type="policy_catalog",
        action_pattern="policy.catalog.read",
        description="Read policy catalog.",
    )
    role = RoleTemplate(
        role_template_id="role-template-viewer",
        role_name="viewer",
        description="Read-only role.",
        permissions=[permission.permission],
    )

    assert role.permissions == ["policy.read"]


def test_simulation_request_requires_scope() -> None:
    with pytest.raises(ValidationError):
        PolicySimulationRequest(
            action_type="memory.retrieve",
            resource_type="memory_record",
            security_scope=[],
        )


def test_policy_test_case_expected_must_assert_decision() -> None:
    with pytest.raises(ValidationError):
        PolicyTestCase(
            policy_test_case_id="case-1",
            name="invalid",
            description="Missing decision expectation.",
            action_type="memory.retrieve",
            resource_type="memory_record",
            input={"security_scope": ["workspace:main"]},
            expected={"reason_contains": "allowed"},
        )


def test_opa_status_contract_is_secret_free_and_typed() -> None:
    status = OPAStatus(
        available=False,
        url="http://opa:8181",
        policy_loaded=False,
        decision_path="/v1/data/aion/brain/decision",
        reason="policy_engine_unavailable",
        checked_at=datetime.now(UTC),
    )

    assert status.available is False
