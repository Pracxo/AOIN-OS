"""Kernel diagnostic contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DiagnosticStatus = Literal["passed", "failed", "skipped", "warning"]
DiagnosticSeverity = Literal["low", "medium", "high", "critical"]


class DiagnosticCheck(BaseModel):
    """One deterministic kernel diagnostic result."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    component: str = Field(min_length=1)
    status: DiagnosticStatus
    severity: DiagnosticSeverity
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
