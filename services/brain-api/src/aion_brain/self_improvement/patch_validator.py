"""Patch validation for approval-bound source rewrites."""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import ImprovementChangeBudget
from aion_brain.self_improvement.change_budget import ChangeBudgetLimit, evaluate_change_budget
from aion_brain.self_improvement.experiment import ApprovalTier, ImprovementProposal
from aion_brain.self_improvement.patch_generator import PatchArtifact
from aion_brain.self_improvement.protected_paths import matched_protected_pattern
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID

ValidationReason = Literal[
    "allowed_path_violation",
    "prohibited_path_violation",
    "change_budget_exceeded",
    "protected_core_change_requires_dual_governance",
    "own_approval_modified",
    "test_weakening_detected",
    "source_and_guarding_tests_changed",
    "mutation_checks_required",
]


class ChangeObservation(BaseModel):
    """Observed change shape extracted from a diff."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    changed_paths: tuple[str, ...] = Field(min_length=1)
    insertions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    dependency_changes: int = Field(default=0, ge=0)

    @field_validator("changed_paths")
    @classmethod
    def paths_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(_normalize_path(path) for path in value)
        for path in cleaned:
            reject_hidden_or_secret_text(path, "rewrite change observation path")
        return cleaned


class PathPolicy(BaseModel):
    """Allowed and prohibited path policy for one proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed_paths: tuple[str, ...] = Field(min_length=1)
    prohibited_paths: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("allowed_paths", "prohibited_paths")
    @classmethod
    def paths_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_normalize_path(path) for path in value)

    def allows(self, path: str) -> bool:
        """Return whether the path matches an allowed pattern."""

        normalized = _normalize_path(path)
        return any(_matches(normalized, pattern) for pattern in self.allowed_paths)

    def prohibits(self, path: str) -> bool:
        """Return whether the path matches a prohibited pattern."""

        normalized = _normalize_path(path)
        return any(_matches(normalized, pattern) for pattern in self.prohibited_paths)


class TestWeakeningReport(BaseModel):
    """Test-weakening findings extracted from a unified diff."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    deleted_assertions: tuple[str, ...] = Field(default_factory=tuple)
    reduced_expected_security_state: tuple[str, ...] = Field(default_factory=tuple)
    skipped_tests: tuple[str, ...] = Field(default_factory=tuple)
    broad_test_exclusions: tuple[str, ...] = Field(default_factory=tuple)
    benchmark_threshold_changes: tuple[str, ...] = Field(default_factory=tuple)
    elevated_approval_required: bool
    mutation_checks_required: bool
    weakening_detected: bool

    @model_validator(mode="after")
    def weakening_flag_must_match_findings(self) -> TestWeakeningReport:
        expected = any(
            (
                self.deleted_assertions,
                self.reduced_expected_security_state,
                self.skipped_tests,
                self.broad_test_exclusions,
                self.benchmark_threshold_changes,
            )
        )
        if self.weakening_detected != expected:
            raise ValueError("weakening_detected must match weakening findings")
        return self


class PatchValidationResult(BaseModel):
    """Patch validation result that must pass before approval can be requested."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    changed_paths: tuple[str, ...] = Field(min_length=1)
    change_budget: ImprovementChangeBudget
    protected_core_paths: tuple[str, ...] = Field(default_factory=tuple)
    own_approval_modified: bool
    allowed_paths_pass: bool
    prohibited_paths_pass: bool
    change_budget_pass: bool
    protected_core_pass: bool
    test_weakening_pass: bool
    mutation_checks_required: bool
    required_approval_tier: ApprovalTier
    validation_passed: bool
    reason_codes: tuple[ValidationReason, ...] = Field(default_factory=tuple)
    weakening_report: TestWeakeningReport

    @model_validator(mode="after")
    def validation_flag_must_match_gates(self) -> PatchValidationResult:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("patch validation must use the AION-171 rewrite authorization")
        expected = (
            self.allowed_paths_pass
            and self.prohibited_paths_pass
            and self.change_budget_pass
            and self.protected_core_pass
            and self.test_weakening_pass
            and not self.own_approval_modified
        )
        if self.validation_passed != expected:
            raise ValueError("validation_passed must reflect all hard gates")
        return self


class PatchValidator:
    """Validate patch artifacts against proposal boundaries."""

    def validate(
        self,
        *,
        proposal: ImprovementProposal,
        artifact: PatchArtifact,
        observation: ChangeObservation,
        limit: ChangeBudgetLimit | None = None,
        dual_governance_approved: bool = False,
    ) -> PatchValidationResult:
        """Validate path, budget, protected-core, and test-weakening controls."""

        if proposal.proposal_id != artifact.proposal_id:
            raise ValueError("patch artifact must match proposal")
        if tuple(sorted(artifact.changed_paths)) != tuple(sorted(observation.changed_paths)):
            raise ValueError("change observation must match patch artifact paths")

        policy = PathPolicy(
            allowed_paths=proposal.allowed_paths,
            prohibited_paths=proposal.prohibited_paths,
        )
        protected_core_paths = tuple(
            path
            for path in observation.changed_paths
            if matched_protected_pattern(path) is not None
        )
        own_approval_modified = any(
            _is_own_approval_path(path) for path in observation.changed_paths
        )
        weakening = analyze_test_weakening(
            artifact.unified_diff,
            changed_paths=observation.changed_paths,
            risk_level=proposal.risk_level,
        )
        budget = evaluate_change_budget(
            proposal_id=proposal.proposal_id,
            observed_files=len(observation.changed_paths),
            observed_insertions=observation.insertions,
            observed_deletions=observation.deletions,
            dependency_changes=observation.dependency_changes,
            protected_paths_touched=len(protected_core_paths),
            limit=limit
            or ChangeBudgetLimit(
                max_protected_paths=len(protected_core_paths) if dual_governance_approved else 0
            ),
        )
        allowed_pass = all(policy.allows(path) for path in observation.changed_paths)
        prohibited_pass = not any(policy.prohibits(path) for path in observation.changed_paths)
        protected_pass = not protected_core_paths or dual_governance_approved
        test_weakening_pass = not weakening.weakening_detected
        required_tier: ApprovalTier = (
            "dual_approval"
            if (protected_core_paths or weakening.elevated_approval_required)
            else proposal.approval_tier
        )
        reasons: list[ValidationReason] = []
        if not allowed_pass:
            reasons.append("allowed_path_violation")
        if not prohibited_pass:
            reasons.append("prohibited_path_violation")
        if not budget.within_budget:
            reasons.append("change_budget_exceeded")
        if protected_core_paths and not dual_governance_approved:
            reasons.append("protected_core_change_requires_dual_governance")
        if own_approval_modified:
            reasons.append("own_approval_modified")
        if weakening.weakening_detected:
            reasons.append("test_weakening_detected")
        if weakening.elevated_approval_required:
            reasons.append("source_and_guarding_tests_changed")
        if weakening.mutation_checks_required:
            reasons.append("mutation_checks_required")

        validation_passed = (
            allowed_pass
            and prohibited_pass
            and budget.within_budget
            and protected_pass
            and test_weakening_pass
            and not own_approval_modified
        )
        return PatchValidationResult(
            proposal_id=proposal.proposal_id,
            changed_paths=observation.changed_paths,
            change_budget=budget,
            protected_core_paths=protected_core_paths,
            own_approval_modified=own_approval_modified,
            allowed_paths_pass=allowed_pass,
            prohibited_paths_pass=prohibited_pass,
            change_budget_pass=budget.within_budget,
            protected_core_pass=protected_pass,
            test_weakening_pass=test_weakening_pass,
            mutation_checks_required=weakening.mutation_checks_required,
            required_approval_tier=required_tier,
            validation_passed=validation_passed,
            reason_codes=tuple(reasons),
            weakening_report=weakening,
        )


def analyze_test_weakening(
    unified_diff: str,
    *,
    changed_paths: tuple[str, ...],
    risk_level: str,
) -> TestWeakeningReport:
    """Detect common attempts to make a patch pass by weakening tests."""

    deleted_assertions: list[str] = []
    reduced_security: list[str] = []
    skipped_tests: list[str] = []
    broad_exclusions: list[str] = []
    threshold_changes: list[str] = []
    for line in unified_diff.splitlines():
        lowered = line.lower()
        if line.startswith("-") and not line.startswith("---") and "assert" in lowered:
            deleted_assertions.append(line)
        if line.startswith("+") and not line.startswith("+++") and _is_skip_marker(lowered):
            skipped_tests.append(line)
        if line.startswith("+") and not line.startswith("+++") and _is_broad_exclusion(lowered):
            broad_exclusions.append(line)
        if (
            line[:1] in {"+", "-"}
            and not line.startswith(("+++", "---"))
            and "threshold" in lowered
        ):
            threshold_changes.append(line)
        if line.startswith("+") and not line.startswith("+++") and _reduces_security_state(lowered):
            reduced_security.append(line)

    source_changed = any(path.startswith("services/brain-api/src/") for path in changed_paths)
    tests_changed = any(
        "/tests/" in path or path.startswith("services/brain-api/tests/") for path in changed_paths
    )
    return TestWeakeningReport(
        deleted_assertions=tuple(deleted_assertions),
        reduced_expected_security_state=tuple(reduced_security),
        skipped_tests=tuple(skipped_tests),
        broad_test_exclusions=tuple(broad_exclusions),
        benchmark_threshold_changes=tuple(threshold_changes),
        elevated_approval_required=source_changed and tests_changed,
        mutation_checks_required=risk_level in {"high", "critical"},
        weakening_detected=any(
            (
                deleted_assertions,
                reduced_security,
                skipped_tests,
                broad_exclusions,
                threshold_changes,
            )
        ),
    )


def _matches(path: str, pattern: str) -> bool:
    normalized = _normalize_path(pattern)
    if normalized.endswith("/"):
        return path.startswith(normalized)
    if normalized.endswith("*"):
        return fnmatch(path, normalized)
    return path == normalized or fnmatch(path, normalized)


def _normalize_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        raise ValueError("repository path must stay inside the repository")
    return normalized


def _is_skip_marker(lowered_line: str) -> bool:
    return any(
        marker in lowered_line
        for marker in ("pytest.mark.skip", "pytest.skip", "@unittest.skip", "skipif(")
    )


def _is_broad_exclusion(lowered_line: str) -> bool:
    return any(
        marker in lowered_line
        for marker in ("--ignore=", '-k "not', "-k 'not", "xfail", "filterwarnings")
    )


def _reduces_security_state(lowered_line: str) -> bool:
    return any(
        marker in lowered_line
        for marker in (
            "security_passed = true",
            "security_passed: true",
            "policy_violation_count = 0",
            'expected_status = "allowed"',
            "fail_closed = false",
        )
    )


def _is_own_approval_path(path: str) -> bool:
    return _normalize_path(path) in {
        "docs/self-improvement/authorization-ledger.json",
        "services/brain-api/src/aion_brain/self_improvement/approval.py",
    }


__all__ = [
    "ChangeObservation",
    "PatchValidationResult",
    "PatchValidator",
    "PathPolicy",
    "TestWeakeningReport",
    "analyze_test_weakening",
]
