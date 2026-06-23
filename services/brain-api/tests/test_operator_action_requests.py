from __future__ import annotations

import pytest

from tests.operator_action_fakes import DenyPolicy, OperatorActionFixture, operator_action_request


def test_request_service_creates_dry_run_request_through_policy() -> None:
    fixture = OperatorActionFixture()
    request = fixture.requests.create_request(operator_action_request())

    assert request.mode == "dry_run"
    assert request.execution_allowed is False
    assert request.external_calls_allowed is False
    assert request.activation_allowed is False
    assert request.status == "blocked"
    assert request.blocker_refs


def test_policy_deny_blocks_request_creation() -> None:
    fixture = OperatorActionFixture(policy=DenyPolicy())

    with pytest.raises(PermissionError):
        fixture.requests.create_request(operator_action_request())
