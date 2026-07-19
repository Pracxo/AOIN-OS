"""Rollback metadata for approved self-improvement rewrites."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class RollbackMetadata(BaseModel):
    """Exact rollback metadata recorded before and after merge."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    approved_commit_sha: str
    rollback_commit_sha: str
    deployment_scope: str = Field(min_length=1)
    rollback_command_ref: str = Field(min_length=1)
    rollback_test_refs: tuple[str, ...] = Field(min_length=1)
    created_at: datetime
    merge_commit_sha: str | None = None
    recorded_after_merge: bool = False

    @field_validator("proposal_id", "deployment_scope", "rollback_command_ref")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite rollback metadata text")
        return cleaned

    @field_validator("approved_commit_sha", "rollback_commit_sha", "merge_commit_sha")
    @classmethod
    def sha_must_be_exact(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
        return value

    @field_validator("rollback_test_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for ref in value:
            reject_hidden_or_secret_text(ref, "rewrite rollback test reference")
        return value

    @model_validator(mode="after")
    def metadata_must_bind_a_real_rollback_commit(self) -> RollbackMetadata:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("rollback metadata must use the AION-171 rewrite authorization")
        if self.rollback_commit_sha == self.approved_commit_sha:
            raise ValueError("rollback commit must differ from the approved candidate commit")
        if self.recorded_after_merge and self.merge_commit_sha is None:
            raise ValueError("post-merge rollback metadata must include merge_commit_sha")
        return self

    def record_merge(self, merge_commit_sha: str) -> RollbackMetadata:
        """Return rollback metadata enriched with the observed merge commit."""

        return self.model_copy(
            update={
                "merge_commit_sha": merge_commit_sha,
                "recorded_after_merge": True,
            }
        )


def rollback_metadata_for_candidate(
    *,
    proposal_id: str,
    approved_commit_sha: str,
    rollback_commit_sha: str,
    deployment_scope: str,
    rollback_test_refs: tuple[str, ...],
) -> RollbackMetadata:
    """Build rollback metadata before PR creation."""

    return RollbackMetadata(
        proposal_id=proposal_id,
        approved_commit_sha=approved_commit_sha,
        rollback_commit_sha=rollback_commit_sha,
        deployment_scope=deployment_scope,
        rollback_command_ref="git revert --no-commit <approved_commit_sha>",
        rollback_test_refs=rollback_test_refs,
        created_at=utc_now(),
    )


__all__ = [
    "RollbackMetadata",
    "rollback_metadata_for_candidate",
]
