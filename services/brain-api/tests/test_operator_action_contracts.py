from __future__ import annotations

import pytest

from aion_brain.contracts.operator_actions import (
    OperatorActionPreview,
    OperatorActionRequest,
    OperatorActionReview,
)


def test_operator_action_request_mode_and_flags_are_locked() -> None:
    request = OperatorActionRequest(
        operator_action_request_id="request-1",
        action_key="operator.review",
        action_type="generic",
        target_type="generic",
        status="requested",
        mode="dry_run",
        risk_level="medium",
        owner_scope=["workspace:main"],
        request_payload_hash="hash",
        execution_allowed=False,
        external_calls_allowed=False,
        activation_allowed=False,
    )

    assert request.mode == "dry_run"
    assert request.execution_allowed is False
    assert request.external_calls_allowed is False
    assert request.activation_allowed is False


def test_operator_action_request_rejects_non_dotted_action_key() -> None:
    with pytest.raises(ValueError):
        OperatorActionRequest(
            operator_action_request_id="request-1",
            action_key="OperatorReview",
            action_type="generic",
            target_type="generic",
            status="requested",
            mode="dry_run",
            risk_level="medium",
            owner_scope=["workspace:main"],
            request_payload_hash="hash",
        )


def test_operator_action_preview_and_review_never_execute() -> None:
    preview = OperatorActionPreview(
        operator_action_preview_id="preview-1",
        operator_action_request_id="request-1",
        status="blocked",
        preview_type="dry_run",
        owner_scope=["workspace:main"],
        would_execute=False,
        execution_allowed=False,
        external_calls_allowed=False,
        activation_allowed=False,
    )
    review = OperatorActionReview(
        operator_action_review_id="review-1",
        operator_action_request_id="request-1",
        status="completed",
        decision="approve_preview_only",
        reason="reviewed",
        approval_present=True,
        execution_allowed=False,
    )

    assert preview.would_execute is False
    assert preview.execution_allowed is False
    assert review.execution_allowed is False


def test_operator_action_preview_rejects_execution_enabled() -> None:
    with pytest.raises(ValueError):
        OperatorActionPreview(
            operator_action_preview_id="preview-1",
            operator_action_request_id="request-1",
            status="blocked",
            preview_type="dry_run",
            owner_scope=["workspace:main"],
            would_execute=True,
        )
