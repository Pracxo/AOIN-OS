from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.confidence import ConfidenceCalibration


def test_confidence_calibration_validates_confidence_bounds() -> None:
    with pytest.raises(ValidationError):
        ConfidenceCalibration(
            calibration_id="calibration-1",
            source_type="response",
            confidence=1.2,
            confidence_level="high",
            grounding_status="grounded",
            clarification_recommended=False,
            verification_recommended=False,
            metadata={},
        )


def test_confidence_calibration_rejects_secret_metadata() -> None:
    with pytest.raises(ValidationError):
        ConfidenceCalibration(
            calibration_id="calibration-1",
            source_type="response",
            confidence=0.8,
            confidence_level="high",
            grounding_status="grounded",
            clarification_recommended=False,
            verification_recommended=False,
            metadata={"token": "hidden"},
        )
