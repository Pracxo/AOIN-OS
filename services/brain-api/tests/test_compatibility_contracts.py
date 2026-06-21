"""Compatibility contract validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.compatibility import (
    CompatibilityRule,
    CompatibilityScanRequest,
    InterfaceDriftFinding,
)
from tests.contract_registry_helpers import compatibility_rule, drift_finding


def test_compatibility_rule_validates_rule_type() -> None:
    assert compatibility_rule().rule_type == "no_removed_route"
    with pytest.raises(ValidationError):
        CompatibilityRule(**{**compatibility_rule().model_dump(), "rule_type": "finance"})


def test_interface_drift_finding_validates_finding_type() -> None:
    assert drift_finding().finding_type == "removed_route"
    with pytest.raises(ValidationError):
        InterfaceDriftFinding(**{**drift_finding().model_dump(), "finding_type": "finance"})


def test_compatibility_scan_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        CompatibilityScanRequest(owner_scope=[])
