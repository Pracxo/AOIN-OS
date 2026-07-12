"""Audit event builder for the disabled production-auth core."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.production_auth import (
    AUTHORIZATION_TRANSACTION_ID,
    ProductionAuthAuditEvent,
    ProductionAuthAuditEventType,
    ProductionAuthPolicyDecision,
    utc_now,
)


class ProductionAuthAuditBuilder:
    """Build redacted audit events with no runtime effect."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory or (lambda: f"prod-auth-audit-{uuid4().hex}")

    def build(
        self,
        *,
        event_type: ProductionAuthAuditEventType,
        decision: ProductionAuthPolicyDecision,
        metadata: dict[str, object] | None = None,
    ) -> ProductionAuthAuditEvent:
        """Return one redacted audit event for an internal preview."""

        return ProductionAuthAuditEvent(
            event_id=self._id_factory(),
            event_type=event_type,
            request_id=decision.request_id,
            outcome=decision.outcome,
            reason_codes=decision.reason_codes,
            runtime_effect=False,
            redacted=True,
            authorization_transaction_id=AUTHORIZATION_TRANSACTION_ID,
            created_at=self._clock(),
            metadata={
                "policy_version": decision.policy_version,
                **(metadata or {}),
            },
        )


__all__ = ["ProductionAuthAuditBuilder"]
