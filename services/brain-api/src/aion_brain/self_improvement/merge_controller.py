"""Merge controller for exact approved rewrite commits."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.ci_monitor import CIReport
from aion_brain.self_improvement.pr_controller import PullRequestRecord, RewriteApprovalBinding
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID

MergeStatus = Literal["merged", "blocked"]
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class MergeRequest(BaseModel):
    """Request to merge a pull request after all approval gates pass."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    pr_number: int = Field(ge=1)
    head_sha: str
    approved_commit_sha: str
    benchmark_fingerprint: str
    approved_benchmark_fingerprint: str
    base_branch: str = "main"
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("proposal_id")
    @classmethod
    def proposal_id_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite merge proposal id")
        return cleaned

    @field_validator("head_sha", "approved_commit_sha")
    @classmethod
    def sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
        return value

    @model_validator(mode="after")
    def request_must_bind_exact_head_and_main_base(self) -> MergeRequest:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("merge request must use the AION-171 rewrite authorization")
        if self.base_branch != "main":
            raise ValueError("rewrite merge target must be main through PR controls")
        if self.head_sha != self.approved_commit_sha:
            raise ValueError("merge request head must equal approved commit")
        if self.benchmark_fingerprint != self.approved_benchmark_fingerprint:
            raise ValueError("merge request benchmark evidence must equal approved evidence")
        return self


class MergeResult(BaseModel):
    """Adapter-neutral merge result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str
    pr_number: int
    status: MergeStatus
    merged_commit_sha: str | None = None
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    merged_at: datetime | None = None


class MergeAdapter(Protocol):
    """Protocol seam for configured merge providers."""

    adapter_id: str

    def merge_pull_request(self, request: MergeRequest) -> MergeResult:
        """Merge one pull request."""


class DisabledMergeAdapter:
    """Fail-closed default; production PR merge is disabled."""

    adapter_id = "disabled-merge-adapter"

    def merge_pull_request(self, request: MergeRequest) -> MergeResult:  # noqa: ARG002
        raise RuntimeError("self-improvement pull request merge is disabled")


class DeterministicTestMergeAdapter:
    """Deterministic merge adapter for focused tests."""

    adapter_id = "deterministic-test-merge-adapter"

    def merge_pull_request(self, request: MergeRequest) -> MergeResult:
        return MergeResult(
            proposal_id=request.proposal_id,
            pr_number=request.pr_number,
            status="merged",
            merged_commit_sha=request.head_sha,
            reason_codes=("exact_approved_commit_merged",),
            merged_at=utc_now(),
        )


class MergeController:
    """Merge only when approval, PR head, CI, and benchmark evidence still match."""

    def __init__(self, adapter: MergeAdapter | None = None) -> None:
        self._adapter = adapter or DisabledMergeAdapter()

    def merge_when_safe(
        self,
        *,
        approval: RewriteApprovalBinding,
        pull_request: PullRequestRecord,
        ci_report: CIReport,
        current_head_sha: str,
        current_benchmark_fingerprint: str,
    ) -> MergeResult:
        """Merge through the adapter only after exact safety gates pass."""

        if not approval.is_valid:
            return _blocked(pull_request, "approval_invalid")
        if not ci_report.all_green:
            return _blocked(pull_request, "ci_not_green")
        if pull_request.head_sha != current_head_sha:
            return _blocked(pull_request, "pull_request_head_changed")
        if current_head_sha != approval.approved_commit_sha:
            return _blocked(pull_request, "head_sha_not_approved")
        if current_benchmark_fingerprint != approval.approved_benchmark_fingerprint:
            return _blocked(pull_request, "benchmark_evidence_changed")
        request = MergeRequest(
            proposal_id=approval.proposal_id,
            pr_number=pull_request.pr_number,
            head_sha=current_head_sha,
            approved_commit_sha=approval.approved_commit_sha,
            benchmark_fingerprint=current_benchmark_fingerprint,
            approved_benchmark_fingerprint=approval.approved_benchmark_fingerprint,
            base_branch=pull_request.base_branch,
        )
        return self._adapter.merge_pull_request(request)


def _blocked(pull_request: PullRequestRecord, reason: str) -> MergeResult:
    return MergeResult(
        proposal_id="blocked",
        pr_number=pull_request.pr_number,
        status="blocked",
        reason_codes=(reason,),
    )


__all__ = [
    "DeterministicTestMergeAdapter",
    "DisabledMergeAdapter",
    "MergeAdapter",
    "MergeController",
    "MergeRequest",
    "MergeResult",
    "MergeStatus",
]
