"""Policy catalog repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.policy_catalog import (
    PermissionCatalogEntry,
    PolicyActionCatalogEntry,
    PolicyBundleRecord,
    PolicySimulationRequest,
    PolicySimulationResult,
    PolicyTestCase,
    PolicyTestRun,
    RoleTemplate,
)
from aion_brain.policy_catalog.repository import PolicyCatalogRepository


def repository() -> PolicyCatalogRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return PolicyCatalogRepository(engine=engine)


def test_repository_persists_action_permission_and_role() -> None:
    repo = repository()
    repo.save_action(action_entry("memory.retrieve"))
    repo.save_permission(permission_entry("memory.read", "memory.retrieve"))
    repo.save_role_template(role_template("viewer", ["memory.read"]))

    assert repo.get_action("memory.retrieve") is not None
    assert repo.list_permissions()[0].permission == "memory.read"
    assert repo.list_role_templates()[0].role_name == "viewer"


def test_repository_persists_simulations_tests_runs_and_bundles() -> None:
    repo = repository()
    decision = decision_for("memory.retrieve", allow=True)
    request = PolicySimulationRequest(
        simulation_id="simulation-1",
        action_type="memory.retrieve",
        resource_type="memory_record",
        risk_level="low",
        requested_permissions=["memory.retrieve"],
        security_scope=["workspace:main"],
    )
    simulation = PolicySimulationResult(
        simulation_id="simulation-1",
        request=request,
        decision=decision,
        explanation={"target_action_executed": False},
        created_at=decision_time(),
    )
    test_case = policy_test_case("case-1")
    test_run = PolicyTestRun(
        policy_test_run_id="run-1",
        status="passed",
        total_count=1,
        passed_count=1,
        failed_count=0,
        warning_count=0,
        results=[{"policy_test_case_id": "case-1", "passed": True}],
        report={},
        created_by="tester",
        created_at=decision_time(),
        completed_at=decision_time(),
    )
    bundle = PolicyBundleRecord(
        policy_bundle_id="bundle-1",
        bundle_type="full",
        version="0.1.0",
        content_hash="abc",
        content={"action_catalog": []},
        status="exported",
        created_by="tester",
        created_at=decision_time(),
    )

    repo.save_simulation(simulation)
    repo.save_test_case(test_case)
    repo.save_test_run(test_run)
    repo.save_bundle(bundle)

    assert repo.get_simulation("simulation-1") is not None
    assert repo.list_test_cases()[0].policy_test_case_id == "case-1"
    assert repo.get_bundle("bundle-1") is not None


def action_entry(action_type: str) -> PolicyActionCatalogEntry:
    return PolicyActionCatalogEntry(
        policy_action_id=f"action-{action_type.replace('.', '-')}",
        action_type=action_type,
        category=action_type.split(".", 1)[0],
        resource_type="policy_resource",
        default_risk_level="low",
        required_permission="memory.read",
        description="Generic action.",
    )


def permission_entry(permission: str, action_pattern: str) -> PermissionCatalogEntry:
    return PermissionCatalogEntry(
        permission_id=f"permission-{permission.replace('.', '-')}",
        permission=permission,
        category=permission.split(".", 1)[0],
        resource_type="policy_resource",
        action_pattern=action_pattern,
        description="Generic permission.",
    )


def role_template(role_name: str, permissions: list[str]) -> RoleTemplate:
    return RoleTemplate(
        role_template_id=f"role-template-{role_name}",
        role_name=role_name,
        description="Role template.",
        permissions=permissions,
    )


def policy_test_case(case_id: str) -> PolicyTestCase:
    return PolicyTestCase(
        policy_test_case_id=case_id,
        name="allows memory retrieval",
        description="Low-risk generic read.",
        action_type="memory.retrieve",
        resource_type="memory_record",
        input={
            "risk_level": "low",
            "requested_permissions": ["memory.retrieve"],
            "security_scope": ["workspace:main"],
        },
        expected={"allow": True},
    )


def decision_for(action_type: str, *, allow: bool) -> PolicyDecision:
    return PolicyDecision(
        decision_id=f"decision-{action_type}",
        trace_id="trace-1",
        allow=allow,
        approval_required=False,
        reason="test_allowed" if allow else "test_denied",
        constraints=[],
        audit_level="standard",
    )


def decision_time():
    from datetime import UTC, datetime

    return datetime.now(UTC)
