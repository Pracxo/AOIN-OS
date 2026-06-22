"""Security baseline contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.security_baseline import (
    AttackSurfaceRecord,
    HardeningGateRequest,
    SecretScanFinding,
    SecurityControlRecord,
    SecurityScanRequest,
    ThreatModelRecord,
)
from tests.security_fakes import SCOPE


def test_threat_model_record_validates_category() -> None:
    with pytest.raises(ValidationError):
        ThreatModelRecord(
            threat_model_id="threat-1",
            name="Generic threat",
            description="Generic local threat",
            status="open",
            category="domain",
            asset_type="api",
            threat_type="generic",
            severity="medium",
            likelihood="medium",
            impact="medium",
            residual_risk="medium",
            owner_scope=SCOPE,
        )


def test_threat_model_record_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        ThreatModelRecord(
            threat_model_id="threat-1",
            name="Generic threat",
            description="Generic local threat",
            status="open",
            category="api",
            asset_type="api",
            threat_type="generic",
            severity="medium",
            likelihood="medium",
            impact="medium",
            residual_risk="medium",
            owner_scope=[],
        )


def test_attack_surface_record_validates_surface_type() -> None:
    with pytest.raises(ValidationError):
        AttackSurfaceRecord(
            attack_surface_id="surface-1",
            surface_type="domain",
            name="Surface",
            description="Generic surface",
            exposure_level="local",
            risk_level="medium",
            owner_scope=SCOPE,
        )


def test_security_control_record_validates_control_key() -> None:
    with pytest.raises(ValidationError):
        SecurityControlRecord(
            security_control_id="control-1",
            control_key="Not Dotted",
            name="Control",
            description="Generic control",
            category="api",
            status="implemented",
            required=True,
        )


def test_secret_scan_finding_redacted_match_cannot_contain_raw_secret() -> None:
    with pytest.raises(ValidationError):
        SecretScanFinding(
            finding_id="finding-1",
            scan_id="scan-1",
            file_path="example.py",
            finding_type="api_key_like",
            severity="high",
            redacted_match="sk-abcdefghijklmnopqrstuvwxyz",
        )


def test_security_scan_request_rejects_unsafe_path() -> None:
    with pytest.raises(ValidationError):
        SecurityScanRequest(scan_type="secrets", owner_scope=SCOPE, paths=["../escape"])


def test_hardening_gate_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        HardeningGateRequest(owner_scope=[])
