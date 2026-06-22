"""API support models."""

from datetime import datetime
from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class AIONErrorModel(AIONSDKModel):
    code: str
    category: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    retryable: bool = False
    created_at: datetime | None = None


class AIONErrorResponseModel(AIONSDKModel):
    error: AIONErrorModel
