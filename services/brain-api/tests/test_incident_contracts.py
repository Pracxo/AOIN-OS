from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.incidents import (
    IncidentCorrelationRule,
    IncidentRecord,
    IncidentSignal,
)
from aion_brain.contracts.root_cause import RecoveryReview, RootCauseCandidate


def _signal_payload() -> dict[str, object]:
    return {
        "incident_signal_id": "signal-1",
        "source_type": "run_supervision",
        "source_id": "run-1",
        "signal_type": "stalled",
        "severity": "high",
        "status": "new",
        "title": "Run stalled",
        "summary": "A supervised run stalled.",
        "owner_scope": ["workspace:main"],
        "correlation_key": "incident:run_supervision:stalled:trace-1:run-1",
        "fingerprint": "fp",
        "occurred_at": datetime.now(UTC),
    }


def _incident_payload() -> dict[str, object]:
    return {
        "incident_id": "incident-1",
        "status": "open",
        "incident_type": "run_failure",
        "severity": "high",
        "title": "Run failure",
        "summary": "A local run failed.",
        "owner_scope": ["workspace:main"],
        "correlation_key": "incident:run",
        "fingerprint": "fp",
        "confidence": 0.8,
    }


def test_incident_signal_validates_signal_type() -> None:
    payload = _signal_payload()
    payload["signal_type"] = "domain_outage"

    with pytest.raises(ValidationError):
        IncidentSignal(**payload)


def test_incident_signal_rejects_hidden_reasoning_in_summary() -> None:
    payload = _signal_payload()
    payload["summary"] = "hidden reasoning should not be stored"

    with pytest.raises(ValidationError):
        IncidentSignal(**payload)


def test_incident_record_validates_incident_type() -> None:
    payload = _incident_payload()
    payload["incident_type"] = "domain_specific_failure"

    with pytest.raises(ValidationError):
        IncidentRecord(**payload)


def test_incident_record_rejects_domain_specific_incident_type() -> None:
    payload = _incident_payload()
    payload["incident_type"] = "finance_outage"

    with pytest.raises(ValidationError):
        IncidentRecord(**payload)


def test_incident_correlation_rule_validates_window_seconds() -> None:
    with pytest.raises(ValidationError):
        IncidentCorrelationRule(
            correlation_rule_id="rule-1",
            name="rule",
            description="Generic rule.",
            status="active",
            rule_type="same_trace",
            window_seconds=0,
            owner_scope=["workspace:main"],
        )


def test_root_cause_candidate_validates_candidate_type() -> None:
    with pytest.raises(ValidationError):
        RootCauseCandidate(
            root_cause_candidate_id="root-1",
            incident_id="incident-1",
            status="proposed",
            candidate_type="database_specific_truth",
            severity="medium",
            title="Candidate",
            hypothesis="A generic hypothesis.",
            confidence=0.5,
        )


def test_root_cause_candidate_remains_candidate_not_truth() -> None:
    with pytest.raises(ValidationError):
        RootCauseCandidate(
            root_cause_candidate_id="root-1",
            incident_id="incident-1",
            status="proposed",
            candidate_type="unknown",
            severity="medium",
            title="Candidate",
            hypothesis="A generic hypothesis.",
            confidence=0.5,
            metadata={"is_truth": True},
        )


def test_recovery_review_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        RecoveryReview(
            recovery_review_id="review-1",
            incident_id="incident-1",
            status="completed",
            review_type="generic",
            title="Review",
            summary="Generic review.",
            owner_scope=[],
        )
