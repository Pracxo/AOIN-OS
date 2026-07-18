"""Regression-test proposal generation for self-improvement experiments."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.hypothesis import ImprovementHypothesis
from aion_brain.self_improvement.observation import EXPERIMENT_AUTHORIZATION_TRANSACTION_ID


class RegressionTestProposal(BaseModel):
    """Reviewable regression-test specification; no file is written by this model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    regression_test_proposal_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    failure_pattern_id: str = Field(min_length=1)
    test_name: str = Field(min_length=1)
    test_file_path: str = Field(min_length=1)
    failing_condition: str = Field(min_length=1)
    expected_behavior: str = Field(min_length=1)
    proposed_assertions: tuple[str, ...] = Field(min_length=1)
    source_evidence_refs: tuple[str, ...] = Field(min_length=1)
    generated_by: str = Field(min_length=1)
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator(
        "regression_test_proposal_id",
        "hypothesis_id",
        "failure_pattern_id",
        "test_name",
        "test_file_path",
        "failing_condition",
        "expected_behavior",
        "generated_by",
    )
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip().replace("\\", "/")
        reject_hidden_or_secret_text(cleaned, "self-improvement regression proposal text")
        return cleaned

    @field_validator("proposed_assertions", "source_evidence_refs")
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement regression proposal reference")
        return cleaned

    @model_validator(mode="after")
    def proposal_must_be_spec_only(self) -> RegressionTestProposal:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("regression proposal must use the AION-169 experiment authorization")
        if not self.test_file_path.startswith("services/brain-api/tests/"):
            raise ValueError("regression proposals must target the Brain API test tree")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError(
                "regression proposals cannot modify source, Git, PRs, or runtime state"
            )
        return self


class RegressionTestProposalGenerator(Protocol):
    """Protocol for explicitly configured regression-test proposal generators."""

    generator_id: str

    def generate(self, hypothesis: ImprovementHypothesis) -> RegressionTestProposal:
        """Generate one regression-test specification."""


class DisabledRegressionTestProposalGenerator:
    """Fail-closed runtime default; no autonomous regression-test proposal generation."""

    generator_id = "disabled-regression-test-proposal-generator"

    def generate(self, hypothesis: ImprovementHypothesis) -> RegressionTestProposal:  # noqa: ARG002
        raise RuntimeError("self-improvement regression-test proposal generation is disabled")


class DeterministicTestRegressionProposalGenerator:
    """Deterministic test double for focused proposal-engine tests."""

    generator_id = "deterministic-test-regression-proposal-generator"

    def generate(self, hypothesis: ImprovementHypothesis) -> RegressionTestProposal:
        safe_name = hypothesis.target_metric.replace("_", "-")
        return RegressionTestProposal(
            regression_test_proposal_id=f"regression-test-{hypothesis.hypothesis_id}",
            hypothesis_id=hypothesis.hypothesis_id,
            failure_pattern_id=hypothesis.failure_pattern_id,
            test_name=f"test_self_improvement_{safe_name}_improves",
            test_file_path=(
                "services/brain-api/tests/test_self_improvement_generated_regression.py"
            ),
            failing_condition=(
                f"baseline {hypothesis.target_metric} does not satisfy the proposed target"
            ),
            expected_behavior=(
                f"candidate experiment improves {hypothesis.target_metric} "
                f"by at least {hypothesis.target_delta:.2f}"
            ),
            proposed_assertions=(
                "candidate_result.source_modified is False",
                "candidate_result.git_branch_created is False",
                "candidate_result.pr_created is False",
                f"candidate metric {hypothesis.target_metric} meets target",
            ),
            source_evidence_refs=hypothesis.source_evidence_refs,
            generated_by=self.generator_id,
            created_at=utc_now(),
        )


__all__ = [
    "DeterministicTestRegressionProposalGenerator",
    "DisabledRegressionTestProposalGenerator",
    "RegressionTestProposal",
    "RegressionTestProposalGenerator",
]
