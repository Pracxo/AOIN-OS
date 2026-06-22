"""Reflection API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_reflection_engine, get_reflection_repository
from aion_brain.contracts.reflection import ReflectionRecord, ReflectionRequest
from aion_brain.main import app
from tests.test_reflection_contracts import make_evaluation, make_trace


class FakeReflectionEngine:
    """Reflection engine fake."""

    def __init__(self) -> None:
        self.reflection = make_reflection()

    def reflect(self, request: ReflectionRequest) -> ReflectionRecord:
        return self.reflection


class FakeReflectionRepository:
    """Reflection repository fake."""

    def __init__(self) -> None:
        self.reflection = make_reflection()

    def get_reflection(self, reflection_id: str) -> ReflectionRecord | None:
        if reflection_id == self.reflection.reflection_id:
            return self.reflection
        return None

    def list_reflections(
        self,
        *,
        trace_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ReflectionRecord]:
        return [self.reflection][:limit]


def test_reflection_api_create_and_get_endpoints_work() -> None:
    """Reflection endpoints return ReflectionRecord contracts."""
    repository = FakeReflectionRepository()
    app.dependency_overrides[get_reflection_engine] = lambda: FakeReflectionEngine()
    app.dependency_overrides[get_reflection_repository] = lambda: repository
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/reflections",
            json={
                "trace": make_trace().model_dump(mode="json"),
                "evaluation": make_evaluation().model_dump(mode="json"),
            },
        )
        fetched = client.get("/brain/reflections/reflection-1")
        listed = client.get("/brain/reflections", params={"trace_id": "trace-1"})
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert created.json()["reflection_id"] == "reflection-1"
    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert listed.json()[0]["reflection_id"] == "reflection-1"


def make_reflection() -> ReflectionRecord:
    """Create a reflection record."""
    return ReflectionRecord(
        reflection_id="reflection-1",
        trace_id="trace-1",
        learning_signal_ids=[],
        reflection_type="trace_review",
        observations=["successful_plan_pattern_observed"],
        proposed_changes=[],
        risks=[],
        confidence=0.7,
        status="recorded",
        created_at=datetime.now(UTC),
    )
