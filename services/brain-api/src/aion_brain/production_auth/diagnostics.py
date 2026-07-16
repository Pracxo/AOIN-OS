"""Redacted diagnostics for the disabled production-auth core."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.production_auth import (
    REQUIRED_REASON_CODES,
    STABILIZATION_AUTHORIZATION_SCOPE,
    STABILIZATION_AUTHORIZATION_TASK,
    STABILIZATION_AUTHORIZATION_TRANSACTION_ID,
    ProductionAuthCoreConfig,
    ProductionAuthDiagnosticSnapshot,
    utc_now,
)


class ProductionAuthDiagnosticBuilder:
    """Build safe diagnostic snapshots for internal kernel checks."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory or (lambda: f"prod-auth-diagnostic-{uuid4().hex}")

    def build(self, config: ProductionAuthCoreConfig) -> ProductionAuthDiagnosticSnapshot:
        """Return a redacted diagnostic snapshot with no request payload data."""

        return ProductionAuthDiagnosticSnapshot(
            snapshot_id=self._id_factory(),
            production_auth_core_implemented=config.production_auth_core_implemented,
            production_auth_core_state=config.production_auth_core_state,
            implementation_state=config.production_auth_core_state,
            runtime_guard_hold_active=config.runtime_guard_hold_active,
            runtime_no_go_status=config.runtime_no_go_status,
            runtime_enabled=config.runtime_enabled,
            blocker_count=len(REQUIRED_REASON_CODES),
            reason_codes=tuple(REQUIRED_REASON_CODES),
            authorization_transaction_id=config.authorization_transaction_id,
            authorization_scope=config.authorization_scope,
            stabilization_authorization_transaction_id=(
                STABILIZATION_AUTHORIZATION_TRANSACTION_ID
            ),
            stabilization_authorization_task=STABILIZATION_AUTHORIZATION_TASK,
            stabilization_authorization_scope=STABILIZATION_AUTHORIZATION_SCOPE,
            redacted=True,
            metadata={
                "implementation_present": config.implementation_present,
                "authorization_consumed_by_task": config.authorization_consumed_by_task,
                "authorization_reusable": config.authorization_reusable,
                "stabilization_authorization_task": config.stabilization_authorization_task,
            },
            created_at=self._clock(),
        )


__all__ = ["ProductionAuthDiagnosticBuilder"]
