"""Approval models."""

from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class ApprovalRequestModel(AIONSDKModel):
    approval_request_id: str
    status: str
    approval_scope: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecisionModel(AIONSDKModel):
    approval_request_id: str
    decision: str
    decided_by: str | None = None
