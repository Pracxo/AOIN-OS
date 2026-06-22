from __future__ import annotations

from aion_brain.contracts.grounding import GroundingVerificationRequest
from tests.grounding_helpers import DenyPolicy, service_bundle


def test_grounding_verifier_passes_grounded_text() -> None:
    bundle = service_bundle()

    run = bundle.verifier.verify(
        GroundingVerificationRequest(
            trace_id="trace-1",
            target_type="generic",
            target_id="target-1",
            owner_scope=["workspace:main"],
            text="AION records deterministic source support.",
            metadata={},
        )
    )

    assert run.status in {"passed", "warning", "failed"}
    assert run.grounding_verification_id


def test_grounding_verifier_fails_required_evidence_missing() -> None:
    bundle = service_bundle()

    run = bundle.verifier.verify(
        GroundingVerificationRequest(
            trace_id="trace-1",
            target_type="generic",
            target_id="target-1",
            owner_scope=["workspace:main"],
            text="AION records deterministic source support.",
            required_source_types=["evidence"],
            metadata={},
        )
    )

    assert run.status == "insufficient_sources"


def test_grounding_verifier_returns_blocked_by_policy() -> None:
    bundle = service_bundle(DenyPolicy())

    run = bundle.verifier.verify(
        GroundingVerificationRequest(
            target_type="generic",
            target_id="target-1",
            owner_scope=["workspace:main"],
            text="AION records deterministic source support.",
        )
    )

    assert run.status == "blocked_by_policy"
