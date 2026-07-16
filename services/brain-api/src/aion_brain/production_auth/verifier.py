"""Provider-agnostic disabled request identity verifier."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import uuid4

from aion_brain.contracts.request_identity import (
    REQUIRED_REASON_CODES,
    RequestIdentitySource,
    RequestIdentityVerificationInput,
    RequestIdentityVerificationResult,
    utc_now,
)


class RequestIdentityVerifier(Protocol):
    """Internal verifier protocol for request identity evidence."""

    identity_source: RequestIdentitySource
    verifier_type: str

    async def verify(
        self,
        input: RequestIdentityVerificationInput,
    ) -> RequestIdentityVerificationResult:
        """Return a disabled anonymous request identity result."""


class DisabledRequestIdentityVerifier:
    """Disabled verifier that performs no I/O and authenticates nobody."""

    identity_source: RequestIdentitySource = "disabled_verifier"
    verifier_type = "disabled"

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[str], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")

    async def verify(
        self,
        input: RequestIdentityVerificationInput,
    ) -> RequestIdentityVerificationResult:
        """Return anonymous disabled identity evidence with zero runtime effect."""

        return RequestIdentityVerificationResult(
            verification_id=self._id_factory("request-identity-verification"),
            request_id=input.request_id,
            trace_id=input.trace_id,
            correlation_id=input.correlation_id,
            identity_source=self.identity_source,
            reason_codes=tuple(REQUIRED_REASON_CODES),
            created_at=self._clock(),
            metadata={"verifier": self.verifier_type, "io_performed": False},
        )


class DeterministicDisabledTestVerifier(DisabledRequestIdentityVerifier):
    """Deterministic disabled verifier intended only for tests."""

    identity_source: RequestIdentitySource = "deterministic_disabled_test_verifier"
    verifier_type = "deterministic_disabled_test"

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[str], str] | None = None,
    ) -> None:
        super().__init__(
            clock=clock,
            id_factory=id_factory or (lambda prefix: f"{prefix}-deterministic"),
        )


__all__ = [
    "DeterministicDisabledTestVerifier",
    "DisabledRequestIdentityVerifier",
    "RequestIdentityVerifier",
]
