"""Service layer for persistent identity assertion replay protection."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aion_brain.contracts.identity_assertion import (
    IdentityAssertionEnvelope,
    IdentityAssertionVerificationBundle,
    assertion_fingerprint,
    normalize_utc_datetime,
)
from aion_brain.contracts.identity_assertion_replay import (
    PARENT_AUTHORIZATION_TRANSACTION_ID,
    IdentityAssertionReplayPolicy,
    IdentityAssertionReplayProtectionBundle,
    IdentityAssertionReplayProtectionOutcome,
    IdentityAssertionReplayProtectionResult,
    IdentityAssertionReplayRecord,
    IdentityAssertionReplayRepositoryResult,
    protection_reason_codes,
)
from aion_brain.production_auth.identity_assertion_replay import (
    compute_identity_assertion_retain_until,
    derive_identity_assertion_issuer_fingerprint,
    derive_identity_assertion_replay_key,
)
from aion_brain.production_auth.identity_assertion_replay_evidence import (
    build_identity_assertion_replay_evidence_bundle,
)
from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)

_ReplayEvidenceSlot = str


class IdentityAssertionReplayProtectionService:
    """Claim verified identity assertions in a persistent replay ledger."""

    def __init__(
        self,
        *,
        repository: IdentityAssertionReplayRepository,
        policy: IdentityAssertionReplayPolicy,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[_ReplayEvidenceSlot], str] | None = None,
        ) -> None:
        self._repository = repository
        self._policy = policy
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda slot: f"{slot}-{uuid4().hex}")

    @property
    def policy(self) -> IdentityAssertionReplayPolicy:
        """Return replay policy."""

        return self._policy

    def protect(
        self,
        *,
        envelope: IdentityAssertionEnvelope,
        verification_bundle: IdentityAssertionVerificationBundle,
    ) -> IdentityAssertionReplayProtectionBundle:
        """Fail closed unless a verified assertion can be claimed exactly once."""

        protected_at = normalize_utc_datetime(self._clock())
        if verification_bundle.result.rejected:
            return self._bundle(
                outcome="verification_rejected",
                cryptographic_verification_verified=False,
                verification_bundle=verification_bundle,
                protected_at=protected_at,
            )
        replay_key = derive_identity_assertion_replay_key(
            issuer=envelope.payload.issuer,
            assertion_id=envelope.payload.assertion_id,
        )
        issuer_fingerprint = derive_identity_assertion_issuer_fingerprint(
            issuer=envelope.payload.issuer,
        )
        payload_fingerprint = assertion_fingerprint(envelope.payload)
        mismatch = _verification_bundle_mismatch(envelope, verification_bundle)
        if mismatch:
            return self._bundle(
                outcome="verification_bundle_mismatch",
                cryptographic_verification_verified=True,
                verification_bundle=verification_bundle,
                protected_at=protected_at,
                replay_key=replay_key,
                issuer_fingerprint=issuer_fingerprint,
                assertion_fingerprint=payload_fingerprint,
            )
        skew = timedelta(seconds=self._policy.allowed_clock_skew_seconds)
        if envelope.payload.expires_at < protected_at - skew:
            return self._bundle(
                outcome="assertion_expired",
                cryptographic_verification_verified=True,
                verification_bundle=verification_bundle,
                protected_at=protected_at,
                replay_key=replay_key,
                issuer_fingerprint=issuer_fingerprint,
                assertion_fingerprint=payload_fingerprint,
            )

        if payload_fingerprint is None:
            return self._bundle(
                outcome="verification_bundle_mismatch",
                cryptographic_verification_verified=True,
                verification_bundle=verification_bundle,
                protected_at=protected_at,
                replay_key=replay_key,
                issuer_fingerprint=issuer_fingerprint,
            )
        retain_until = compute_identity_assertion_retain_until(
            claimed_at=protected_at,
            assertion_expires_at=envelope.payload.expires_at,
            policy=self._policy,
        )
        record = IdentityAssertionReplayRecord(
            replay_key=replay_key,
            issuer_fingerprint=issuer_fingerprint,
            assertion_fingerprint=payload_fingerprint,
            claimed_at=protected_at,
            assertion_expires_at=envelope.payload.expires_at,
            retain_until=retain_until,
            created_at=protected_at,
        )
        repository_result = self._repository.claim(record)
        return self._bundle(
            outcome=repository_result.outcome,
            cryptographic_verification_verified=True,
            verification_bundle=verification_bundle,
            protected_at=protected_at,
            repository_result=repository_result,
            replay_key=replay_key,
            issuer_fingerprint=issuer_fingerprint,
            assertion_fingerprint=payload_fingerprint,
            retain_until=retain_until,
        )

    def _bundle(
        self,
        *,
        outcome: IdentityAssertionReplayProtectionOutcome,
        cryptographic_verification_verified: bool,
        verification_bundle: IdentityAssertionVerificationBundle,
        protected_at: datetime,
        repository_result: IdentityAssertionReplayRepositoryResult | None = None,
        replay_key: str | None = None,
        issuer_fingerprint: str | None = None,
        assertion_fingerprint: str | None = None,
        retain_until: datetime | None = None,
    ) -> IdentityAssertionReplayProtectionBundle:
        repository_available = (
            repository_result.repository_available
            if repository_result is not None
            else outcome not in {"repository_unavailable", "schema_unavailable"}
        )
        schema_available = (
            repository_result.schema_available
            if repository_result is not None
            else outcome not in {"repository_unavailable", "schema_unavailable"}
        )
        result = IdentityAssertionReplayProtectionResult(
            replay_protection_id=self._id_factory("protection"),
            outcome=outcome,
            cryptographic_verification_verified=cryptographic_verification_verified,
            replay_check_performed=repository_result is not None,
            replay_protection_passed=outcome == "claimed",
            claim_created=(
                repository_result.claim_created if repository_result is not None else False
            ),
            replay_detected=outcome == "replay_detected",
            identifier_collision=outcome == "identifier_collision",
            repository_available=repository_available,
            schema_available=schema_available,
            fail_closed=outcome != "claimed",
            replay_key=replay_key,
            issuer_fingerprint=issuer_fingerprint,
            assertion_fingerprint=assertion_fingerprint,
            retain_until=retain_until,
            primary_reason_code=protection_reason_codes(outcome)[0],
            reason_codes=protection_reason_codes(outcome),
            checked_at=protected_at,
        )
        return build_identity_assertion_replay_evidence_bundle(
            result=result,
            repository_result=repository_result,
            policy=self._policy,
            created_at=protected_at,
            bundle_id=self._id_factory("bundle"),
            event_id=self._id_factory("event"),
            provenance_id=self._id_factory("provenance"),
            snapshot_id=self._id_factory("snapshot"),
            metadata={
                "verification_bundle_fingerprint": verification_bundle.fingerprint or "",
            },
        )


def _verification_bundle_mismatch(
    envelope: IdentityAssertionEnvelope,
    verification_bundle: IdentityAssertionVerificationBundle,
) -> bool:
    result = verification_bundle.result
    payload_fingerprint = assertion_fingerprint(envelope.payload)
    return (
        result.verification_id != verification_bundle.verification_id
        or verification_bundle.authorization_transaction_id != PARENT_AUTHORIZATION_TRANSACTION_ID
        or result.verified is not True
        or result.rejected is not False
        or result.request_authenticated is not False
        or result.actor_context_applied is not False
        or result.request_identity_context_applied is not False
        or result.runtime_effect is not False
        or result.runtime_integration_allowed is not False
        or result.replay_check_performed is not False
        or result.assertion_id != envelope.payload.assertion_id
        or result.key_id != envelope.key_id
        or result.issuer != envelope.payload.issuer
        or result.audience != envelope.payload.audience
        or result.assertion_fingerprint != payload_fingerprint
    )


__all__ = ["IdentityAssertionReplayProtectionService"]
