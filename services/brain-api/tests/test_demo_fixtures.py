"""Demo fixture service tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scenarios import DemoFixtureLoadRequest
from aion_brain.scenarios.fixtures import DemoFixtureService
from aion_brain.scenarios.repository import ScenarioRepository


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


def test_demo_fixture_service_dry_run_loads_no_records() -> None:
    service = fixture_service()
    result = service.load(
        DemoFixtureLoadRequest(
            fixture_id="generic_event",
            owner_scope=["workspace:main"],
            dry_run=True,
        )
    )

    assert result.loaded is False
    assert service.list_loaded(["workspace:main"]) == []


def test_demo_fixture_service_controlled_load_persists_generic_record() -> None:
    service = fixture_service()
    result = service.load(
        DemoFixtureLoadRequest(
            fixture_id="generic_memory",
            owner_scope=["workspace:main"],
            dry_run=False,
        )
    )

    loaded = service.list_loaded(["workspace:main"], fixture_type="memory")
    assert result.loaded is True
    assert len(loaded) == 1
    assert loaded[0].fixture_type == "memory"


def fixture_service() -> DemoFixtureService:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return DemoFixtureService(ScenarioRepository(engine=engine), AllowPolicy())
