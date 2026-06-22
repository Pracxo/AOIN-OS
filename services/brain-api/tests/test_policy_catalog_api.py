"""Policy catalog API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.policy_catalog import (
    get_kernel_container,
    get_permission_matrix_service,
    get_policy_bundle_service,
    get_policy_catalog_service,
    get_policy_coverage_analyzer,
    get_policy_simulation_service,
    get_policy_test_harness,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.policy_catalog import (
    OPAStatus,
    PermissionCatalogEntry,
    PolicyActionCatalogEntry,
    PolicyBundleRecord,
    PolicyCoverageReport,
    PolicySimulationRequest,
    PolicySimulationResult,
    PolicyTestCase,
    PolicyTestRun,
    RoleTemplate,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeCatalogService:
    def create_action(self, entry: PolicyActionCatalogEntry) -> PolicyActionCatalogEntry:
        return entry

    def list_actions(self, category: str | None = None, status: str | None = None):
        return [action_entry("policy.catalog.read")]

    def get_action(self, action_type: str):
        return action_entry(action_type)

    def disable_action(self, action_type: str, actor_id: str, reason: str):
        return action_entry(action_type).model_copy(update={"status": "disabled"})

    def seed_defaults(self, dry_run: bool = True):
        return {"dry_run": dry_run, "action_count": 1}


class FakePermissionService:
    def create_permission(self, entry: PermissionCatalogEntry) -> PermissionCatalogEntry:
        return entry

    def list_permissions(self, category: str | None = None, status: str | None = None):
        return [permission_entry("policy.read", "policy.catalog.read")]

    def create_role_template(self, entry: RoleTemplate) -> RoleTemplate:
        return entry

    def list_role_templates(self, status: str | None = None):
        return [role_template("viewer", ["policy.read"])]

    def seed_default_roles(self, dry_run: bool = True):
        return {"dry_run": dry_run, "role_template_count": 1}


class FakeSimulationService:
    def simulate(
        self,
        request: PolicySimulationRequest,
        actor_context: ActorContext | None = None,
    ) -> PolicySimulationResult:
        return PolicySimulationResult(
            simulation_id=request.simulation_id or "simulation-1",
            request=request,
            decision=decision_for(request.action_type, allow=True),
            explanation={"target_action_executed": False},
            created_at=datetime.now(UTC),
        )


class FakeTestHarness:
    def create_test_case(self, test_case: PolicyTestCase) -> PolicyTestCase:
        return test_case

    def list_test_cases(self, status: str | None = None, tags: list[str] | None = None):
        return [policy_test_case("case-1")]

    def run_tests(self, request, actor_context):
        return PolicyTestRun(
            policy_test_run_id="run-1",
            status="passed",
            total_count=1,
            passed_count=1,
            failed_count=0,
            warning_count=0,
            results=[{"policy_test_case_id": "case-1", "passed": True}],
            report={},
            created_by="tester",
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )


class FakeCoverageAnalyzer:
    def generate(self) -> PolicyCoverageReport:
        return PolicyCoverageReport(
            report_id="coverage-1",
            action_count=1,
            catalogued_action_count=1,
            uncatalogued_actions=[],
            permission_count=1,
            role_template_count=1,
            test_case_count=1,
            untested_actions=[],
            duplicate_permissions=[],
            domain_specific_violations=[],
            status="passed",
            generated_at=datetime.now(UTC),
        )


class FakeBundleService:
    def export_bundle(self, request):
        return bundle_record("bundle-1")

    def get_bundle(self, policy_bundle_id: str):
        return bundle_record(policy_bundle_id)

    def list_bundles(self, bundle_type: str | None = None):
        return [bundle_record("bundle-1")]


class FakePolicyAdapter:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return decision_for(request.action_type, allow=True)

    def status(self) -> OPAStatus:
        return OPAStatus(
            available=True,
            url="http://opa:8181",
            policy_loaded=True,
            decision_path="/v1/data/aion/brain/decision",
            reason=None,
            checked_at=datetime.now(UTC),
        )


class FakeContainer:
    policy_adapter = FakePolicyAdapter()
    settings = type("Settings", (), {"opa_url": "http://opa:8181"})()


def test_policy_catalog_api_routes_work() -> None:
    app.dependency_overrides[get_policy_catalog_service] = lambda: FakeCatalogService()
    app.dependency_overrides[get_permission_matrix_service] = lambda: FakePermissionService()
    app.dependency_overrides[get_policy_simulation_service] = lambda: FakeSimulationService()
    app.dependency_overrides[get_policy_test_harness] = lambda: FakeTestHarness()
    app.dependency_overrides[get_policy_coverage_analyzer] = lambda: FakeCoverageAnalyzer()
    app.dependency_overrides[get_policy_bundle_service] = lambda: FakeBundleService()
    app.dependency_overrides[get_kernel_container] = lambda: FakeContainer()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        action = client.post("/brain/policy-catalog/actions", json=action_payload())
        actions = client.get("/brain/policy-catalog/actions")
        action_get = client.get("/brain/policy-catalog/actions/policy.catalog.read")
        disable = client.post(
            "/brain/policy-catalog/actions/policy.catalog.read/disable",
            json={"reason": "retired"},
        )
        seed = client.post("/brain/policy-catalog/seed-defaults", json={"dry_run": True})
        permission = client.post(
            "/brain/policy-catalog/permissions",
            json=permission_payload(),
        )
        permissions = client.get("/brain/policy-catalog/permissions")
        role = client.post("/brain/policy-catalog/roles", json=role_payload())
        roles = client.get("/brain/policy-catalog/roles")
        role_seed = client.post("/brain/policy-catalog/roles/seed-defaults", json={"dry_run": True})
        simulation = client.post("/brain/policy/simulate", json=simulation_payload())
        test_case = client.post("/brain/policy/tests", json=policy_test_payload())
        tests = client.get("/brain/policy/tests")
        test_run = client.post("/brain/policy/tests/run", json={"dry_run": True})
        coverage = client.get("/brain/policy/coverage")
        bundle = client.post("/brain/policy/bundles/export", json={"bundle_type": "full"})
        bundle_get = client.get("/brain/policy/bundles/bundle-1")
        bundles = client.get("/brain/policy/bundles")
        opa = client.get("/brain/policy/opa/status")
    finally:
        app.dependency_overrides.clear()

    responses = [
        action,
        actions,
        action_get,
        disable,
        seed,
        permission,
        permissions,
        role,
        roles,
        role_seed,
        simulation,
        test_case,
        tests,
        test_run,
        coverage,
        bundle,
        bundle_get,
        bundles,
        opa,
    ]
    assert all(response.status_code == 200 for response in responses)
    assert simulation.json()["explanation"]["target_action_executed"] is False
    assert opa.json()["available"] is True


def action_entry(action_type: str) -> PolicyActionCatalogEntry:
    return PolicyActionCatalogEntry(**action_payload(action_type))


def action_payload(action_type: str = "policy.catalog.read") -> dict[str, object]:
    return {
        "policy_action_id": f"action-{action_type.replace('.', '-')}",
        "action_type": action_type,
        "category": "policy",
        "resource_type": "policy_catalog",
        "default_risk_level": "low",
        "required_permission": "policy.read",
        "description": "Generic action.",
    }


def permission_entry(permission: str, action_pattern: str) -> PermissionCatalogEntry:
    return PermissionCatalogEntry(**permission_payload(permission, action_pattern))


def permission_payload(
    permission: str = "policy.read",
    action_pattern: str = "policy.catalog.read",
) -> dict[str, object]:
    return {
        "permission_id": f"permission-{permission.replace('.', '-')}",
        "permission": permission,
        "category": "policy",
        "resource_type": "policy_catalog",
        "action_pattern": action_pattern,
        "description": "Generic permission.",
    }


def role_template(role_name: str, permissions: list[str]) -> RoleTemplate:
    return RoleTemplate(**role_payload(role_name, permissions))


def role_payload(
    role_name: str = "viewer",
    permissions: list[str] | None = None,
) -> dict[str, object]:
    return {
        "role_template_id": f"role-template-{role_name}",
        "role_name": role_name,
        "description": "Role template.",
        "permissions": permissions or ["policy.read"],
        "constraints": [],
    }


def simulation_payload() -> dict[str, object]:
    return {
        "action_type": "memory.retrieve",
        "resource_type": "memory_record",
        "risk_level": "low",
        "requested_permissions": ["memory.retrieve"],
        "security_scope": ["workspace:main"],
        "context": {},
    }


def policy_test_payload() -> dict[str, object]:
    return {
        "policy_test_case_id": "case-1",
        "name": "low risk read",
        "description": "Low-risk read is allowed.",
        "action_type": "memory.retrieve",
        "resource_type": "memory_record",
        "input": simulation_payload(),
        "expected": {"allow": True},
    }


def policy_test_case(case_id: str) -> PolicyTestCase:
    payload = policy_test_payload()
    payload["policy_test_case_id"] = case_id
    return PolicyTestCase(**payload)


def bundle_record(bundle_id: str) -> PolicyBundleRecord:
    return PolicyBundleRecord(
        policy_bundle_id=bundle_id,
        bundle_type="full",
        version="0.1.0",
        content_hash="abc",
        content={"action_catalog": []},
        status="exported",
        created_by="tester",
        created_at=datetime.now(UTC),
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


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["policy.catalog.read", "policy.opa.status"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
