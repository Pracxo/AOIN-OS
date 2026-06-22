from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.capability_awareness import CapabilityAwarenessRecord


def test_capability_awareness_record_validates_capability_type() -> None:
    with pytest.raises(ValidationError):
        CapabilityAwarenessRecord(
            awareness_id="awareness-1",
            capability_key="aion.invalid",
            capability_type="finance",
            status="active",
            availability="available",
            mode="assist",
            risk_level="low",
            requires_policy=True,
            requires_approval=False,
            requires_autonomy=False,
            dry_run_only=False,
        )


def test_capability_awareness_record_rejects_secret_metadata() -> None:
    with pytest.raises(ValidationError):
        CapabilityAwarenessRecord(
            awareness_id="awareness-1",
            capability_key="aion.kernel",
            capability_type="kernel",
            status="active",
            availability="available",
            mode="assist",
            risk_level="low",
            requires_policy=True,
            requires_approval=False,
            requires_autonomy=False,
            dry_run_only=False,
            metadata={"api_key": "hidden"},
        )
