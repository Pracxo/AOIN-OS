"""Reasoning models."""

from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class ReasoningResultModel(AIONSDKModel):
    reasoning_id: str
    trace_id: str | None = None
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
