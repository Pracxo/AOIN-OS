"""Test-first evidence for approval-bound rewrite candidates."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID


class RegressionTestSpec(BaseModel):
    """Regression test that must fail on baseline before a patch is eligible."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    test_file_path: str = Field(min_length=1)
    test_name: str = Field(min_length=1)
    command: tuple[str, ...] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("proposal_id", "test_file_path", "test_name")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip().replace("\\", "/")
        reject_hidden_or_secret_text(cleaned, "rewrite regression test spec")
        return cleaned

    @field_validator("command")
    @classmethod
    def command_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "rewrite regression command")
        return value

    @model_validator(mode="after")
    def spec_must_target_tests(self) -> RegressionTestSpec:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("test-first spec must use the AION-171 rewrite authorization")
        if not self.test_file_path.startswith("services/brain-api/tests/"):
            raise ValueError("regression test must target the Brain API test tree")
        return self


class TestCommandResult(BaseModel):
    """Observed command result captured by a sandbox or local test repo."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    command: tuple[str, ...] = Field(min_length=1)
    exit_code: int
    stdout: str = ""
    stderr: str = ""

    @model_validator(mode="after")
    def output_must_be_public(self) -> TestCommandResult:
        reject_hidden_or_secret_text(self.stdout, "rewrite test stdout")
        reject_hidden_or_secret_text(self.stderr, "rewrite test stderr")
        return self


class TestFirstEvidence(BaseModel):
    """Evidence that the regression guard failed first and passed after the patch."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    spec: RegressionTestSpec
    baseline_result: TestCommandResult
    candidate_result: TestCommandResult | None = None
    baseline_failed: bool
    candidate_passed: bool = False
    test_first_verified: bool
    created_at: datetime

    @model_validator(mode="after")
    def evidence_must_reflect_command_results(self) -> TestFirstEvidence:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("test-first evidence must use the AION-171 rewrite authorization")
        if self.proposal_id != self.spec.proposal_id:
            raise ValueError("test-first evidence must match the proposal")
        if self.baseline_failed != (self.baseline_result.exit_code != 0):
            raise ValueError("baseline_failed must reflect the baseline command exit code")
        expected_candidate_passed = (
            self.candidate_result is not None and self.candidate_result.exit_code == 0
        )
        if self.candidate_passed != expected_candidate_passed:
            raise ValueError("candidate_passed must reflect the candidate command exit code")
        expected_verified = self.baseline_failed and (
            self.candidate_result is None or self.candidate_passed
        )
        if self.test_first_verified != expected_verified:
            raise ValueError("test_first_verified must require a baseline failure")
        return self


class TestFirstVerifier:
    """Build test-first evidence from observed command results."""

    def verify_baseline_failure(
        self,
        spec: RegressionTestSpec,
        baseline_result: TestCommandResult,
    ) -> TestFirstEvidence:
        """Verify that the proposed regression fails on the baseline."""

        return TestFirstEvidence(
            proposal_id=spec.proposal_id,
            spec=spec,
            baseline_result=baseline_result,
            baseline_failed=baseline_result.exit_code != 0,
            test_first_verified=baseline_result.exit_code != 0,
            created_at=utc_now(),
        )

    def verify_candidate_pass(
        self,
        evidence: TestFirstEvidence,
        candidate_result: TestCommandResult,
    ) -> TestFirstEvidence:
        """Attach the post-patch pass evidence."""

        if not evidence.baseline_failed:
            raise ValueError("candidate pass cannot be accepted before baseline failure")
        return TestFirstEvidence(
            proposal_id=evidence.proposal_id,
            spec=evidence.spec,
            baseline_result=evidence.baseline_result,
            candidate_result=candidate_result,
            baseline_failed=evidence.baseline_failed,
            candidate_passed=candidate_result.exit_code == 0,
            test_first_verified=evidence.baseline_failed and candidate_result.exit_code == 0,
            created_at=utc_now(),
        )

__all__ = [
    "RegressionTestSpec",
    "TestCommandResult",
    "TestFirstEvidence",
    "TestFirstVerifier",
]
