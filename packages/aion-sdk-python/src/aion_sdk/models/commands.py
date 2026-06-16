"""Command Bus models."""

from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class BrainCommandModel(AIONSDKModel):
    command_id: str
    command_type: str
    status: str
    owner_scope: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class CommandDispatchResultModel(AIONSDKModel):
    accepted: bool
    command_id: str
    status: str
    idempotency_key: str | None = None
