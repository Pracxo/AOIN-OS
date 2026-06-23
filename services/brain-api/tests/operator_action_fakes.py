"""Shared fakes for governed operator action tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.operator_actions import OperatorActionCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.operator_actions import (
    OperatorActionBlockerService,
    OperatorActionPreviewService,
    OperatorActionQueryService,
    OperatorActionRepository,
    OperatorActionRequestService,
    OperatorActionReviewService,
)


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


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=["test"],
            audit_level="standard",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[object] = []

    def record_event(self, event: object) -> None:
        self.events.append(event)


class FakeProvenance:
    def __init__(self) -> None:
        self.links: list[tuple[str, str, str]] = []

    def record_link(self, source_id: str, target_id: str, relation_type: str) -> None:
        self.links.append((source_id, target_id, relation_type))


class OperatorActionFixture:
    def __init__(self, policy: object | None = None) -> None:
        self.settings = Settings(
            _env_file=None,
            DATABASE_URL="sqlite+pysqlite:///:memory:",
        )
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.policy = policy or AllowPolicy()
        self.repository = OperatorActionRepository(engine=engine)
        self.telemetry = FakeTelemetry()
        self.audit = FakeAudit()
        self.provenance = FakeProvenance()
        self.blockers = OperatorActionBlockerService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.previews = OperatorActionPreviewService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.requests = OperatorActionRequestService(
            self.repository,
            self.policy,
            blocker_service=self.blockers,
            preview_service=self.previews,
            telemetry_service=self.telemetry,
            audit_sink=self.audit,
            provenance_service=self.provenance,
            settings=self.settings,
        )
        self.reviews = OperatorActionReviewService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            audit_sink=self.audit,
            provenance_service=self.provenance,
            settings=self.settings,
        )
        self.query = OperatorActionQueryService(self.repository, self.policy)


def operator_action_request(**overrides: object) -> OperatorActionCreateRequest:
    payload = {
        "action_key": "operator.review",
        "action_type": "generic",
        "target_type": "generic",
        "owner_scope": ["workspace:main"],
        "risk_level": "medium",
        "request_payload": {"summary": "review generic local record"},
        "create_preview": False,
    }
    payload.update(overrides)
    return OperatorActionCreateRequest(**payload)
