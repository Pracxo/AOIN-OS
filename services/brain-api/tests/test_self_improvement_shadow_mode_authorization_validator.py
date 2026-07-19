"""AION-177 shadow-mode authorization validator tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    SHADOW_APPROVED_FLAGS,
    SHADOW_AUTHORIZATION_ID,
    SHADOW_PROHIBITED_FLAGS,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
    validate_shadow_authorization_example,
)


def test_authorization_ledger_has_single_active_shadow_mode_record() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    validate_authorization_ledger(payload)
    validate_no_go(ROOT)

    active = [record for record in payload["records"] if record["authorization_active"] is True]
    assert len(active) == 1
    record = active[0]
    assert record["authorization_transaction_id"] == SHADOW_AUTHORIZATION_ID
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    for key in SHADOW_APPROVED_FLAGS:
        assert record[key] is True
    for key in SHADOW_PROHIBITED_FLAGS:
        assert record[key] is False


def test_shadow_authorization_example_matches_validator_contract() -> None:
    payload = _json("examples/self-improvement/shadow-mode-authorization.json")
    validate_shadow_authorization_example(payload)


def test_shadow_validator_rejects_runtime_enablement() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    payload["records"][-1]["shadow_mode_runtime_enabled"] = True
    with pytest.raises(GovernanceValidationError, match="shadow_mode_runtime_enabled"):
        validate_authorization_ledger(payload)


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
