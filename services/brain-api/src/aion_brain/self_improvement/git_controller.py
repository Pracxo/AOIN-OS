"""Local Git controls for approval-bound rewrite candidates."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.worktree import (
    REWRITE_AUTHORIZATION_TRANSACTION_ID,
    DisabledGitCommandRunner,
    GitCommandRunner,
)

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master", "refs/heads/main"}


class GitSnapshot(BaseModel):
    """Current Git commit and tree observed in an isolated worktree."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commit_sha: str
    tree_hash: str
    branch_name: str | None = None
    observed_at: datetime

    @field_validator("commit_sha", "tree_hash")
    @classmethod
    def sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
        return value


class TaskBranchRequest(BaseModel):
    """Request to create a local task branch after approval is valid."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    repo_path: Path
    branch_name: str = Field(min_length=1)
    start_sha: str
    approved_commit_sha: str
    approved_diff_hash: str
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("branch_name")
    @classmethod
    def branch_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite branch name")
        if cleaned in _PROTECTED_BRANCHES or cleaned.endswith("/main"):
            raise ValueError("rewrite controller must not create or push main branches")
        if not cleaned.startswith("phase/"):
            raise ValueError("rewrite task branch must use the phase/ namespace")
        return cleaned

    @field_validator("start_sha", "approved_commit_sha")
    @classmethod
    def sha_must_be_exact(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
        return value

    @model_validator(mode="after")
    def request_must_be_approval_bound(self) -> TaskBranchRequest:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("task branch request must use the AION-171 rewrite authorization")
        if self.start_sha != self.approved_commit_sha:
            raise ValueError("task branch start SHA must equal the approved commit SHA")
        if not self.approved_diff_hash:
            raise ValueError("task branch request must bind an approved diff hash")
        return self


class GitController:
    """Run local Git commands only through an explicitly supplied runner."""

    def __init__(self, runner: GitCommandRunner | None = None) -> None:
        self._runner = runner or DisabledGitCommandRunner()

    def snapshot(self, repo_path: Path) -> GitSnapshot:
        """Return the current commit and tree hash."""

        repo = repo_path.resolve()
        commit_sha = self._runner.run_git(repo, ("rev-parse", "HEAD"))
        tree_hash = self._runner.run_git(repo, ("rev-parse", "HEAD^{tree}"))
        branch_name = self._runner.run_git(repo, ("rev-parse", "--abbrev-ref", "HEAD"))
        return GitSnapshot(
            commit_sha=commit_sha,
            tree_hash=tree_hash,
            branch_name=None if branch_name == "HEAD" else branch_name,
            observed_at=utc_now(),
        )

    def create_task_branch(self, request: TaskBranchRequest) -> GitSnapshot:
        """Create a local task branch from the exact approved commit."""

        repo = request.repo_path.resolve()
        self._runner.run_git(
            repo,
            ("rev-parse", "--verify", "--quiet", request.approved_commit_sha),
        )
        self._runner.run_git(
            repo,
            ("switch", "-c", request.branch_name, request.approved_commit_sha),
        )
        snapshot = self.snapshot(repo)
        if snapshot.branch_name != request.branch_name:
            raise ValueError("created branch did not match requested branch")
        return snapshot

    def reject_direct_main_push(self, refspec: str) -> None:
        """Fail closed for direct pushes to main."""

        target = refspec.strip()
        if target in _PROTECTED_BRANCHES or target.endswith(":main") or target.endswith("/main"):
            raise ValueError("rewrite controller must never push directly to main")


__all__ = [
    "GitController",
    "GitSnapshot",
    "TaskBranchRequest",
]
