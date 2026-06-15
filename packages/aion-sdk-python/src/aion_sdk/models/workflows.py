"""Workflow models."""

from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class WorkflowDefinitionModel(AIONSDKModel):
    workflow_id: str
    name: str
    status: str
    owner_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunModel(AIONSDKModel):
    workflow_run_id: str
    workflow_id: str
    status: str
    owner_scope: list[str] = Field(default_factory=list)

