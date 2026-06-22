"""Runtime configuration contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.runtime_config import (
    ConfigProfile,
    ConfigSnapshot,
    ConfigValidationRun,
    FeatureFlagOverride,
    RuntimeConfigValue,
)

SCOPE = ["workspace:main"]


def test_runtime_config_value_rejects_raw_sensitive_value() -> None:
    with pytest.raises(ValidationError):
        RuntimeConfigValue(
            config_value_id="value-1",
            config_key="AION_API_KEY",
            config_value={"value": "sk-rawsecret1234567890"},
            value_type="string",
            source="env",
            status="active",
            sensitive=True,
            mutable=False,
            requires_restart=True,
            owner_scope=SCOPE,
            metadata={},
        )


def test_config_profile_rejects_full_autonomy_enabled_by_default() -> None:
    with pytest.raises(ValidationError):
        _profile(values={"autonomy.full": True})


def test_config_profile_rejects_external_tools_enabled_by_default() -> None:
    with pytest.raises(ValidationError):
        _profile(values={"autonomy.external_tools": True})


def test_feature_flag_override_validates_feature_key() -> None:
    with pytest.raises(ValidationError):
        FeatureFlagOverride(
            feature_override_id="override-1",
            feature_key="not valid",
            enabled=True,
            source="runtime",
            status="active",
            owner_scope=SCOPE,
            reason="test",
            metadata={},
        )


def test_feature_flag_override_rejects_domain_specific_feature_key() -> None:
    with pytest.raises(ValidationError):
        FeatureFlagOverride(
            feature_override_id="override-1",
            feature_key="finance.example",
            enabled=True,
            source="runtime",
            status="active",
            owner_scope=SCOPE,
            reason="test",
            metadata={},
        )


def test_config_snapshot_requires_config_hash() -> None:
    with pytest.raises(ValidationError):
        ConfigSnapshot(
            config_snapshot_id="snapshot-1",
            snapshot_type="manual",
            status="active",
            owner_scope=SCOPE,
            settings={},
            feature_flags={},
            adapter_status={},
            config_hash="",
            drift={},
            metadata={},
        )


def test_config_validation_run_validates_status() -> None:
    with pytest.raises(ValidationError):
        ConfigValidationRun(
            config_validation_id="validation-1",
            status="unknown",
            checks=[],
            failures=[],
            warnings=[],
            report={},
        )


def _profile(values: dict[str, object]) -> ConfigProfile:
    return ConfigProfile(
        config_profile_id="profile-1",
        name="safe",
        description="safe profile",
        status="active",
        profile_type="custom",
        owner_scope=SCOPE,
        values=values,
        feature_flags={},
        constraints=[],
        metadata={},
    )
