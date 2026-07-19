"""AION-177 shadow-mode resource budget tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import SHADOW_RESOURCE_BUDGETS  # noqa: E402


def test_shadow_mode_resource_budgets_match_authorization_record() -> None:
    budget = _json("examples/self-improvement/shadow-mode-resource-budget.json")
    authorization = _json("docs/self-improvement/authorization-ledger.json")

    assert budget["resource_budgets"] == SHADOW_RESOURCE_BUDGETS
    assert authorization["records"][-1]["resource_budgets"] == SHADOW_RESOURCE_BUDGETS
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
