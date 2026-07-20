"""AION-177 shadow-mode resource budget tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    SHADOW_AUTHORIZATION_ID,
    SHADOW_RESOURCE_BUDGETS,
)


def test_shadow_mode_resource_budgets_match_authorization_record() -> None:
    budget = _json("examples/self-improvement/shadow-mode-resource-budget.json")
    authorization = _json("docs/self-improvement/authorization-ledger.json")
    shadow_record = _record(authorization["records"], SHADOW_AUTHORIZATION_ID)

    assert budget["resource_budgets"] == SHADOW_RESOURCE_BUDGETS
    assert shadow_record["resource_budgets"] == SHADOW_RESOURCE_BUDGETS
    assert budget["resource_budgets"]["network_calls"] == 0
    assert budget["resource_budgets"]["git_operations"] == 0
    assert budget["resource_budgets"]["source_mutations"] == 0
    assert budget["resource_budgets"]["real_pull_requests"] == 0
    assert budget["resource_budgets"]["runtime_promotions"] == 0


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _record(records: list[dict[str, Any]], authorization_id: str) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record["authorization_transaction_id"] == authorization_id
    ]
    assert len(matches) == 1
    return matches[0]
