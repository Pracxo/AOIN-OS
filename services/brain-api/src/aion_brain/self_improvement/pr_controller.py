"""Pull-request adapter controls for approval-bound rewrites."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID

ApprovalStatus = Literal["pending", "approved", "rejected", "invalidated"]
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RewriteApprovalBinding(BaseModel):
    """Exact human approval binding for a rewrite candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    approval_status: ApprovalStatus
    approved_commit_sha: str
    approved_diff_hash: str
    approved_benchmark_fingerprint: str
    approved_rollback_commit: str
    approved_deployment_scope: str = Field(min_length=1)
    current_commit_sha: str
    current_diff_hash: str
    current_benchmark_fingerprint: str
    current_rollback_commit: str
    approver_actor_ids: tuple[str, ...] = Field(min_length=1)
    created_at: datetime

    @field_validator("proposal_id", "approved_deployment_scope")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite approval binding text")
        return cleaned

    @field_validator(
        "approved_commit_sha",
        "approved_rollback_commit",
        "current_commit_sha",
        "current_rollback_commit",
    )
    @classmethod
    def git_sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
        return value

    @field_validator(
        "approved_diff_hash",
        "approved_benchmark_fingerprint",
        "current_diff_hash",
        "current_benchmark_fingerprint",
    )
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("hash must be a 64-character lowercase SHA-256 value")
        return value

    @field_validator("approver_actor_ids")
    @classmethod
    def approvers_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for actor_id in value:
            reject_hidden_or_secret_text(actor_id, "rewrite approver actor id")
        return value

    @model_validator(mode="after")
    def approval_must_bind_exact_current_evidence(self) -> RewriteApprovalBinding:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("rewrite approval must use the AION-171 authorization")
        exact = (
            self.approved_commit_sha == self.current_commit_sha
            and self.approved_diff_hash == self.current_diff_hash
            and self.approved_benchmark_fingerprint == self.current_benchmark_fingerprint
            and self.approved_rollback_commit == self.current_rollback_commit
        )
        if self.approval_status == "approved" and not exact:
            raise ValueError("approved rewrite binding must match current evidence exactly")
        return self

    @property
    def is_valid(self) -> bool:
        """Return whether the approval is currently exact and approved."""

        return self.approval_status == "approved" and (
            self.approved_commit_sha == self.current_commit_sha
            and self.approved_diff_hash == self.current_diff_hash
            and self.approved_benchmark_fingerprint == self.current_benchmark_fingerprint
            and self.approved_rollback_commit == self.current_rollback_commit
        )

    def invalidate_after_change(
        self,
        *,
        current_commit_sha: str,
        current_diff_hash: str,
        current_benchmark_fingerprint: str,
        current_rollback_commit: str,
    ) -> RewriteApprovalBinding:
        """Return an invalidated binding if any approved evidence changed."""

        status: ApprovalStatus = "approved"
        if (
            current_commit_sha != self.approved_commit_sha
            or current_diff_hash != self.approved_diff_hash
            or current_benchmark_fingerprint != self.approved_benchmark_fingerprint
            or current_rollback_commit != self.approved_rollback_commit
        ):
            status = "invalidated"
        return self.model_copy(
            update={
                "approval_status": status,
                "current_commit_sha": current_commit_sha,
                "current_diff_hash": current_diff_hash,
                "current_benchmark_fingerprint": current_benchmark_fingerprint,
                "current_rollback_commit": current_rollback_commit,
            }
        )


class PullRequestCreateRequest(BaseModel):
    """Request to create a pull request after valid exact approval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1)
    branch_name: str = Field(min_length=1)
    base_branch: str = "main"
    head_sha: str
    diff_hash: str
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)

    @field_validator("head_sha")
    @classmethod
    def head_sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("head_sha must be a 40-character lowercase SHA-1 value")
        return value

    @field_validator("diff_hash")
    @classmethod
    def diff_hash_must_be_sha256(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("diff_hash must be a 64-character lowercase SHA-256 value")
        return value

    @model_validator(mode="after")
    def request_must_not_target_direct_main_head(self) -> PullRequestCreateRequest:
        if self.branch_name in {"main", "master"}:
            raise ValueError("pull request head branch cannot be main")
        if self.base_branch != "main":
            raise ValueError("rewrite pull requests must target main through review")
        reject_hidden_or_secret_text(self.title, "rewrite pull request title")
        reject_hidden_or_secret_text(self.body, "rewrite pull request body")
        return self


class PullRequestRecord(BaseModel):
    """Adapter-neutral pull request record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pr_number: int = Field(ge=1)
    url: str = Field(min_length=1)
    branch_name: str = Field(min_length=1)
    base_branch: str
    head_sha: str
    diff_hash: str
    created_at: datetime


class PullRequestAdapter(Protocol):
    """Protocol seam for configured pull-request providers."""

    adapter_id: str

    def create_pull_request(self, request: PullRequestCreateRequest) -> PullRequestRecord:
        """Create a pull request."""


class DisabledPullRequestAdapter:
    """Fail-closed default; production PR creation is disabled."""

    adapter_id = "disabled-pull-request-adapter"

    def create_pull_request(self, request: PullRequestCreateRequest) -> PullRequestRecord:  # noqa: ARG002
        raise RuntimeError("self-improvement pull request creation is disabled")


class DeterministicTestPullRequestAdapter:
    """Deterministic test double for focused controller tests."""

    adapter_id = "deterministic-test-pull-request-adapter"

    def create_pull_request(self, request: PullRequestCreateRequest) -> PullRequestRecord:
        return PullRequestRecord(
            pr_number=172,
            url=f"https://example.invalid/pull/{request.proposal_id}",
            branch_name=request.branch_name,
            base_branch=request.base_branch,
            head_sha=request.head_sha,
            diff_hash=request.diff_hash,
            created_at=utc_now(),
        )


class PullRequestController:
    """Create PRs only after valid exact approval exists."""

    def __init__(self, adapter: PullRequestAdapter | None = None) -> None:
        self._adapter = adapter or DisabledPullRequestAdapter()

    def create_pull_request(
        self,
        *,
        approval: RewriteApprovalBinding,
        request: PullRequestCreateRequest,
    ) -> PullRequestRecord:
        """Create a pull request only for the exact approved commit and diff."""

        if not approval.is_valid:
            raise ValueError("valid exact approval is required before pull request creation")
        if approval.proposal_id != request.proposal_id:
            raise ValueError("pull request must match the approved proposal")
        if approval.approved_commit_sha != request.head_sha:
            raise ValueError("pull request head SHA must equal the approved commit")
        if approval.approved_diff_hash != request.diff_hash:
            raise ValueError("pull request diff hash must equal the approved diff")
        return self._adapter.create_pull_request(request)


__all__ = [
    "ApprovalStatus",
    "DeterministicTestPullRequestAdapter",
    "DisabledPullRequestAdapter",
    "PullRequestAdapter",
    "PullRequestController",
    "PullRequestCreateRequest",
    "PullRequestRecord",
    "RewriteApprovalBinding",
]
