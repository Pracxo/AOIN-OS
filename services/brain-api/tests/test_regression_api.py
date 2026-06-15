"""Regression and local evaluation adapter API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.regression import get_regression_service
from aion_brain.contracts.regression import (
    EvalAdapterRunResult,
    RegressionCase,
    RegressionRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class RegressionAPI:
    def with_actor_context(self, actor_context):
        return self

    def create_case(self, request):
        return case()

    def get_case(self, case_id, scope):
        return case()

    def list_cases(self, scope, status=None, tags=None, limit=50):
        return [case()]

    def disable_case(self, case_id, reason):
        return case().model_copy(update={"status": "disabled"})

    def run_regression(self, request):
        return run()

    def get_run(self, regression_run_id, scope):
        return run()

    def run_eval_adapter(self, request, adapter):
        return EvalAdapterRunResult(adapter_name="local", status="completed", output={})


def test_regression_and_local_eval_routes_work() -> None:
    """Golden case, run, and local eval routes return AION contracts."""
    app.dependency_overrides[get_regression_service] = lambda: RegressionAPI()
    app.dependency_overrides[get_actor_context] = actor_context
    client = TestClient(app)
    try:
        created = client.post(
            "/brain/regression/cases",
            json={
                "name": "Stable planning",
                "description": "Generic golden trace.",
                "source_trace_id": "trace-1",
                "owner_scope": ["workspace:main"],
            },
        )
        listed = client.get("/brain/regression/cases", params={"scope": "workspace:main"})
        disabled = client.post(
            "/brain/regression/cases/case-1/disable",
            json={"reason": "retired"},
        )
        executed = client.post(
            "/brain/regression/run",
            json={"case_ids": ["case-1"], "owner_scope": ["workspace:main"]},
        )
        evaluated = client.post(
            "/brain/eval/adapters/run",
            json={"adapter_name": "local", "config": {}},
        )
    finally:
        app.dependency_overrides.clear()
    assert created.status_code == 200
    assert listed.status_code == 200
    assert disabled.status_code == 200
    assert executed.status_code == 200
    assert evaluated.status_code == 200


def case() -> RegressionCase:
    return RegressionCase(
        case_id="case-1",
        name="Stable planning",
        description="Generic golden trace.",
        source_trace_id="trace-1",
        input_snapshot_id="snapshot-1",
        expected_snapshot_id="snapshot-2",
        owner_scope=["workspace:main"],
        status="active",
        tags=[],
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def run() -> RegressionRun:
    return RegressionRun(
        regression_run_id="run-1",
        status="completed",
        case_count=0,
        passed_count=0,
        failed_count=0,
        drift_count=0,
        results=[],
        report={},
        created_by="actor-1",
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["regression.run", "eval.adapter.run"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
