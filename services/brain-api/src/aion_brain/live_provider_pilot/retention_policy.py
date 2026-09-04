"""Retention policy for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import LiveProviderRetentionPolicy


def create_retention_policy(
    *, retention_id: str, created_at: datetime
) -> LiveProviderRetentionPolicy:
    """Create the no-retention policy record."""

    return LiveProviderRetentionPolicy(retention_id=retention_id, created_at=created_at)
