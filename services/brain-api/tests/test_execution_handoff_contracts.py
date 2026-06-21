"""Execution handoff contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest


def test_execution_handoff_request_rejects_external_target_system() -> None:
    with pytest.raises(ValidationError):
        ExecutionHandoffRequest(
            action_proposal_id="proposal-1",
            handoff_type="dry_run",
            target_system="external",
        )


def test_execution_handoff_request_controlled_high_risk_requires_approval() -> None:
    with pytest.raises(ValidationError):
        ExecutionHandoffRequest(
            action_proposal_id="proposal-1",
            handoff_type="command_dispatch",
            target_system="command_bus",
            mode="controlled",
            metadata={"risk_level": "high"},
        )
