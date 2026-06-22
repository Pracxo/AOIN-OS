from __future__ import annotations

from aion_brain.contracts.responses import ResponseComposeRequest
from tests.dialogue_helpers import service_bundle
from tests.self_model_helpers import bundle as self_model_bundle


def test_response_metadata_includes_confidence_calibration_when_enabled() -> None:
    dialogue = service_bundle()
    self_model = self_model_bundle()
    dialogue.response_composer._confidence_calibrator = self_model.confidence

    response = dialogue.response_composer.compose(
        ResponseComposeRequest(
            context={"evidence_refs": ["evidence-1"], "owner_scope": ["workspace:main"]},
            reasoning_result={"summary": "Grounded response."},
        )
    )

    assert response.metadata["calibration_id"].startswith("confidence-")
    assert response.metadata["confidence_level"] in {"medium", "high"}


def test_response_verifier_detects_unsupported_capability_claim() -> None:
    dialogue = service_bundle()
    self_model = self_model_bundle()
    dialogue.response_verifier._capability_awareness_service = self_model.capabilities
    response = dialogue.response_composer.compose(
        ResponseComposeRequest(
            reasoning_result={"summary": "TurboVec integration is active."},
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    verification = dialogue.response_verifier.verify(response.response_id)

    assert any(issue["code"] == "unsupported_capability_claim" for issue in verification.issues)
    assert any(
        getattr(event, "event_type", None) == "unsupported_capability_claim_detected"
        for event in dialogue.telemetry.events
    )
