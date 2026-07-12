from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthDiagnosticSnapshot,
    utc_now,
)
from aion_brain.production_auth import ProductionAuthCoreService


def test_production_auth_diagnostics_are_redacted_safety_state_only() -> None:
    snapshot = ProductionAuthCoreService(ProductionAuthCoreConfig()).diagnostic_snapshot()

    assert snapshot.redacted is True
    assert snapshot.production_auth_core_implemented is True
    assert snapshot.production_auth_core_state == "implemented_disabled"
    assert snapshot.runtime_enabled is False
    assert snapshot.runtime_guard_hold_active is True
    assert snapshot.runtime_no_go_status is True
    assert snapshot.blocker_count == len(snapshot.reason_codes)
    assert snapshot.authorization_transaction_id == "AION-151-PA-0001"


def test_production_auth_diagnostics_reject_raw_request_or_material() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthDiagnosticSnapshot(
            snapshot_id="snapshot-unsafe",
            blocker_count=1,
            runtime_enabled=False,
            reason_codes=["production_auth_runtime_disabled"],
            redacted=True,
            metadata={"raw_claims": {"sub": "demo"}},
            created_at=utc_now(),
        )
