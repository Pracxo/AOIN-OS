"""Disabled production-auth request identity boundary service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.api import RequestContext
from aion_brain.contracts.request_identity import (
    REQUIRED_REASON_CODES,
    RequestIdentityBoundaryBundle,
    RequestIdentityBoundaryStatus,
    RequestIdentityDiagnosticSnapshot,
    RequestIdentitySource,
    RequestIdentityVerificationInput,
    RequestIdentityVerifierType,
    utc_now,
)
from aion_brain.production_auth.request_evidence import (
    build_request_identity_audit_event,
    build_request_identity_context,
    build_request_identity_diagnostic_snapshot,
    build_request_identity_provenance_record,
    build_request_identity_status,
)
from aion_brain.production_auth.verifier import (
    DisabledRequestIdentityVerifier,
    RequestIdentityVerifier,
)


class ProductionAuthRequestIdentityBoundary:
    """Attach anonymous disabled request identity evidence from safe correlation."""

    def __init__(
        self,
        verifier: RequestIdentityVerifier | None = None,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[str], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")
        self._verifier = verifier or DisabledRequestIdentityVerifier(
            clock=clock,
            id_factory=self._id_factory,
        )

    @property
    def verifier(self) -> RequestIdentityVerifier:
        """Return the configured internal verifier."""

        return self._verifier

    async def build_bundle(
        self,
        request_context: RequestContext,
        *,
        registered: bool = True,
    ) -> RequestIdentityBoundaryBundle:
        """Build a correlated disabled request identity evidence bundle."""

        verifier_type = _verifier_type(self._verifier)
        identity_source = _identity_source(self._verifier)
        verification_input = RequestIdentityVerificationInput(
            request_id=request_context.request_id,
            trace_id=request_context.trace_id,
            correlation_id=request_context.correlation_id,
            identity_source=identity_source,
            metadata={"safe_correlation_only": True},
            created_at=self._clock(),
        )
        verification = await self._verifier.verify(verification_input)
        context = build_request_identity_context(
            verification,
            clock=self._clock,
            id_factory=self._id_factory,
        )
        audit_event = build_request_identity_audit_event(
            event_type="request_identity_boundary_attached",
            verification=verification,
            context=context,
            clock=self._clock,
            id_factory=self._id_factory,
            metadata={"request_context_actor_ignored": True},
        )
        provenance = build_request_identity_provenance_record(
            verification=verification,
            verifier_type=verifier_type,
            clock=self._clock,
            id_factory=self._id_factory,
        )
        status = self.status(registered=registered)
        return RequestIdentityBoundaryBundle(
            bundle_id=self._id_factory("request-identity-bundle"),
            request_id=verification.request_id,
            trace_id=verification.trace_id,
            correlation_id=verification.correlation_id,
            verification=verification,
            identity_context=context,
            audit_event=audit_event,
            provenance=provenance,
            status=status,
            reason_codes=tuple(REQUIRED_REASON_CODES),
            created_at=self._clock(),
            metadata={"request_context_actor_ignored": True},
        )

    def status(self, *, registered: bool = False) -> RequestIdentityBoundaryStatus:
        """Return safe disabled boundary status."""

        return build_request_identity_status(
            registered=registered,
            clock=self._clock,
            id_factory=self._id_factory,
        )

    def diagnostic_snapshot(
        self,
        *,
        registered: bool = False,
    ) -> RequestIdentityDiagnosticSnapshot:
        """Return safe disabled boundary diagnostics."""

        return build_request_identity_diagnostic_snapshot(
            registered=registered,
            verifier_type=_verifier_type(self._verifier),
            clock=self._clock,
            id_factory=self._id_factory,
        )


def _identity_source(verifier: RequestIdentityVerifier) -> RequestIdentitySource:
    value = getattr(verifier, "identity_source", "disabled_verifier")
    if value == "deterministic_disabled_test_verifier":
        return "deterministic_disabled_test_verifier"
    return "disabled_verifier"


def _verifier_type(verifier: RequestIdentityVerifier) -> RequestIdentityVerifierType:
    value = getattr(verifier, "verifier_type", "disabled")
    if value == "deterministic_disabled_test":
        return "deterministic_disabled_test"
    return "disabled"


__all__ = ["ProductionAuthRequestIdentityBoundary"]
