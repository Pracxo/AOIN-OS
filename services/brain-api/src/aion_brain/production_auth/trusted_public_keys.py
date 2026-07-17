"""Immutable public-key registry for offline identity assertion verification."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from types import MappingProxyType

from aion_brain.contracts.identity_assertion import (
    TrustedIdentityAssertionPublicKey,
    normalize_utc_datetime,
)
from aion_brain.production_auth.identity_assertion import decode_base64url_unpadded


class TrustedPublicKeyResolutionError(ValueError):
    """Fail-closed public-key resolution error with a safe reason code."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__("identity assertion public key resolution failed")


class TrustedPublicKeyRegistry:
    """Immutable exact-key registry with no fallback or network discovery."""

    def __init__(self, keys: Iterable[TrustedIdentityAssertionPublicKey]) -> None:
        by_id: dict[str, TrustedIdentityAssertionPublicKey] = {}
        material_issuers: dict[bytes, str] = {}
        for key in tuple(keys):
            if key.key_id in by_id:
                raise ValueError("duplicate trusted public key id")
            material = decode_base64url_unpadded(key.public_key_base64url, expected_length=32)
            prior_issuer = material_issuers.get(material)
            if prior_issuer is not None and prior_issuer != key.issuer:
                raise ValueError("duplicate key material cannot cross issuers")
            material_issuers[material] = key.issuer
            by_id[key.key_id] = key
        self._by_id = MappingProxyType(dict(by_id))
        self._key_ids = tuple(sorted(by_id))

    def key_ids(self) -> tuple[str, ...]:
        """Return immutable key IDs in deterministic order."""

        return self._key_ids

    def get(self, key_id: str) -> TrustedIdentityAssertionPublicKey | None:
        """Return an exact key by ID, or None."""

        return self._by_id.get(key_id)

    def resolve(
        self,
        key_id: str,
        issuer: str,
        issued_at: datetime,
    ) -> TrustedIdentityAssertionPublicKey:
        """Resolve an exact active key for issuer and assertion time."""

        issued_at_utc = normalize_utc_datetime(issued_at)
        key = self._by_id.get(key_id)
        if key is None:
            raise TrustedPublicKeyResolutionError("public_key_unknown")
        if key.issuer != issuer:
            raise TrustedPublicKeyResolutionError("public_key_issuer_mismatch")
        if key.revoked:
            raise TrustedPublicKeyResolutionError("public_key_revoked")
        if issued_at_utc < key.active_from:
            raise TrustedPublicKeyResolutionError("public_key_inactive")
        if key.active_until is not None and issued_at_utc >= key.active_until:
            raise TrustedPublicKeyResolutionError("public_key_retired")
        return key


__all__ = ["TrustedPublicKeyRegistry", "TrustedPublicKeyResolutionError"]
