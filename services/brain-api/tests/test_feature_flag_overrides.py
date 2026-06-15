"""Feature flag override service tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from aion_brain.api_support.errors import AIONConflictException
from aion_brain.contracts.runtime_config import FeatureFlagOverrideRequest
from tests.runtime_config_fakes import SCOPE, services


def test_feature_flag_override_service_blocks_unsafe_full_autonomy_override() -> None:
    _, _, feature_overrides, *_ = services()

    with pytest.raises(AIONConflictException):
        feature_overrides.create_override(
            FeatureFlagOverrideRequest(
                feature_key="autonomy.full",
                enabled=True,
                owner_scope=SCOPE,
                reason="unsafe",
            )
        )


def test_feature_flag_override_service_expires_old_overrides() -> None:
    _, _, feature_overrides, *_ = services()
    old = datetime.now(UTC) - timedelta(days=1)
    override = feature_overrides.create_override(
        FeatureFlagOverrideRequest(
            feature_key="runtime_config.feature_overrides",
            enabled=False,
            owner_scope=SCOPE,
            reason="temporary",
            expires_at=old,
        )
    )

    expired = feature_overrides.expire_old(now=datetime.now(UTC))

    assert expired[0].feature_override_id == override.feature_override_id
    assert expired[0].status == "expired"
