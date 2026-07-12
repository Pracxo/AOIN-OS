"""Fail-closed policy evaluator for the disabled production-auth core."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.production_auth import (
    AUTHORIZATION_TRANSACTION_ID,
    REQUIRED_REASON_CODES,
    ProductionAuthCoreConfig,
    ProductionAuthPolicyDecision,
    ProductionAuthPolicyRequest,
    utc_now,
)


class ProductionAuthPolicyEvaluator:
    """Evaluate internal production-auth requests without runtime effect."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory or (lambda: f"prod-auth-decision-{uuid4().hex}")

    def evaluate(
        self,
        request: ProductionAuthPolicyRequest,
        config: ProductionAuthCoreConfig,
    ) -> ProductionAuthPolicyDecision:
        """Return a deterministic blocked decision for every request."""

        return ProductionAuthPolicyDecision(
            decision_id=self._id_factory(),
            request_id=request.request_id,
            outcome="blocked",
            reason_codes=list(REQUIRED_REASON_CODES),
            runtime_effect=False,
            policy_version="production-auth-core-v0.2-disabled",
            authorization_transaction_id=AUTHORIZATION_TRANSACTION_ID,
            created_at=self._clock(),
            metadata={
                "owner_scope": request.owner_scope,
                "requested_operation": request.requested_operation,
                "authorization_scope": config.authorization_scope,
                "implementation_state": config.production_auth_core_state,
            },
        )


__all__ = ["ProductionAuthPolicyEvaluator"]
