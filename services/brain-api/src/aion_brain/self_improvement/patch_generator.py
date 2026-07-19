"""Patch generator protocol for approval-bound self-improvement rewrites."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.diff_hash import canonical_diff_hash
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID


class PatchRequest(BaseModel):
    """Request for a bounded patch artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    base_sha: str
    allowed_paths: tuple[str, ...] = Field(min_length=1)
    prohibited_paths: tuple[str, ...] = Field(default_factory=tuple)
    regression_test_path: str = Field(min_length=1)
    target_paths: tuple[str, ...] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("proposal_id", "base_sha", "regression_test_path")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip().replace("\\", "/")
        reject_hidden_or_secret_text(cleaned, "rewrite patch request text")
        return cleaned

    @field_validator("allowed_paths", "prohibited_paths", "target_paths")
    @classmethod
    def paths_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip().replace("\\", "/") for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "rewrite patch path")
        return cleaned

    @model_validator(mode="after")
    def request_must_be_bounded(self) -> PatchRequest:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("patch request must use the AION-171 rewrite authorization")
        if set(self.allowed_paths) & set(self.prohibited_paths):
            raise ValueError("allowed and prohibited paths cannot overlap")
        if self.regression_test_path not in self.allowed_paths:
            raise ValueError("regression test path must be explicitly allowed")
        return self


class PatchArtifact(BaseModel):
    """Reviewable unified-diff artifact; generation does not apply it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    generator_id: str = Field(min_length=1)
    unified_diff: str = Field(min_length=1)
    changed_paths: tuple[str, ...] = Field(min_length=1)
    diff_hash: str
    generated_at: datetime
    source_applied: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False

    @field_validator("proposal_id", "generator_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite patch artifact text")
        return cleaned

    @field_validator("changed_paths")
    @classmethod
    def changed_paths_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(path.strip().replace("\\", "/").lstrip("/") for path in value)
        for path in cleaned:
            reject_hidden_or_secret_text(path, "rewrite patch changed path")
        return cleaned

    @model_validator(mode="after")
    def artifact_must_be_review_only(self) -> PatchArtifact:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("patch artifact must use the AION-171 rewrite authorization")
        if self.diff_hash != canonical_diff_hash(self.unified_diff):
            raise ValueError("diff_hash must match the unified diff")
        if any(
            (self.source_applied, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError(
                "patch generation must not apply source, branch, PR, or runtime effects"
            )
        return self


class PatchGenerator(Protocol):
    """Protocol seam for explicitly approved patch generators."""

    generator_id: str

    def generate(self, request: PatchRequest) -> PatchArtifact:
        """Return a bounded patch artifact."""


class DisabledPatchGenerator:
    """Fail-closed runtime default; no autonomous patch generation."""

    generator_id = "disabled-patch-generator"

    def generate(self, request: PatchRequest) -> PatchArtifact:  # noqa: ARG002
        raise RuntimeError("self-improvement patch generation is disabled")


class DeterministicTestPatchGenerator:
    """Deterministic test double for focused rewrite-controller tests."""

    generator_id = "deterministic-test-patch-generator"

    def __init__(self, unified_diff: str | None = None) -> None:
        self._unified_diff = unified_diff

    def generate(self, request: PatchRequest) -> PatchArtifact:
        changed_paths = tuple(dict.fromkeys((*request.target_paths, request.regression_test_path)))
        unified_diff = self._unified_diff or _fixture_diff(changed_paths[0])
        return PatchArtifact(
            proposal_id=request.proposal_id,
            generator_id=self.generator_id,
            unified_diff=unified_diff,
            changed_paths=changed_paths,
            diff_hash=canonical_diff_hash(unified_diff),
            generated_at=utc_now(),
        )


def _fixture_diff(path: str) -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        "-baseline\n"
        "+candidate\n"
    )


__all__ = [
    "DeterministicTestPatchGenerator",
    "DisabledPatchGenerator",
    "PatchArtifact",
    "PatchGenerator",
    "PatchRequest",
]
