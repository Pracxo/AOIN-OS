"""Model output contract tests."""

from __future__ import annotations

import pytest

from aion_brain.contracts.model_outputs import (
    ModelOutputCreateRequest,
    ModelOutputRecord,
    ToolIntentCandidate,
)
from aion_brain.contracts.output_governance import OutputGovernanceRequest


def test_model_output_create_rejects_empty_non_empty_output() -> None:
    with pytest.raises(ValueError):
        ModelOutputCreateRequest(
            raw_output="",
            output_type="text",
            owner_scope=["workspace:main"],
        )


def test_model_output_record_rejects_hidden_marker_in_redacted_output() -> None:
    with pytest.raises(ValueError):
        ModelOutputRecord(
            model_output_id="output-1",
            status="received",
            output_type="text",
            raw_output_hash="hash",
            redacted_output="hidden reasoning: unsafe",
            output_redacted=False,
            token_estimate=1,
            char_count=24,
        )


def test_tool_intent_rejects_secret_like_arguments() -> None:
    with pytest.raises(ValueError):
        ToolIntentCandidate(
            tool_intent_id="tool-intent-1",
            status="blocked",
            intent_type="tool_call",
            arguments_redacted={"password": "redacted"},
            risk_level="high",
            blocked_reason="tool_intent_execution_disabled",
        )


def test_output_governance_request_requires_scope() -> None:
    with pytest.raises(ValueError):
        OutputGovernanceRequest(model_output_id="output-1", owner_scope=[])
