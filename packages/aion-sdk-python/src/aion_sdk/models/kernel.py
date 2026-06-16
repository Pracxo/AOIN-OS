"""Kernel models."""

from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class KernelStatusModel(AIONSDKModel):
    service: str | None = None
    status: str
    version: str | None = None
    adapters: dict[str, Any] = Field(default_factory=dict)


class KernelSelfTestResultModel(AIONSDKModel):
    status: str
    checks: list[dict[str, Any]] = Field(default_factory=list)
