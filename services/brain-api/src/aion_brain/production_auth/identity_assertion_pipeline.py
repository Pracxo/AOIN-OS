"""Offline identity assertion verification pipeline with replay protection."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.identity_assertion import (
    IdentityAssertionEnvelope,
    normalize_utc_datetime,
)
from aion_brain.contracts.identity_assertion_replay import (
    OfflineIdentityAssertionVerificationPipelineBundle,
    OfflineIdentityAssertionVerificationPipelineOutcome,
    OfflineIdentityAssertionVerificationPipelineResult,
    protection_reason_codes,
)
from aion_brain.production_auth.identity_assertion_replay_service import (
    IdentityAssertionReplayProtectionService,
)
from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)

_PipelineEvidenceSlot = str


class OfflineIdentityAssertionVerificationPipeline:
    """Run offline verification before persistent replay protection."""

    def __init__(
        self,
        *,
        verifier: OfflineEd25519IdentityAssertionVerifier,
        replay_protection: IdentityAssertionReplayProtectionService,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[_PipelineEvidenceSlot], str] | None = None,
    ) -> None:
        self._verifier = verifier
        self._replay_protection = replay_protection
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda slot: f"{slot}-{uuid4().hex}")

    def verify_once(
        self,
        envelope: IdentityAssertionEnvelope,
    ) -> OfflineIdentityAssertionVerificationPipelineBundle:
        """Verify one assertion and reject replay before any request integration exists."""

        created_at = normalize_utc_datetime(self._clock())
        verification_bundle = self._verifier.verify(envelope)
        if verification_bundle.result.rejected:
            outcome: OfflineIdentityAssertionVerificationPipelineOutcome = "verification_rejected"
            result = OfflineIdentityAssertionVerificationPipelineResult(
                pipeline_id=self._id_factory("pipeline"),
                outcome=outcome,
                cryptographic_verified=False,
                replay_check_performed=False,
                replay_detected=False,
                identifier_collision=False,
                verification_and_replay_checks_passed=False,
                fail_closed=True,
                verification_bundle_fingerprint=verification_bundle.fingerprint or "",
                reason_codes=protection_reason_codes("verification_rejected"),
                created_at=created_at,
            )
            return OfflineIdentityAssertionVerificationPipelineBundle(
                bundle_id=self._id_factory("bundle"),
                pipeline_id=result.pipeline_id,
                result=result,
                verification_bundle=verification_bundle,
                created_at=created_at,
            )

        replay_bundle = self._replay_protection.protect(
            envelope=envelope,
            verification_bundle=verification_bundle,
        )
        pipeline_outcome = _pipeline_outcome(replay_bundle.result.outcome)
        result = OfflineIdentityAssertionVerificationPipelineResult(
            pipeline_id=self._id_factory("pipeline"),
            replay_protection_id=replay_bundle.replay_protection_id,
            outcome=pipeline_outcome,
            cryptographic_verified=True,
            replay_check_performed=True,
            replay_detected=pipeline_outcome == "replay_detected",
            identifier_collision=pipeline_outcome == "identifier_collision",
            verification_and_replay_checks_passed=pipeline_outcome == "verified_once",
            fail_closed=pipeline_outcome != "verified_once",
            verification_bundle_fingerprint=verification_bundle.fingerprint or "",
            replay_bundle_fingerprint=replay_bundle.fingerprint or "",
            reason_codes=replay_bundle.result.reason_codes,
            created_at=created_at,
        )
        return OfflineIdentityAssertionVerificationPipelineBundle(
            bundle_id=self._id_factory("bundle"),
            pipeline_id=result.pipeline_id,
            result=result,
            verification_bundle=verification_bundle,
            replay_bundle=replay_bundle,
            created_at=created_at,
        )


def _pipeline_outcome(
    replay_outcome: str,
) -> OfflineIdentityAssertionVerificationPipelineOutcome:
    if replay_outcome == "claimed":
        return "verified_once"
    return cast(OfflineIdentityAssertionVerificationPipelineOutcome, replay_outcome)


__all__ = ["OfflineIdentityAssertionVerificationPipeline"]
