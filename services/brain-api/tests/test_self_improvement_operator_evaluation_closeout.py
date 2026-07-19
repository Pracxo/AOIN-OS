"""AION-OE-001 closeout evidence tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION_176_FEATURE_COMMIT,
    AION_176_MERGE_COMMIT,
    OPERATOR_EVALUATION_DECISION,
    OPERATOR_EVALUATION_ID,
    validate_operator_evaluation_closeout,
)


def test_operator_evaluation_closeout_records_pass_decision_without_activation() -> None:
    payload = _json("examples/self-improvement/operator-evaluation-closeout.json")
    validate_operator_evaluation_closeout(payload)

    assert payload["evaluation_id"] == OPERATOR_EVALUATION_ID
    assert payload["decision"] == OPERATOR_EVALUATION_DECISION
    assert payload["base_commit"] == AION_176_MERGE_COMMIT
    assert payload["aion_176"]["feature_commit"] == AION_176_FEATURE_COMMIT
    assert payload["aion_176"]["merge_commit"] == AION_176_MERGE_COMMIT
    assert payload["new_implementation_authorization_created"] is False
    assert payload["runtime_activation_created"] is False
    assert payload["source_rewrite_enabled"] is False
    assert payload["deployment_enabled"] is False
    assert payload["model_weight_training_enabled"] is False


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
