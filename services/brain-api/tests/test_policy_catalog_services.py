"""Policy catalog service tests."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.policy_catalog import (
    PermissionCatalogEntry,
    PolicyActionCatalogEntry,
    PolicyBundleExportRequest,
    PolicySimulationRequest,
    PolicyTestCase,
    PolicyTestRunRequest,
    RoleTemplate,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.policy_catalog.bundles import PolicyBundleService
from aion_brain.policy_catalog.catalog import PolicyCatalogService
from aion_brain.policy_catalog.coverage import PolicyCoverageAnalyzer
from aion_brain.policy_catalog.permissions import PermissionMatrixService
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.simulation import PolicySimulationService
from aion_brain.policy_catalog.test_harness import PolicyTestHarness


class FakePolicyAdapter:
    """Configurable policy fake."""

    def __init__(self, deny_actions: set[str] | None = None) -> None:
        self.deny_actions = deny_actions or set()
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type not in self.deny_actions
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="test_allowed" if allow else "test_denied",
            constraints=[] if allow else ["policy_denied"],
            audit_level="standard",
        )


class FakeTelemetry:
    """Collect visual telemetry."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)

    def save_visual_telemetry(self, trace_id: str, events: list[object]) -> None:
        self.events.extend(events)


def repository() -> PolicyCatalogRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return PolicyCatalogRepository(engine=engine)


def test_catalog_seed_defaults_dry_run_does_not_persist() -> None:
    repo = repository()
    service = PolicyCatalogService(
        repository=repo,
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=FakeTelemetry(),
    )

    result = service.seed_defaults(dry_run=True)

    assert result["dry_run"] is True
    assert repo.list_actions(status=None) == []


def test_catalog_create_and_disable_action() -> None:
    repo = repository()
    telemetry = FakeTelemetry()
    service = PolicyCatalogService(
        repository=repo,
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=telemetry,
    )

    service.create_action(action_entry("policy.catalog.read"))
    disabled = service.disable_action("policy.catalog.read", "actor-1", "retired")

    assert disabled.status == "disabled"
    assert telemetry.events


def test_permission_matrix_seeds_permissions_and_roles() -> None:
    repo = repository()
    service = PermissionMatrixService(
        repository=repo,
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=FakeTelemetry(),
    )

    result = service.seed_default_roles(dry_run=False)

    assert result["created"] is True
    assert repo.list_permissions(status=None)
    assert {role.role_name for role in repo.list_role_templates(status=None)} >= {"owner", "viewer"}


def test_policy_deny_blocks_catalog_write() -> None:
    service = PolicyCatalogService(
        repository=repository(),
        policy_adapter=FakePolicyAdapter({"policy.catalog.create"}),
        telemetry_service=FakeTelemetry(),
    )

    try:
        service.create_action(action_entry("policy.catalog.read"))
    except PermissionError as exc:
        assert "policy_denied" in str(exc)
    else:
        raise AssertionError("policy denial should block catalog write")


def test_simulation_records_decision_without_executing_target() -> None:
    repo = repository()
    policy = FakePolicyAdapter({"memory.write"})
    service = PolicySimulationService(
        repository=repo,
        policy_adapter=policy,
        telemetry_service=FakeTelemetry(),
    )

    result = service.simulate(
        PolicySimulationRequest(
            action_type="memory.write",
            resource_type="memory_record",
            risk_level="medium",
            requested_permissions=["memory.write"],
            security_scope=["workspace:main"],
        ),
        actor_context(),
    )

    assert result.decision.allow is False
    assert result.explanation["target_action_executed"] is False
    assert repo.get_simulation(result.simulation_id) is not None


def test_policy_test_harness_runs_cases() -> None:
    repo = repository()
    policy = FakePolicyAdapter()
    simulation_service = PolicySimulationService(
        repository=repo,
        policy_adapter=policy,
        telemetry_service=FakeTelemetry(),
    )
    harness = PolicyTestHarness(
        repository=repo,
        policy_adapter=policy,
        simulation_service=simulation_service,
        telemetry_service=FakeTelemetry(),
    )
    test_case = harness.create_test_case(policy_test_case("case-1"))

    run = harness.run_tests(
        PolicyTestRunRequest(test_case_ids=[test_case.policy_test_case_id]),
        actor_context(),
    )

    assert run.status == "passed"
    assert run.passed_count == 1


def test_coverage_detects_domain_specific_catalog_entries() -> None:
    repo = repository()
    repo.save_action(
        PolicyActionCatalogEntry(
            policy_action_id="action-bad",
            action_type="memory.retrieve",
            category="memory",
            resource_type="memory_record",
            default_risk_level="low",
            required_permission="memory.read",
            description="Generic action.",
            metadata={"original": "safe"},
        )
    )
    repo.save_permission(
        PermissionCatalogEntry(
            permission_id="permission-bad",
            permission="memory.read",
            category="memory",
            resource_type="memory_record",
            action_pattern="memory.retrieve",
            description="Generic permission.",
        )
    )
    repo.save_role_template(role_template("viewer", ["memory.read"]))
    analyzer = PolicyCoverageAnalyzer(
        repository=repo,
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=FakeTelemetry(),
    )

    report = analyzer.generate()

    assert report.status in {"warning", "passed"}
    assert report.permission_count == 1


def test_bundle_export_hash_ignores_generated_timestamp() -> None:
    repo = repository()
    repo.save_action(action_entry("policy.catalog.read"))
    service = PolicyBundleService(
        repository=repo,
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=FakeTelemetry(),
        version="0.1.0",
    )
    request = PolicyBundleExportRequest(bundle_type="full", created_by="tester")

    first = service.export_bundle(request)
    second = service.export_bundle(request)

    assert first.content_hash == second.content_hash


def action_entry(action_type: str) -> PolicyActionCatalogEntry:
    return PolicyActionCatalogEntry(
        policy_action_id=f"action-{action_type.replace('.', '-')}",
        action_type=action_type,
        category="policy",
        resource_type="policy_catalog",
        default_risk_level="low",
        required_permission="policy.read",
        description="Generic action.",
    )


def role_template(role_name: str, permissions: list[str]) -> RoleTemplate:
    return RoleTemplate(
        role_template_id=f"role-template-{role_name}",
        role_name=role_name,
        description="Role template.",
        permissions=permissions,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def policy_test_case(case_id: str) -> PolicyTestCase:
    return PolicyTestCase(
        policy_test_case_id=case_id,
        name="low risk read",
        description="Low-risk read is allowed.",
        action_type="memory.retrieve",
        resource_type="memory_record",
        input={
            "action_type": "memory.retrieve",
            "resource_type": "memory_record",
            "risk_level": "low",
            "requested_permissions": ["memory.retrieve"],
            "security_scope": ["workspace:main"],
        },
        expected={"allow": True},
    )


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["policy.simulate", "policy.test.run"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
