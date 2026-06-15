"""Versioning and freeze contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.compatibility import SDKCompatibilityReport
from aion_brain.contracts.freeze import FreezeGateRunRequest
from aion_brain.contracts.versioning import FeatureRegistryEntry, VersionManifest


def test_version_manifest_rejects_secret_like_metadata() -> None:
    with pytest.raises(ValidationError):
        VersionManifest(
            version_manifest_id="manifest-1",
            version="0.1.0",
            release_channel="alpha",
            status="active",
            api_version="v1",
            sdk_version="0.1.0",
            schema_version="0.1.0",
            contract_hash="hash",
            metadata={"api_key": "never"},
            created_at=datetime.now(UTC),
        )


def test_feature_registry_rejects_domain_specific_key() -> None:
    with pytest.raises(ValidationError):
        FeatureRegistryEntry(
            feature_id="feature-1",
            feature_key="finance.trading",
            name="Bad",
            description="Domain drift",
            status="active",
            category="api",
            default_enabled=True,
            required=False,
            owner_scope=["workspace:main"],
        )


def test_feature_registry_requires_scope() -> None:
    with pytest.raises(ValidationError):
        FeatureRegistryEntry(
            feature_id="feature-1",
            feature_key="kernel.container",
            name="Kernel",
            description="Generic feature",
            status="active",
            category="kernel",
            default_enabled=True,
            required=True,
            owner_scope=[],
        )


def test_freeze_gate_request_accepts_scope_alias() -> None:
    request = FreezeGateRunRequest.model_validate({"version": "0.1.0", "scope": ["workspace:main"]})

    assert request.owner_scope == ["workspace:main"]


def test_sdk_report_rejects_secret_like_warning_payloads() -> None:
    with pytest.raises(ValidationError):
        SDKCompatibilityReport(
            report_id="sdk-1",
            api_version="v1",
            sdk_version="0.1.0",
            compatible=False,
            checked_endpoints=[],
            missing_endpoints=[],
            mismatched_contracts=[],
            warnings=[{"client_secret": "never"}],
            generated_at=datetime.now(UTC),
        )
