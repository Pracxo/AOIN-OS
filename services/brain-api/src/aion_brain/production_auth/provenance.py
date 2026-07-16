"""Provenance builder for AION-152 disabled production-auth core evidence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.production_auth import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    IMPLEMENTATION_TASK,
    STABILIZATION_AUTHORIZATION_SCOPE,
    STABILIZATION_AUTHORIZATION_TASK,
    STABILIZATION_AUTHORIZATION_TRANSACTION_ID,
    ProductionAuthProvenanceRecord,
    utc_now,
)


class ProductionAuthProvenanceBuilder:
    """Build redacted provenance records for implementation-only evidence."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory or (lambda: f"prod-auth-provenance-{uuid4().hex}")

    def build(
        self,
        *,
        source_refs: list[str],
        metadata: dict[str, object] | None = None,
    ) -> ProductionAuthProvenanceRecord:
        """Return one redacted provenance record for AION-152."""

        return ProductionAuthProvenanceRecord(
            provenance_id=self._id_factory(),
            authorization_transaction_id=AUTHORIZATION_TRANSACTION_ID,
            implementation_task=IMPLEMENTATION_TASK,
            authorization_scope=AUTHORIZATION_SCOPE,
            stabilization_authorization_transaction_id=(
                STABILIZATION_AUTHORIZATION_TRANSACTION_ID
            ),
            stabilization_authorization_task=STABILIZATION_AUTHORIZATION_TASK,
            stabilization_authorization_scope=STABILIZATION_AUTHORIZATION_SCOPE,
            stabilization_authorization_reusable=False,
            stabilization_authorization_expires_on_aion_154_merge=True,
            source_refs=tuple(source_refs),
            runtime_effect=False,
            redacted=True,
            created_at=self._clock(),
            metadata=metadata or {},
        )


__all__ = ["ProductionAuthProvenanceBuilder"]
