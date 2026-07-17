"""Offline Ed25519 identity assertion verifier."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from aion_brain.contracts.identity_assertion import (
    IdentityAssertionEnvelope,
    IdentityAssertionReasonCode,
    IdentityAssertionVerificationBundle,
    IdentityAssertionVerificationPolicy,
    TrustedIdentityAssertionPublicKey,
    normalize_utc_datetime,
)
from aion_brain.production_auth.identity_assertion import (
    decode_base64url_unpadded,
    identity_assertion_signing_input,
)
from aion_brain.production_auth.identity_assertion_evidence import (
    build_identity_assertion_verification_bundle,
)
from aion_brain.production_auth.trusted_public_keys import (
    TrustedPublicKeyRegistry,
    TrustedPublicKeyResolutionError,
)

_EvidenceSlot = Literal["verification", "bundle", "event", "provenance", "snapshot"]


class OfflineEd25519IdentityAssertionVerifier:
    """Verify detached offline assertions without authenticating requests."""

    def __init__(
        self,
        *,
        public_keys: TrustedPublicKeyRegistry | Iterable[TrustedIdentityAssertionPublicKey],
        policy: IdentityAssertionVerificationPolicy,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[_EvidenceSlot], str] | None = None,
    ) -> None:
        self._registry = (
            public_keys
            if isinstance(public_keys, TrustedPublicKeyRegistry)
            else TrustedPublicKeyRegistry(public_keys)
        )
        self._policy = policy
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda slot: f"{slot}-{uuid4().hex}")

    @property
    def public_key_registry(self) -> TrustedPublicKeyRegistry:
        """Return the immutable public-key registry."""

        return self._registry

    @property
    def policy(self) -> IdentityAssertionVerificationPolicy:
        """Return the verifier policy."""

        return self._policy

    def verify(self, envelope: IdentityAssertionEnvelope) -> IdentityAssertionVerificationBundle:
        """Verify one envelope and return redacted evidence."""

        verified_at = normalize_utc_datetime(self._clock())
        primary_reason: IdentityAssertionReasonCode | None = None
        try:
            key = self._registry.resolve(
                envelope.key_id,
                envelope.payload.issuer,
                envelope.payload.issued_at,
            )
            primary_reason = self._policy_rejection(envelope, verified_at)
            if primary_reason is None:
                signature = decode_base64url_unpadded(envelope.signature, expected_length=64)
                public_key_bytes = decode_base64url_unpadded(
                    key.public_key_base64url,
                    expected_length=32,
                )
                public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
                public_key.verify(signature, identity_assertion_signing_input(envelope.payload))
        except TrustedPublicKeyResolutionError as exc:
            primary_reason = _safe_resolution_reason(exc.reason_code)
        except InvalidSignature:
            primary_reason = "signature_invalid"
        except (TypeError, ValueError):
            primary_reason = "malformed_envelope"
        return self._bundle(
            envelope=envelope,
            verified=primary_reason is None,
            primary_reason_code=primary_reason or "identity_assertion_verified",
            verified_at=verified_at,
        )

    def _policy_rejection(
        self,
        envelope: IdentityAssertionEnvelope,
        verified_at: datetime,
    ) -> IdentityAssertionReasonCode | None:
        payload = envelope.payload
        if payload.issuer != self._policy.expected_issuer:
            return "issuer_mismatch"
        if payload.audience != self._policy.expected_audience:
            return "audience_mismatch"
        lifetime_seconds = (payload.expires_at - payload.issued_at).total_seconds()
        if lifetime_seconds > self._policy.maximum_assertion_lifetime_seconds:
            return "assertion_lifetime_exceeded"
        skew = timedelta(seconds=self._policy.allowed_clock_skew_seconds)
        if payload.issued_at > verified_at + skew:
            return "future_issued_at"
        if payload.not_before > verified_at + skew:
            return "not_yet_valid"
        if payload.expires_at < verified_at - skew:
            return "assertion_expired"
        return None

    def _bundle(
        self,
        *,
        envelope: IdentityAssertionEnvelope,
        verified: bool,
        primary_reason_code: IdentityAssertionReasonCode,
        verified_at: datetime,
    ) -> IdentityAssertionVerificationBundle:
        return build_identity_assertion_verification_bundle(
            envelope=envelope,
            verified=verified,
            primary_reason_code=primary_reason_code,
            verified_at=verified_at,
            verification_id=self._id_factory("verification"),
            bundle_id=self._id_factory("bundle"),
            event_id=self._id_factory("event"),
            provenance_id=self._id_factory("provenance"),
            snapshot_id=self._id_factory("snapshot"),
            public_key_count=len(self._registry.key_ids()),
            policy=self._policy,
        )


def _safe_resolution_reason(value: str) -> IdentityAssertionReasonCode:
    if value in {
        "public_key_unknown",
        "public_key_issuer_mismatch",
        "public_key_revoked",
        "public_key_inactive",
        "public_key_retired",
    }:
        return value  # type: ignore[return-value]
    return "malformed_public_key"


__all__ = ["OfflineEd25519IdentityAssertionVerifier"]
