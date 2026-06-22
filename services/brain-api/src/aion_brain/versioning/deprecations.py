"""Deprecation policy helpers."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.versioning import DeprecationPolicy


def default_deprecation_policy(version: str) -> DeprecationPolicy:
    """Return the default v0.1 deprecation policy."""
    return DeprecationPolicy(
        policy_id=f"deprecation-policy-{uuid4().hex}",
        version=version,
        rules=[
            {
                "rule": "no_silent_removal_in_stable",
                "description": "Stable features require deprecation metadata before removal.",
            },
            {
                "rule": "alpha_contracts_may_change",
                "description": "v0.1 alpha contracts may change before a stable release.",
            },
            {
                "rule": "feature_registry_records_deprecation",
                "description": "Deprecated features record deprecated_at and reason metadata.",
            },
        ],
        created_at=datetime.now(UTC),
    )
