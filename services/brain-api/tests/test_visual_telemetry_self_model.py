from __future__ import annotations

from aion_brain.contracts.confidence import ConfidenceCalibrationRequest, SelfAssessmentRequest
from aion_brain.contracts.self_model import LimitationCreateRequest, SelfDescriptionRequest
from tests.self_model_helpers import bundle


def test_visual_telemetry_emits_self_model_events() -> None:
    services = bundle()

    services.description.describe(SelfDescriptionRequest(scope=["workspace:main"]))
    services.capabilities.refresh(["workspace:main"], dry_run=True)
    services.limitations.create_limitation(
        LimitationCreateRequest(
            limitation_key="generic.telemetry_limit",
            category="generic",
            severity="critical",
            title="Telemetry limitation",
            description="A generic limitation for telemetry.",
            owner_scope=["workspace:main"],
        )
    )
    services.confidence.calibrate(
        ConfidenceCalibrationRequest(
            source_type="response",
            source_id="response-1",
            evidence_refs=["evidence-1"],
            metadata={"owner_scope": ["workspace:main"]},
        )
    )
    services.assessment.run(SelfAssessmentRequest(owner_scope=["workspace:main"]))

    event_types = {getattr(event, "event_type", None) for event in services.telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in services.telemetry.events}

    assert {
        "self_description_generated",
        "capability_awareness_refreshed",
        "limitation_record_created",
        "confidence_calibrated",
        "self_assessment_started",
        "self_assessment_completed",
    } <= event_types
    assert {
        "self_model",
        "capability_awareness",
        "limitation",
        "confidence",
        "self_assessment",
    } <= node_types
