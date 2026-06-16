from __future__ import annotations

from aion_brain.contracts.decisions import (
    DecisionFrameCreateRequest,
    DecisionOptionCreateRequest,
    DecisionRecord,
    DecisionRecordRequest,
)
from tests.decision_helpers import bundle


def test_decision_record_requires_rationale() -> None:
    try:
        DecisionRecord(
            decision_record_id="record-1",
            decision_frame_id="frame-1",
            rationale="",
        )
    except Exception as exc:
        assert "rationale" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected validation failure")


def test_decision_journal_records_without_executing_option_and_marks_approval() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
        )
    )
    option = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="High",
            description="High risk option.",
            risk_level="high",
        )
    )

    record = services.journal.record_decision(
        DecisionRecordRequest(
            decision_frame_id=frame.decision_frame_id,
            selected_option_id=option.decision_option_id,
            rationale="Recommendation recorded only.",
        )
    )

    assert record.metadata["selected_option_not_executed"] is True
    assert record.approval_request_id == "approval_required"
