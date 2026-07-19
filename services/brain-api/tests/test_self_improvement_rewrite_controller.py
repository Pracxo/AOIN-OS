from __future__ import annotations

import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aion_brain.self_improvement import (
    DeterministicTestCIMonitorAdapter,
    DeterministicTestMergeAdapter,
    DeterministicTestPatchGenerator,
    DeterministicTestPullRequestAdapter,
    DeterministicTestSandboxRunner,
    DisabledCIMonitorAdapter,
    DisabledPatchGenerator,
    DisabledPullRequestAdapter,
    DisabledSandboxRunner,
    GitController,
    ImprovementExperimentPlan,
    ImprovementProposal,
    MergeController,
    PatchRequest,
    PatchValidator,
    PullRequestController,
    PullRequestCreateRequest,
    PullRequestRecord,
    RegressionTestProposal,
    RewriteApprovalBinding,
    TaskBranchRequest,
    WorktreeManager,
    WorktreeRequest,
    analyze_test_weakening,
    build_sandbox_evidence,
    required_sandbox_commands,
    rollback_metadata_for_candidate,
)
from aion_brain.self_improvement.benchmark_contracts import (
    HIGHER_IS_BETTER_METRICS,
    REQUIRED_BENCHMARK_METRICS,
    BenchmarkMetric,
)
from aion_brain.self_improvement.patch_validator import ChangeObservation
from aion_brain.self_improvement.test_first import (
    RegressionTestSpec,
)
from aion_brain.self_improvement.test_first import (
    TestCommandResult as RewriteTestCommandResult,
)
from aion_brain.self_improvement.test_first import (
    TestFirstVerifier as RewriteTestFirstVerifier,
)


def test_worktree_manager_creates_detached_isolated_worktree_from_exact_base(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)
    base_sha = _git(repo, "rev-parse", "HEAD")
    worktree_path = tmp_path / "candidate-worktree"

    result = WorktreeManager(SubprocessGitCommandRunner()).create(
        WorktreeRequest(
            proposal_id="proposal-172",
            repo_path=repo,
            worktree_path=worktree_path,
            base_sha=base_sha,
        )
    )

    assert result.base_sha == base_sha
    assert result.head_sha == base_sha
    assert result.isolated is True
    assert (worktree_path / "subject.txt").read_text() == "baseline\n"
    assert _git(worktree_path, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"


def test_git_controller_rejects_direct_main_push_and_creates_task_branch(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)
    sha = _git(repo, "rev-parse", "HEAD")
    controller = GitController(SubprocessGitCommandRunner())

    with pytest.raises(ValueError, match="must never push directly to main"):
        controller.reject_direct_main_push("HEAD:main")

    snapshot = controller.create_task_branch(
        TaskBranchRequest(
            repo_path=repo,
            branch_name="phase/self-improvement-approved-rewrite-controller",
            start_sha=sha,
            approved_commit_sha=sha,
            approved_diff_hash=_hash("d"),
        )
    )

    assert snapshot.commit_sha == sha
    assert snapshot.branch_name == "phase/self-improvement-approved-rewrite-controller"


def test_test_first_requires_baseline_failure_before_candidate_pass() -> None:
    spec = RegressionTestSpec(
        proposal_id="proposal-172",
        test_file_path="services/brain-api/tests/test_generated_regression.py",
        test_name="test_generated_regression",
        command=("pytest", "services/brain-api/tests/test_generated_regression.py"),
    )
    verifier = RewriteTestFirstVerifier()

    evidence = verifier.verify_baseline_failure(
        spec,
        RewriteTestCommandResult(command=spec.command, exit_code=1, stdout="", stderr="failed"),
    )

    assert evidence.baseline_failed is True
    assert evidence.test_first_verified is True

    candidate = verifier.verify_candidate_pass(
        evidence,
        RewriteTestCommandResult(command=spec.command, exit_code=0, stdout="passed", stderr=""),
    )

    assert candidate.candidate_passed is True
    assert candidate.test_first_verified is True

    no_failure = verifier.verify_baseline_failure(
        spec,
        RewriteTestCommandResult(command=spec.command, exit_code=0, stdout="passed", stderr=""),
    )
    with pytest.raises(ValueError, match="before baseline failure"):
        verifier.verify_candidate_pass(
            no_failure,
            RewriteTestCommandResult(command=spec.command, exit_code=0),
        )


def test_patch_validator_enforces_paths_budget_and_elevated_test_changes() -> None:
    source_path = "services/brain-api/src/aion_brain/self_improvement/example.py"
    test_path = "services/brain-api/tests/test_self_improvement_example.py"
    proposal = _proposal(allowed_paths=(source_path, test_path))
    artifact = DeterministicTestPatchGenerator(
        unified_diff=(
            f"diff --git a/{source_path} b/{source_path}\n"
            f"--- a/{source_path}\n"
            f"+++ b/{source_path}\n"
            "@@ -1 +1 @@\n"
            "-baseline\n"
            "+candidate\n"
        )
    ).generate(
        PatchRequest(
            proposal_id=proposal.proposal_id,
            base_sha=_sha("a"),
            allowed_paths=proposal.allowed_paths,
            prohibited_paths=proposal.prohibited_paths,
            regression_test_path=test_path,
            target_paths=(source_path,),
        )
    )

    result = PatchValidator().validate(
        proposal=proposal,
        artifact=artifact,
        observation=ChangeObservation(
            changed_paths=(source_path, test_path),
            insertions=8,
            deletions=1,
        ),
    )

    assert result.validation_passed is True
    assert result.required_approval_tier == "dual_approval"
    assert "source_and_guarding_tests_changed" in result.reason_codes


def test_patch_validator_blocks_prohibited_protected_and_own_approval_changes() -> None:
    approval_path = "services/brain-api/src/aion_brain/self_improvement/approval.py"
    test_path = "services/brain-api/tests/test_self_improvement_generated_regression.py"
    proposal = _proposal(
        allowed_paths=(approval_path, test_path),
        prohibited_paths=(".github/",),
    )
    diff = (
        f"diff --git a/{approval_path} b/{approval_path}\n"
        f"--- a/{approval_path}\n"
        f"+++ b/{approval_path}\n"
        "@@ -1 +1 @@\n"
        "-baseline\n"
        "+candidate\n"
    )
    artifact = DeterministicTestPatchGenerator(unified_diff=diff).generate(
        PatchRequest(
            proposal_id=proposal.proposal_id,
            base_sha=_sha("a"),
            allowed_paths=proposal.allowed_paths,
            prohibited_paths=proposal.prohibited_paths,
            regression_test_path=test_path,
            target_paths=(approval_path,),
        )
    )

    result = PatchValidator().validate(
        proposal=proposal,
        artifact=artifact,
        observation=ChangeObservation(
            changed_paths=(approval_path, test_path),
            insertions=1,
            deletions=1,
        ),
    )

    assert result.validation_passed is False
    assert "protected_core_change_requires_dual_governance" in result.reason_codes
    assert "own_approval_modified" in result.reason_codes


def test_test_weakening_controls_detect_guard_removal_and_high_risk_mutation_need() -> None:
    report = analyze_test_weakening(
        "\n".join(
            (
                "-    assert result.status == 'blocked'",
                "+    pytest.skip('temporary exclusion')",
                "+    expected_status = \"allowed\"",
                "-threshold = 0.9",
                "+threshold = 0.1",
            )
        ),
        changed_paths=(
            "services/brain-api/src/aion_brain/self_improvement/example.py",
            "services/brain-api/tests/test_self_improvement_example.py",
        ),
        risk_level="high",
    )

    assert report.deleted_assertions
    assert report.skipped_tests
    assert report.reduced_expected_security_state
    assert report.benchmark_threshold_changes
    assert report.elevated_approval_required is True
    assert report.mutation_checks_required is True
    assert report.weakening_detected is True


def test_disabled_defaults_block_patch_sandbox_pr_ci_and_merge() -> None:
    request = PatchRequest(
        proposal_id="proposal-172",
        base_sha=_sha("a"),
        allowed_paths=("services/brain-api/tests/test_generated_regression.py",),
        regression_test_path="services/brain-api/tests/test_generated_regression.py",
        target_paths=("services/brain-api/tests/test_generated_regression.py",),
    )
    with pytest.raises(RuntimeError, match="patch generation is disabled"):
        DisabledPatchGenerator().generate(request)

    command = required_sandbox_commands()[0]
    with pytest.raises(RuntimeError, match="sandbox execution is disabled"):
        DisabledSandboxRunner().run(command)

    with pytest.raises(RuntimeError, match="pull request creation is disabled"):
        DisabledPullRequestAdapter().create_pull_request(_pr_request())

    with pytest.raises(RuntimeError, match="CI monitoring is disabled"):
        DisabledCIMonitorAdapter().checks_for_pull_request(1, _sha("a"))

    approval = _approval()
    pr = _pull_request()
    ci = DeterministicTestCIMonitorAdapter().checks_for_pull_request(
        pr.pr_number,
        pr.head_sha,
    )
    with pytest.raises(RuntimeError, match="pull request merge is disabled"):
        MergeController().merge_when_safe(
            approval=approval,
            pull_request=pr,
            ci_report=ci,
            current_head_sha=pr.head_sha,
            current_benchmark_fingerprint=approval.approved_benchmark_fingerprint,
        )


def test_approval_binding_invalidates_after_code_change_and_pr_uses_mocked_adapter() -> None:
    approval = _approval()
    request = _pr_request()
    controller = PullRequestController(DeterministicTestPullRequestAdapter())

    record = controller.create_pull_request(approval=approval, request=request)

    assert record.pr_number == 172
    assert record.head_sha == approval.approved_commit_sha

    invalidated = approval.invalidate_after_change(
        current_commit_sha=approval.approved_commit_sha,
        current_diff_hash=_hash("e"),
        current_benchmark_fingerprint=approval.approved_benchmark_fingerprint,
        current_rollback_commit=approval.approved_rollback_commit,
    )
    with pytest.raises(ValueError, match="valid exact approval is required"):
        controller.create_pull_request(approval=invalidated, request=request)


def test_sandbox_evidence_and_merge_controller_require_green_unchanged_head() -> None:
    runner = DeterministicTestSandboxRunner()
    results = tuple(runner.run(command) for command in required_sandbox_commands())
    evidence = build_sandbox_evidence(
        proposal_id="proposal-172",
        worktree_path=Path("/tmp/aion-172-candidate"),
        command_results=results,
    )

    assert evidence.all_required_pass is True
    assert evidence.benchmark_fingerprint
    assert evidence.holdout_fingerprint

    approval = _approval(benchmark_fingerprint=evidence.benchmark_fingerprint)
    pr = _pull_request(diff_hash=approval.approved_diff_hash, head_sha=approval.approved_commit_sha)
    ci_monitor = DeterministicTestCIMonitorAdapter(proposal_id=approval.proposal_id)
    ci = ci_monitor.checks_for_pull_request(pr.pr_number, pr.head_sha)
    merged = MergeController(DeterministicTestMergeAdapter()).merge_when_safe(
        approval=approval,
        pull_request=pr,
        ci_report=ci,
        current_head_sha=pr.head_sha,
        current_benchmark_fingerprint=evidence.benchmark_fingerprint,
    )

    assert merged.status == "merged"
    assert merged.merged_commit_sha == approval.approved_commit_sha

    changed_head = MergeController(DeterministicTestMergeAdapter()).merge_when_safe(
        approval=approval,
        pull_request=pr,
        ci_report=ci,
        current_head_sha=_sha("c"),
        current_benchmark_fingerprint=evidence.benchmark_fingerprint,
    )

    assert changed_head.status == "blocked"
    assert "pull_request_head_changed" in changed_head.reason_codes


def test_rollback_metadata_binds_distinct_rollback_commit_and_merge_commit() -> None:
    metadata = rollback_metadata_for_candidate(
        proposal_id="proposal-172",
        approved_commit_sha=_sha("a"),
        rollback_commit_sha=_sha("b"),
        deployment_scope="disabled-local-canary",
        rollback_test_refs=("pytest:services/brain-api/tests/test_self_improvement_rewrite_controller.py",),
    )

    assert metadata.rollback_commit_sha != metadata.approved_commit_sha
    after_merge = metadata.record_merge(_sha("c"))
    assert after_merge.recorded_after_merge is True
    assert after_merge.merge_commit_sha == _sha("c")

    with pytest.raises(ValueError, match="rollback commit must differ"):
        rollback_metadata_for_candidate(
            proposal_id="proposal-172",
            approved_commit_sha=_sha("a"),
            rollback_commit_sha=_sha("a"),
            deployment_scope="disabled-local-canary",
            rollback_test_refs=("pytest:rewrite-controller",),
        )


def _proposal(
    *,
    allowed_paths: tuple[str, ...],
    prohibited_paths: tuple[str, ...] = ("docs/self-improvement/holdout/",),
    risk_level: str = "medium",
) -> ImprovementProposal:
    test = RegressionTestProposal(
        regression_test_proposal_id="regression-test-172",
        hypothesis_id="hypothesis-172",
        failure_pattern_id="failure-pattern-172",
        test_name="test_generated_regression",
        test_file_path=allowed_paths[-1],
        failing_condition="baseline fails the regression",
        expected_behavior="candidate passes the regression",
        proposed_assertions=("candidate_result.status == 'passed'",),
        source_evidence_refs=("evaluation:evaluation-172",),
        generated_by="deterministic-test",
        created_at=_now(),
    )
    plan = ImprovementExperimentPlan(
        experiment_plan_id="experiment-plan-172",
        failure_pattern_id="failure-pattern-172",
        hypothesis_id="hypothesis-172",
        regression_test_proposal_id="regression-test-172",
        baseline_metrics=_baseline_metrics(),
        target_metrics=_target_metrics(),
        candidate_slot_id="candidate-slot-172",
        allowed_paths=allowed_paths,
        prohibited_paths=prohibited_paths,
        experiment_spec={"source_mutation_enabled": False},
        source_evidence_refs=("evaluation:evaluation-172",),
        created_at=_now(),
    )
    return ImprovementProposal(
        proposal_id="proposal-172",
        author_actor_id="operator-aion",
        problem_statement="Repeated evaluation failure requires a bounded rewrite.",
        source_evidence_refs=("evaluation:evaluation-172",),
        failure_pattern_id="failure-pattern-172",
        baseline_metrics=_baseline_metrics(),
        target_metrics=_target_metrics(),
        change_type="regression_test",
        allowed_paths=allowed_paths,
        prohibited_paths=prohibited_paths,
        test_specification=test,
        experiment_specification=plan,
        risk_level=risk_level,  # type: ignore[arg-type]
        approval_tier="owner",
        rollback_requirement=True,
        created_at=_now(),
    )


def _baseline_metrics() -> tuple[BenchmarkMetric, ...]:
    values = {
        "task_success": 0.6,
        "evidence_grounding": 0.6,
        "user_correction_rate": 0.1,
        "retrieval_precision": 0.55,
        "plan_success": 0.65,
        "policy_violation_count": 1.0,
        "regression_count": 1.0,
        "latency": 12.0,
        "compute_cost": 1.2,
        "rollback_count": 1.0,
        "improvement_survival": 0.8,
    }
    return _metrics(values)


def _target_metrics() -> tuple[BenchmarkMetric, ...]:
    values = {
        "task_success": 0.85,
        "evidence_grounding": 0.85,
        "user_correction_rate": 0.03,
        "retrieval_precision": 0.85,
        "plan_success": 0.85,
        "policy_violation_count": 0.0,
        "regression_count": 0.0,
        "latency": 8.0,
        "compute_cost": 0.8,
        "rollback_count": 0.0,
        "improvement_survival": 1.0,
    }
    return _metrics(values)


def _metrics(values: dict[str, float]) -> tuple[BenchmarkMetric, ...]:
    thresholds = {
        "task_success": 0.8,
        "evidence_grounding": 0.8,
        "user_correction_rate": 0.05,
        "retrieval_precision": 0.75,
        "plan_success": 0.8,
        "policy_violation_count": 0.0,
        "regression_count": 0.0,
        "latency": 10.0,
        "compute_cost": 1.0,
        "rollback_count": 0.0,
        "improvement_survival": 1.0,
    }
    return tuple(
        BenchmarkMetric(
            metric_name=name,
            value=values[name],
            threshold=thresholds[name],
            higher_is_better=name in HIGHER_IS_BETTER_METRICS,
            unit="score" if name in HIGHER_IS_BETTER_METRICS else "count",
        )
        for name in REQUIRED_BENCHMARK_METRICS
    )


def _approval(*, benchmark_fingerprint: str | None = None) -> RewriteApprovalBinding:
    fingerprint = benchmark_fingerprint or _hash("b")
    return RewriteApprovalBinding(
        proposal_id="proposal-172",
        approval_status="approved",
        approved_commit_sha=_sha("a"),
        approved_diff_hash=_hash("d"),
        approved_benchmark_fingerprint=fingerprint,
        approved_rollback_commit=_sha("b"),
        approved_deployment_scope="disabled-local-canary",
        current_commit_sha=_sha("a"),
        current_diff_hash=_hash("d"),
        current_benchmark_fingerprint=fingerprint,
        current_rollback_commit=_sha("b"),
        approver_actor_ids=("operator-aion",),
        created_at=_now(),
    )


def _pr_request() -> PullRequestCreateRequest:
    return PullRequestCreateRequest(
        proposal_id="proposal-172",
        branch_name="phase/self-improvement-approved-rewrite-controller",
        head_sha=_sha("a"),
        diff_hash=_hash("d"),
        title="AION-172 approved rewrite controller",
        body="Evidence-bound rewrite controller candidate.",
    )


def _pull_request(
    *,
    diff_hash: str | None = None,
    head_sha: str | None = None,
) -> PullRequestRecord:
    return PullRequestRecord(
        pr_number=172,
        url="https://example.invalid/pull/172",
        branch_name="phase/self-improvement-approved-rewrite-controller",
        base_branch="main",
        head_sha=head_sha or _sha("a"),
        diff_hash=diff_hash or _hash("d"),
        created_at=_now(),
    )


def _git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "aion@example.invalid")
    _git(repo, "config", "user.name", "AION Test")
    (repo / "subject.txt").write_text("baseline\n")
    _git(repo, "add", "subject.txt")
    _git(repo, "commit", "-m", "baseline")
    return repo


def _git(repo: Path, *args: str) -> str:
    return SubprocessGitCommandRunner().run_git(repo, args)


class SubprocessGitCommandRunner:
    def run_git(self, cwd: Path, args: Sequence[str]) -> str:
        result = subprocess.run(
            ("git", *args),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()


def _sha(char: str) -> str:
    return char * 40


def _hash(char: str) -> str:
    return char * 64


def _now() -> datetime:
    return datetime.now(UTC)
