"""Output governance service tests."""

from __future__ import annotations

import pytest

from aion_brain.contracts.model_outputs import ModelOutputCreateRequest
from aion_brain.contracts.output_governance import OutputGovernanceRequest
from tests.model_outputs_fakes import DenyPolicy, governance_service


def test_receive_output_redacts_and_hashes_raw_output() -> None:
    service, repo, _, telemetry = governance_service()

    output = service.receive_output(
        ModelOutputCreateRequest(
            trace_id="trace-1",
            raw_output="password: swordfish",
            output_type="text",
            owner_scope=["workspace:main"],
        )
    )

    stored = repo.get_output(output.model_output_id)

    assert stored is not None
    assert "swordfish" not in stored.redacted_output
    assert stored.raw_output_hash
    assert any(
        getattr(event, "event_type", None) == "model_output_received" for event in telemetry.events
    )


def test_governance_creates_segments_candidate_and_blocks_tool_intent() -> None:
    service, repo, _, _ = governance_service()
    output = service.receive_output(
        ModelOutputCreateRequest(
            trace_id="trace-1",
            raw_output='Answer safely.\ntool: echo {"value":"ok"}',
            output_type="mixed",
            owner_scope=["workspace:main"],
        )
    )

    run = service.govern(
        OutputGovernanceRequest(
            trace_id="trace-1",
            model_output_id=output.model_output_id,
            owner_scope=["workspace:main"],
        )
    )

    assert run.blocked is True
    assert run.parsed_segments
    assert run.response_candidates
    assert run.tool_intents[0].status == "blocked"
    assert repo.get_output(output.model_output_id).status == "blocked"  # type: ignore[union-attr]


def test_governance_policy_deny_blocks_receive() -> None:
    service, _, _, _ = governance_service(policy=DenyPolicy("model_output.create"))

    with pytest.raises(PermissionError):
        service.receive_output(
            ModelOutputCreateRequest(
                raw_output="safe",
                output_type="text",
                owner_scope=["workspace:main"],
            )
        )
