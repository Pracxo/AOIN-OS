"""Autonomy API tests."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from aion_brain.api.autonomy import (
    get_autonomy_governor,
    get_delegation_service,
    get_run_level_service,
)
from aion_brain.contracts.autonomy import (
    AutonomyDecision,
    AutonomyDecisionRequest,
    AutonomyProfile,
    AutonomyProfileCreateRequest,
    AutonomyStatus,
    DelegationGrant,
    DelegationGrantRequest,
    RunLevelRecord,
    SetRunLevelRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeGovernor:
    """Fake autonomy governor for API tests."""

    def __init__(self) -> None:
        self.profile = profile_contract()
        self.decisions: list[AutonomyDecisionRequest] = []

    def create_profile(self, request: AutonomyProfileCreateRequest) -> AutonomyProfile:
        self.profile = self.profile.model_copy(
            update={
                "name": request.name,
                "actor_id": request.actor_id,
                "workspace_id": request.workspace_id,
                "owner_scope": request.owner_scope,
            }
        )
        return self.profile

    def list_profiles(
        self,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[AutonomyProfile]:
        return [self.profile]

    def get_profile(self, autonomy_profile_id: str) -> AutonomyProfile | None:
        if autonomy_profile_id == self.profile.autonomy_profile_id:
            return self.profile
        return None

    def disable_profile(
        self,
        autonomy_profile_id: str,
        actor_id: str | None,
        reason: str,
    ) -> AutonomyProfile:
        return self.profile.model_copy(
            update={"status": "disabled", "disabled_at": datetime.now(UTC)}
        )

    def decide(self, request: AutonomyDecisionRequest) -> AutonomyDecision:
        self.decisions.append(request)
        return AutonomyDecision(
            autonomy_decision_id="decision-1",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            requested_mode=request.requested_mode,
            resolved_mode=request.requested_mode,
            action_type=request.action_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            risk_level=request.risk_level,
            allow=True,
            approval_required=False,
            delegation_id=None,
            autonomy_profile_id="profile-1",
            run_level_id=None,
            reason="autonomy_allowed",
            constraints=[],
            metadata={},
            created_at=datetime.now(UTC),
        )

    def status(
        self,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
    ) -> AutonomyStatus:
        return AutonomyStatus(
            actor_id=actor_id,
            workspace_id=workspace_id,
            active_profile=self.profile,
            active_run_level=None,
            active_delegations=[],
            effective_mode="assist",
            max_risk_level="medium",
            constraints=[],
            generated_at=datetime.now(UTC),
        )


class FakeRunLevelService:
    """Fake run-level service."""

    def __init__(self) -> None:
        self.record = run_level_contract()

    def set_run_level(self, request: SetRunLevelRequest) -> RunLevelRecord:
        self.record = self.record.model_copy(
            update={
                "run_level": request.run_level,
                "actor_id": request.actor_id,
                "workspace_id": request.workspace_id,
                "set_by": request.set_by,
            }
        )
        return self.record

    def get_active_run_level(
        self,
        actor_id: str | None,
        workspace_id: str | None,
    ) -> RunLevelRecord:
        return self.record

    def list_run_levels(
        self,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[RunLevelRecord]:
        return [self.record]

    def end_run_level(
        self,
        run_level_id: str,
        actor_id: str | None,
        reason: str,
    ) -> RunLevelRecord:
        return self.record.model_copy(update={"status": "ended", "ended_at": datetime.now(UTC)})


class FakeDelegationService:
    """Fake delegation service."""

    def __init__(self) -> None:
        self.grant = delegation_contract()

    def create_grant(self, request: DelegationGrantRequest) -> DelegationGrant:
        self.grant = self.grant.model_copy(
            update={
                "actor_id": request.actor_id,
                "workspace_id": request.workspace_id,
                "delegated_by": request.delegated_by,
                "owner_scope": request.owner_scope,
            }
        )
        return self.grant

    def get_grant(self, delegation_id: str, scope: list[str]) -> DelegationGrant | None:
        return self.grant if delegation_id == self.grant.delegation_id else None

    def list_grants(
        self,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[DelegationGrant]:
        return [self.grant]

    def revoke_grant(
        self,
        delegation_id: str,
        actor_id: str | None,
        reason: str,
    ) -> DelegationGrant:
        return self.grant.model_copy(update={"status": "revoked", "revoked_at": datetime.now(UTC)})


@pytest.fixture
def autonomy_client() -> TestClient:
    """Return a test client with autonomy dependency overrides."""
    app.dependency_overrides[get_autonomy_governor] = lambda: FakeGovernor()
    app.dependency_overrides[get_run_level_service] = lambda: FakeRunLevelService()
    app.dependency_overrides[get_delegation_service] = lambda: FakeDelegationService()
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        security_scope=["workspace:main"],
        dev_mode=True,
    )
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_autonomy_profile_and_status_api(autonomy_client: TestClient) -> None:
    """Profile creation and status use actor context defaults."""
    response = autonomy_client.post(
        "/brain/autonomy/profiles",
        json={"name": "Generic", "description": "Generic profile."},
    )
    status = autonomy_client.get("/brain/autonomy/status")

    assert response.status_code == 200
    assert response.json()["actor_id"] == "actor-1"
    assert status.status_code == 200
    assert status.json()["effective_mode"] == "assist"


def test_autonomy_decide_api_returns_decision(autonomy_client: TestClient) -> None:
    """POST /brain/autonomy/decide returns an AION autonomy decision contract."""
    response = autonomy_client.post(
        "/brain/autonomy/decide",
        json={
            "trace_id": "trace-1",
            "requested_mode": "dry_run",
            "action_type": "context.compile",
            "resource_type": "context",
            "risk_level": "low",
            "context": {},
            "metadata": {},
        },
    )

    assert response.status_code == 200
    assert response.json()["allow"] is True
    assert response.json()["actor_id"] == "actor-1"


def test_run_level_and_delegation_api(autonomy_client: TestClient) -> None:
    """Run-level and delegation APIs return their public contracts."""
    run_level = autonomy_client.post(
        "/brain/autonomy/run-levels",
        json={"run_level": "observe", "reason": "test override"},
    )
    delegation = autonomy_client.post(
        "/brain/autonomy/delegations",
        json={"reason": "bounded generic delegation"},
    )

    assert run_level.status_code == 200
    assert run_level.json()["run_level"] == "observe"
    assert delegation.status_code == 200
    assert delegation.json()["mode"] == "supervised_controlled"


def profile_contract() -> AutonomyProfile:
    """Create a profile contract."""
    now = datetime.now(UTC)
    return AutonomyProfile(
        autonomy_profile_id="profile-1",
        name="Generic",
        description="Generic profile.",
        status="active",
        actor_id="actor-1",
        workspace_id="workspace-1",
        owner_scope=["workspace:main"],
        default_mode="assist",
        max_mode="dry_run",
        max_risk_level="medium",
        allowed_action_types=[],
        denied_action_types=[],
        external_models_allowed=False,
        external_tools_allowed=False,
        background_workflows_allowed=False,
        scheduler_allowed=False,
        skill_promotion_allowed=False,
        memory_forgetting_allowed=False,
        approval_required_modes=["supervised_controlled", "delegated_controlled"],
        constraints=[],
        metadata={},
        created_by="actor-1",
        created_at=now,
        updated_at=now,
    )


def run_level_contract() -> RunLevelRecord:
    """Create a run-level contract."""
    return RunLevelRecord(
        run_level_id="run-level-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        active_profile_id=None,
        run_level="observe",
        status="active",
        reason="test override",
        constraints=[],
        metadata={},
        set_by="actor-1",
        created_at=datetime.now(UTC),
    )


def delegation_contract() -> DelegationGrant:
    """Create a delegation contract."""
    return DelegationGrant(
        delegation_id="delegation-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        delegated_by="actor-1",
        delegated_to="aion-system",
        owner_scope=["workspace:main"],
        mode="supervised_controlled",
        max_risk_level="medium",
        allowed_action_types=[],
        resource_types=[],
        constraints=[],
        status="active",
        reason="bounded generic delegation",
        created_at=datetime.now(UTC),
    )
