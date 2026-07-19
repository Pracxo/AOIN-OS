"""CI monitoring adapter controls for approval-bound rewrites."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID

CheckStatus = Literal["pending", "success", "failure", "cancelled", "skipped"]
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class CICheckResult(BaseModel):
    """One CI check result for a rewrite pull request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    status: CheckStatus
    conclusion: str
    url: str | None = None

    @field_validator("name", "conclusion", "url")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite CI check text")
        return cleaned


class CIReport(BaseModel):
    """CI report bound to a pull request head SHA."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    pr_number: int = Field(ge=1)
    head_sha: str
    checks: tuple[CICheckResult, ...] = Field(min_length=1)
    all_green: bool
    observed_at: datetime

    @field_validator("head_sha")
    @classmethod
    def head_sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("head_sha must be a 40-character lowercase SHA-1 value")
        return value

    @model_validator(mode="after")
    def all_green_must_reflect_checks(self) -> CIReport:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("CI report must use the AION-171 rewrite authorization")
        expected = all(check.status == "success" for check in self.checks)
        if self.all_green != expected:
            raise ValueError("all_green must require every CI check to succeed")
        return self


class CIMonitorAdapter(Protocol):
    """Protocol seam for configured CI providers."""

    adapter_id: str

    def checks_for_pull_request(self, pr_number: int, head_sha: str) -> CIReport:
        """Return CI checks for one pull request head."""


class DisabledCIMonitorAdapter:
    """Fail-closed default; production CI polling is disabled."""

    adapter_id = "disabled-ci-monitor-adapter"

    def checks_for_pull_request(self, pr_number: int, head_sha: str) -> CIReport:  # noqa: ARG002
        raise RuntimeError("self-improvement CI monitoring is disabled")


class DeterministicTestCIMonitorAdapter:
    """Deterministic CI adapter for focused tests."""

    adapter_id = "deterministic-test-ci-monitor-adapter"

    def __init__(self, *, success: bool = True, proposal_id: str = "proposal-172") -> None:
        self._success = success
        self._proposal_id = proposal_id

    def checks_for_pull_request(self, pr_number: int, head_sha: str) -> CIReport:
        status: CheckStatus = "success" if self._success else "failure"
        checks = (
            CICheckResult(name="brain-api-quality", status=status, conclusion=status),
            CICheckResult(name="repository-hygiene", status=status, conclusion=status),
        )
        return CIReport(
            proposal_id=self._proposal_id,
            pr_number=pr_number,
            head_sha=head_sha,
            checks=checks,
            all_green=self._success,
            observed_at=utc_now(),
        )


class CIMonitor:
    """Read CI status through an injected adapter."""

    def __init__(self, adapter: CIMonitorAdapter | None = None) -> None:
        self._adapter = adapter or DisabledCIMonitorAdapter()

    def checks_for_pull_request(self, pr_number: int, head_sha: str) -> CIReport:
        """Return CI checks for a pull request through the adapter."""

        return self._adapter.checks_for_pull_request(pr_number, head_sha)


__all__ = [
    "CICheckResult",
    "CIMonitor",
    "CIMonitorAdapter",
    "CIReport",
    "CheckStatus",
    "DeterministicTestCIMonitorAdapter",
    "DisabledCIMonitorAdapter",
]
