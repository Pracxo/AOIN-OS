"""Generic demo fixture service for the scenario harness."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scenarios import (
    DemoFixture,
    DemoFixtureLoadRequest,
    DemoFixtureLoadResult,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.scenarios.repository import ScenarioRepository


class DemoFixtureService:
    """Load safe generic fixtures for local validation."""

    def __init__(
        self,
        repository: ScenarioRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def list_default_fixtures(self, scope: list[str]) -> list[DemoFixture]:
        """Return the built-in generic fixture pack."""
        return _default_fixtures(scope)

    def load(self, request: DemoFixtureLoadRequest) -> DemoFixtureLoadResult:
        """Load one fixture, dry-run by default."""
        if not request.owner_scope:
            request = request.model_copy(update={"owner_scope": ["workspace:main"]})
        self._authorize(
            "demo_fixture.load",
            request.owner_scope,
            created_by=request.created_by,
            context={"dry_run": request.dry_run},
        )
        fixture = self._resolve_fixture(request)
        now = datetime.now(UTC)
        result = {
            "fixture_type": fixture.fixture_type,
            "planned_records": _planned_records(fixture),
            "external_calls": False,
        }
        loaded = not request.dry_run
        if loaded:
            fixture = self._repository.save_fixture(
                fixture.model_copy(
                    update={
                        "loaded": True,
                        "loaded_at": now,
                        "result": {"loaded": True, **result},
                    }
                )
            )
            self._emit("demo_fixture_loaded", fixture.fixture_id, request.owner_scope, result)
        return DemoFixtureLoadResult(
            fixture_id=fixture.fixture_id,
            loaded=loaded,
            dry_run=request.dry_run,
            result=result,
            reason="dry_run" if request.dry_run else None,
            created_at=now,
        )

    def list_loaded(
        self,
        scope: list[str],
        fixture_type: str | None = None,
    ) -> list[DemoFixture]:
        """List loaded fixture records."""
        self._authorize("demo_fixture.read", scope, context={"fixture_type": fixture_type})
        return self._repository.list_fixtures(scope=scope, fixture_type=fixture_type, loaded=True)

    def _resolve_fixture(self, request: DemoFixtureLoadRequest) -> DemoFixture:
        if request.fixture is not None:
            return request.fixture.model_copy(update={"owner_scope": request.owner_scope})
        default_fixtures = self.list_default_fixtures(request.owner_scope)
        for fixture in default_fixtures:
            if fixture.fixture_id == request.fixture_id or fixture.name == request.fixture_name:
                return fixture
        if request.fixture_id:
            persisted = self._repository.get_fixture(request.fixture_id)
            if persisted is not None:
                return persisted
        raise ValueError("demo_fixture_not_found")

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        created_by: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=created_by,
                workspace_id=None,
                action_type=action_type,
                resource_type="demo_fixture",
                resource_id=None,
                risk_level="low",
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
        payload: dict[str, Any],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            from aion_brain.contracts.telemetry import VisualTelemetryEvent

            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=node_id,
                    event_type="demo_fixture_loaded",
                    node_type="fixture",
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=0.7,
                    payload={"owner_scope": scope, **payload},
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _default_fixtures(scope: list[str]) -> list[DemoFixture]:
    return [
        _fixture("generic_event", "Generic Event", "event", scope),
        _fixture("generic_evidence", "Generic Evidence", "evidence", scope),
        _fixture("generic_memory", "Generic Memory", "memory", scope),
        _fixture("generic_module_package", "Generic Module Package", "module_package", scope),
        _fixture("generic_sandbox_profile", "Generic Sandbox Profile", "sandbox_profile", scope),
    ]


def _fixture(
    fixture_id: str,
    name: str,
    fixture_type: str,
    scope: list[str],
) -> DemoFixture:
    return DemoFixture(
        fixture_id=fixture_id,
        name=name,
        description=f"Safe {name.lower()} fixture for deterministic local validation.",
        status="active",
        fixture_type=fixture_type,  # type: ignore[arg-type]
        owner_scope=scope,
        content={"label": name, "kind": fixture_type, "external_calls": False},
        loaded=False,
        result={},
        created_at=datetime.now(UTC),
        loaded_at=None,
    )


def _planned_records(fixture: DemoFixture) -> list[str]:
    mapping = {
        "event": ["aion_event"],
        "evidence": ["evidence_record"],
        "memory": ["memory_record"],
        "module_package": ["module_package_metadata"],
        "sandbox_profile": ["sandbox_profile_metadata"],
    }
    return mapping.get(fixture.fixture_type, [f"{fixture.fixture_type}_metadata"])
