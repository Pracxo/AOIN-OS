"""AION-177 shadow-mode threat model tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    SHADOW_ALLOWED_OUTPUT_FLAGS,
    SHADOW_ALLOWED_REVIEW_STATES,
    SHADOW_FORBIDDEN_REVIEW_STATES,
)


def test_threat_model_requires_fail_closed_runtime_and_data_controls() -> None:
    text = (ROOT / "docs/self-improvement/shadow-mode-threat-model.md").read_text()
    for phrase in (
        "Fail closed",
        "zero budgets for source changes",
        "Redact evidence",
        "operator-visible review item",
        "Preserve immutable `aion-v0.1.0`",
    ):
        assert phrase in text


def test_output_boundary_stays_advisory_only() -> None:
    output = _json("examples/self-improvement/shadow-mode-output-boundary.json")
    review = _json("examples/self-improvement/shadow-mode-operator-review-item.json")

    assert tuple(output["allowed_outputs"]) == SHADOW_ALLOWED_OUTPUT_FLAGS
    assert tuple(output["allowed_review_states"]) == SHADOW_ALLOWED_REVIEW_STATES
    assert tuple(output["forbidden_review_states"]) == SHADOW_FORBIDDEN_REVIEW_STATES
    assert review["review_state"] == "operator_review_pending"
    assert review["source_modified"] is False
    assert review["git_mutated"] is False
    assert review["pull_request_created"] is False
    assert review["approval_created"] is False
    assert review["merged"] is False
    assert review["runtime_effect"] is False


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
