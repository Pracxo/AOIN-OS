"""Isolated Git worktree creation for approval-bound rewrites."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now

REWRITE_AUTHORIZATION_TRANSACTION_ID = "AION-171-SI-0004"
REWRITE_IMPLEMENTATION_TASK = "AION-172"
REWRITE_AUTHORIZATION_SCOPE = "approval-bound-isolated-source-rewrite-and-pr-control"

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class WorktreeRequest(BaseModel):
    """Request to create an isolated worktree from an exact base commit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    repo_path: Path
    worktree_path: Path
    base_sha: str
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("proposal_id")
    @classmethod
    def proposal_id_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite worktree proposal id")
        return cleaned

    @field_validator("base_sha")
    @classmethod
    def base_sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("base_sha must be a 40-character lowercase SHA-1 value")
        return value

    @model_validator(mode="after")
    def worktree_request_must_be_isolated_and_approved(self) -> WorktreeRequest:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("worktree request must use the AION-171 rewrite authorization")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError(
                "worktree request must not mutate source, Git branches, PRs, or runtime"
            )
        repo = self.repo_path.resolve()
        worktree = self.worktree_path.resolve()
        if repo == worktree:
            raise ValueError("worktree path must be isolated from the source repository")
        if repo in worktree.parents:
            raise ValueError("worktree path must not be nested inside the source repository")
        return self


class WorktreeResult(BaseModel):
    """Result of creating an isolated worktree."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    repo_path: Path
    worktree_path: Path
    base_sha: str
    head_sha: str
    isolated: bool
    source_repo_modified: bool = False
    task_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator("base_sha", "head_sha")
    @classmethod
    def sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
        return value

    @model_validator(mode="after")
    def result_must_match_requested_boundary(self) -> WorktreeResult:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("worktree result must use the AION-171 rewrite authorization")
        if self.base_sha != self.head_sha:
            raise ValueError("worktree HEAD must equal the requested base SHA")
        if any(
            (
                self.source_repo_modified,
                self.task_branch_created,
                self.pr_created,
                self.runtime_effect,
            )
        ):
            raise ValueError(
                "isolated worktree creation cannot mutate source, branch, PR, or runtime state"
            )
        return self


class GitCommandRunner(Protocol):
    """Protocol seam for explicitly supplied local Git command execution."""

    def run_git(self, cwd: Path, args: Sequence[str]) -> str:
        """Run a Git command in a caller-supplied repository."""


class DisabledGitCommandRunner:
    """Fail-closed default; no local Git command execution is configured."""

    def run_git(self, cwd: Path, args: Sequence[str]) -> str:  # noqa: ARG002
        raise RuntimeError("self-improvement local Git command execution is disabled")


class WorktreeManager:
    """Create detached Git worktrees through an explicitly supplied runner."""

    def __init__(self, runner: GitCommandRunner | None = None) -> None:
        self._runner = runner or DisabledGitCommandRunner()

    def create(self, request: WorktreeRequest) -> WorktreeResult:
        """Create a detached worktree from an exact base SHA."""

        repo_path = request.repo_path.resolve()
        worktree_path = request.worktree_path.resolve()
        if not (repo_path / ".git").exists():
            raise ValueError("repo_path must point to a Git repository")
        if worktree_path.exists() and any(worktree_path.iterdir()):
            raise ValueError("worktree_path must be absent or empty")

        self._runner.run_git(repo_path, ("rev-parse", "--verify", "--quiet", request.base_sha))
        self._runner.run_git(
            repo_path,
            ("worktree", "add", "--detach", str(worktree_path), request.base_sha),
        )
        head_sha = self._runner.run_git(worktree_path, ("rev-parse", "HEAD"))
        return WorktreeResult(
            proposal_id=request.proposal_id,
            repo_path=repo_path,
            worktree_path=worktree_path,
            base_sha=request.base_sha,
            head_sha=head_sha,
            isolated=repo_path != worktree_path and repo_path not in worktree_path.parents,
            created_at=utc_now(),
        )

    def remove(self, repo_path: Path, worktree_path: Path) -> None:
        """Remove an isolated worktree registered with Git."""

        self._runner.run_git(
            repo_path.resolve(), ("worktree", "remove", "--force", str(worktree_path.resolve()))
        )


__all__ = [
    "REWRITE_AUTHORIZATION_SCOPE",
    "REWRITE_AUTHORIZATION_TRANSACTION_ID",
    "REWRITE_IMPLEMENTATION_TASK",
    "DisabledGitCommandRunner",
    "GitCommandRunner",
    "WorktreeManager",
    "WorktreeRequest",
    "WorktreeResult",
]
