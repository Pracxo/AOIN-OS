from __future__ import annotations

from aion_brain.contracts.confidence import ConfidenceCalibrationRequest
from tests.self_model_helpers import bundle


def test_confidence_calibrator_increases_confidence_with_evidence_refs() -> None:
    services = bundle()

    calibration = services.confidence.calibrate(
        ConfidenceCalibrationRequest(
            source_type="response",
            source_id="response-1",
            evidence_refs=["evidence-1"],
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    assert calibration.confidence > 0.5
    assert calibration.grounding_status == "grounded"


def test_confidence_calibrator_recommends_clarification_for_low_confidence_response() -> None:
    services = bundle()

    calibration = services.confidence.calibrate(
        ConfidenceCalibrationRequest(
            source_type="response",
            source_id="response-1",
            require_grounding=True,
            uncertainty_factors=["missing_context"] * 5,
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    assert calibration.confidence_level == "low"
    assert calibration.clarification_recommended is True
    assert "ungrounded_response" in calibration.required_disclosures
    assert "low_confidence" in calibration.required_disclosures
