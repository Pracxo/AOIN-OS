from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.alerts import AlertCreateRequest
from aion_brain.contracts.incidents import (
    IncidentCorrelationRequest,
    IncidentCreateRequest,
    IncidentSignalCreateRequest,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.root_cause import RecoveryReviewRequest
from aion_brain.incidents.correlation import IncidentCorrelationEngine
from aion_brain.incidents.recovery import RecoveryReviewService
from aion_brain.incidents.repository import IncidentRepository
from aion_brain.incidents.root_cause import RootCauseCandidateService
from aion_brain.incidents.rules import CorrelationRuleService
from aion_brain.incidents.service import IncidentService
from aion_brain.incidents.signals import IncidentSignalService
from aion_brain.notifications.alerts import AlertService
from aion_brain.notifications.repository import NotificationRepository
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from tests.kernel_fakes import AllowPolicy, FakeTelemetry


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"deny-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied_for_test",
            constraints=[],
            audit_level="high",
        )


class FakeActionProposalService:
    def __init__(self) -> None:
        self.created = 0

    def create_proposal(self, request: object) -> object:
        self.created += 1

        class Proposal:
            action_proposal_id = "action-proposal-1"

        return Proposal()


def _repository() -> IncidentRepository:
    return IncidentRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )


def _signal_request(**overrides: object) -> IncidentSignalCreateRequest:
    payload: dict[str, object] = {
        "incident_signal_id": "signal-1",
        "trace_id": "trace-1",
        "source_type": "run_supervision",
        "source_id": "run-1",
        "signal_type": "stalled",
        "severity": "high",
        "title": "Run stalled",
        "summary": "A supervised run stalled.",
        "owner_scope": ["workspace:main"],
        "occurred_at": datetime.now(UTC),
    }
    payload.update(overrides)
    return IncidentSignalCreateRequest(**payload)


def test_incident_signal_service_creates_signal_through_policy() -> None:
    repo = _repository()
    telemetry = FakeTelemetry()
    service = IncidentSignalService(repo, AllowPolicy(), telemetry_service=telemetry)

    signal = service.create_signal(_signal_request())

    assert signal.status == "new"
    assert signal.fingerprint
    assert telemetry.events[-1].event_type == "incident_signal_created"


def test_policy_deny_blocks_signal_create() -> None:
    service = IncidentSignalService(_repository(), DenyPolicy())

    with pytest.raises(PermissionError):
        service.create_signal(_signal_request())


def test_correlation_rule_service_seeds_defaults_dry_run() -> None:
    service = CorrelationRuleService(_repository(), AllowPolicy())

    result = service.seed_default_rules(["workspace:main"], dry_run=True)

    assert result["dry_run"] is True
    assert result["created"] == []
    assert len(result["rules"]) >= 3


def test_incident_correlation_engine_dry_run_creates_no_incidents() -> None:
    repo = _repository()
    IncidentSignalService(repo, AllowPolicy()).create_signal(_signal_request())
    engine = IncidentCorrelationEngine(repo, AllowPolicy())

    run = engine.correlate(
        IncidentCorrelationRequest(owner_scope=["workspace:main"], mode="dry_run")
    )

    assert run.status == "dry_run"
    assert run.incidents_created == 0
    assert repo.list_incidents(limit=10) == []


def test_incident_correlation_engine_controlled_creates_incident_owned_records_only() -> None:
    repo = _repository()
    IncidentSignalService(repo, AllowPolicy()).create_signal(_signal_request())
    engine = IncidentCorrelationEngine(
        repo,
        AllowPolicy(),
        incident_service=IncidentService(repo, AllowPolicy()),
    )

    run = engine.correlate(
        IncidentCorrelationRequest(owner_scope=["workspace:main"], mode="controlled")
    )

    assert run.status == "completed"
    assert run.incidents_created == 1
    assert run.result["source_records_mutated"] is False
    assert repo.get_signal("signal-1").incident_id == run.incidents[0].incident_id  # type: ignore[union-attr]


def test_incident_correlation_groups_by_same_trace_and_correlation_key() -> None:
    repo = _repository()
    signal_service = IncidentSignalService(repo, AllowPolicy())
    signal_service.create_signal(_signal_request(incident_signal_id="signal-1", source_id="run-1"))
    signal_service.create_signal(_signal_request(incident_signal_id="signal-2", source_id="run-1"))

    run = IncidentCorrelationEngine(repo, AllowPolicy()).correlate(
        IncidentCorrelationRequest(owner_scope=["workspace:main"], mode="dry_run")
    )

    assert run.signals_seen == 2
    assert len(run.incidents) == 1


def test_incident_service_acknowledge_does_not_resolve_source_alert() -> None:
    repo = _repository()
    service = IncidentService(repo, AllowPolicy())
    incident = service.create_incident(
        IncidentCreateRequest(
            incident_id="incident-1",
            incident_type="generic",
            severity="high",
            title="Incident",
            summary="Local grouping.",
            owner_scope=["workspace:main"],
            alert_refs=["alert-1"],
        )
    )

    acknowledged = service.acknowledge(incident.incident_id, None, "reviewed")

    assert acknowledged.status == "acknowledged"
    assert acknowledged.alert_refs == ["alert-1"]
    assert acknowledged.metadata["acknowledged_reason"] == "reviewed"


def test_root_cause_service_generates_candidates_from_signals() -> None:
    repo = _repository()
    signal = IncidentSignalService(repo, AllowPolicy()).create_signal(
        _signal_request(signal_type="stalled", source_type="run_supervision")
    )
    incident = IncidentService(repo, AllowPolicy()).create_incident(
        IncidentCreateRequest(
            incident_id="incident-1",
            incident_type="run_failure",
            severity="high",
            title="Incident",
            summary="Local grouping.",
            owner_scope=["workspace:main"],
            signal_refs=[signal.incident_signal_id],
        )
    )
    repo.link_signal(signal.incident_signal_id, incident.incident_id)

    candidates = RootCauseCandidateService(repo, AllowPolicy()).generate_for_incident(
        incident.incident_id, ["workspace:main"]
    )

    assert candidates[0].candidate_type == "run_stalled"
    assert candidates[0].metadata["candidate_not_truth"] is True


def test_root_cause_service_generates_prompt_and_grounding_candidates() -> None:
    repo = _repository()
    service = IncidentSignalService(repo, AllowPolicy())
    prompt = service.create_signal(
        _signal_request(
            incident_signal_id="prompt-signal",
            source_type="prompt_boundary",
            source_id="prompt-1",
            signal_type="high_risk",
        )
    )
    grounding = service.create_signal(
        _signal_request(
            incident_signal_id="grounding-signal",
            source_type="grounding",
            source_id="grounding-1",
            signal_type="unsupported",
        )
    )
    incident = IncidentService(repo, AllowPolicy()).create_incident(
        IncidentCreateRequest(
            incident_id="incident-1",
            title="Incident",
            summary="Local grouping.",
            owner_scope=["workspace:main"],
            signal_refs=[prompt.incident_signal_id, grounding.incident_signal_id],
        )
    )
    repo.link_signal(prompt.incident_signal_id, incident.incident_id)
    repo.link_signal(grounding.incident_signal_id, incident.incident_id)

    candidates = RootCauseCandidateService(repo, AllowPolicy()).generate_for_incident(
        incident.incident_id, ["workspace:main"]
    )

    assert {candidate.candidate_type for candidate in candidates} == {
        "prompt_injection",
        "insufficient_grounding",
    }


def test_recovery_review_service_creates_generic_recommendations_without_actions() -> None:
    repo = _repository()
    incident = IncidentService(repo, AllowPolicy()).create_incident(
        IncidentCreateRequest(
            incident_id="incident-1",
            title="Incident",
            summary="Local grouping.",
            owner_scope=["workspace:main"],
        )
    )
    fake_actions = FakeActionProposalService()

    review = RecoveryReviewService(
        repo,
        AllowPolicy(),
        action_proposal_service=fake_actions,
    ).create_review(
        RecoveryReviewRequest(incident_id=incident.incident_id, owner_scope=["workspace:main"])
    )

    assert review.recommendations
    assert review.action_proposal_refs == []
    assert fake_actions.created == 0
    assert review.metadata["remediation_executed"] is False


def test_recovery_review_service_creates_action_proposal_only_when_requested() -> None:
    repo = _repository()
    incident = IncidentService(repo, AllowPolicy()).create_incident(
        IncidentCreateRequest(
            incident_id="incident-1",
            title="Incident",
            summary="Local grouping.",
            owner_scope=["workspace:main"],
        )
    )
    fake_actions = FakeActionProposalService()

    review = RecoveryReviewService(
        repo,
        AllowPolicy(),
        action_proposal_service=fake_actions,
    ).create_review(
        RecoveryReviewRequest(
            incident_id=incident.incident_id,
            owner_scope=["workspace:main"],
            create_action_proposals=True,
        )
    )

    assert review.action_proposal_refs == ["action-proposal-1"]
    assert fake_actions.created == 1
    assert review.metadata["remediation_executed"] is False


def test_alert_integration_can_create_incident_signal_when_explicit_metadata_true() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    incident_repo = IncidentRepository(engine=engine)
    notification_repo = NotificationRepository(engine=engine)
    signal_service = IncidentSignalService(incident_repo, AllowPolicy())
    alert_service = AlertService(
        notification_repo,
        AllowPolicy(),
        incident_signal_service=signal_service,
    )

    alert_service.create_alert(
        AlertCreateRequest(
            alert_id="alert-1",
            alert_type="failed_run",
            severity="high",
            title="Run failed",
            description="A local supervised run failed.",
            source_type="run_supervision",
            source_id="run-1",
            owner_scope=["workspace:main"],
            metadata={"create_incident_signal": True},
        )
    )

    signals = incident_repo.list_signals(scope=["workspace:main"], limit=10)
    assert len(signals) == 1
    assert signals[0].source_type == "alert"
    assert signals[0].signal_type == "failed"


def test_operator_action_center_surfaces_high_critical_incident() -> None:
    repo = _repository()
    incident_service = IncidentService(repo, AllowPolicy())
    incident_service.create_incident(
        IncidentCreateRequest(
            incident_id="incident-1",
            title="Incident",
            summary="Local grouping.",
            severity="critical",
            owner_scope=["workspace:main"],
        )
    )
    operator_repo = OperatorRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )

    items = ActionCenterService(
        operator_repo,
        AllowPolicy(),
        incident_service=incident_service,
    ).build_action_items(["workspace:main"])

    assert any(item.source_type == "incident" for item in items)


def test_operator_queue_summary_includes_open_incidents() -> None:
    repo = _repository()
    incident_service = IncidentService(repo, AllowPolicy())
    incident_service.create_incident(
        IncidentCreateRequest(
            incident_id="incident-1",
            title="Incident",
            summary="Local grouping.",
            severity="high",
            owner_scope=["workspace:main"],
        )
    )

    queues = QueueSummaryBuilder(incident_service=incident_service).build_queues(["workspace:main"])

    incident_queue = next(queue for queue in queues if queue.queue_type == "incidents")
    assert incident_queue.pending_count == 1
