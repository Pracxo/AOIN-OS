from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement import (
    CANARY_AUTHORIZATION_TRANSACTION_ID,
    ROLLBACK_TRIGGERS,
    CanaryController,
    CanaryExposureBudget,
    CanaryMetricThreshold,
    CanaryObservation,
    CanaryPlan,
    CaseBasedPlanner,
    ContextBucketStrategySelector,
    DeterministicTestCIMonitorAdapter,
    DeterministicTestMergeAdapter,
    DeterministicTestPatchGenerator,
    DeterministicTestPullRequestAdapter,
    ImprovementOutcomeLedger,
    IntegratedSelfImprovementDryRun,
    LearningLedgerRecord,
    PatchRequest,
    PlanningCase,
    PreferenceDistribution,
    PreferenceLearner,
    ProceduralSkillEvolution,
    ProceduralSkillRecord,
    PullRequestController,
    PullRequestCreateRequest,
    RegressionTestSpec,
    RetrievalRankingOptimizer,
    RetrievalRankingVersion,
    RewriteApprovalBinding,
    StrategySelectionPolicy,
    StrategyStats,
    TestCommandResult,
    TestFirstVerifier,
    UserPreferenceSignal,
    WorktreeManager,
    WorktreeRequest,
)
from aion_brain.self_improvement.benchmark_contracts import (
    HIGHER_IS_BETTER_METRICS,
    LOWER_IS_BETTER_METRICS,
    REQUIRED_BENCHMARK_METRICS,
    BenchmarkMetric,
)
from aion_brain.self_improvement.ci_monitor import CIMonitor
from aion_brain.self_improvement.merge_controller import MergeController


def test_canary_requires_exact_approval_and_rolls_back_degraded_metrics() -> None:
    plan = _canary_plan()
    assert plan.authorization_transaction_id == CANARY_AUTHORIZATION_TRANSACTION_ID
    approval = plan.approval_binding(approver_actor_ids=("owner",))
    controller = CanaryController()

    approved = controller.approve(plan, approval)
    assert approved.state == "approved"
    start = controller.start_local_simulation(approved, approval)
    assert start.allowed is True
    assert start.to_state == "running"

    running = approved.model_copy(update={"state": "running"})
    healthy_summary = controller.monitor(running, (_observation("healthy", _metrics()),))
    assert healthy_summary.healthy is True
    assert controller.evaluate(running, healthy_summary).to_state == "passed"

    degraded = _observation(
        "degraded",
        _metrics(task_success=0.5, user_correction_rate=0.3, latency=200.0),
    )
    degraded_summary = controller.monitor(running, (degraded,))
    decision = controller.decide_rollback(running, degraded_summary)

    assert decision.rollback_required is True
    assert decision.rollback_allowed is True
    assert "task_success_degradation" in decision.triggers
    assert "user_correction_increase" in decision.triggers
    assert "latency_budget_breach" in decision.triggers
    assert set(ROLLBACK_TRIGGERS) >= set(decision.triggers)


def test_adaptive_learning_planes_are_bounded_reversible_and_approval_gated() -> None:
    ledger = ImprovementOutcomeLedger(ledger_id="ledger").append(
        LearningLedgerRecord(
            record_id="outcome-1",
            proposal_id="proposal-174",
            record_kind="final_outcome",
            outcome_value="improvement_success",
        )
    )
    active_ranking = RetrievalRankingVersion(
        version_id="ranking-v1",
        feature_weights={"recency": 0.98, "prior_success": 0.2},
        status="active",
    )
    optimizer = RetrievalRankingOptimizer()
    candidate = optimizer.propose_candidate(
        active_ranking,
        ledger.outcomes(),
        candidate_version_id="ranking-v2",
    )
    assert candidate.status == "candidate"
    assert candidate.feature_weights["recency"] == 1.0
    with pytest.raises(ValueError, match="approval is required"):
        optimizer.promote(candidate, approval_granted=False)
    assert optimizer.promote(candidate, approval_granted=True).status == "active"

    case = CaseBasedPlanner().retrieve(
        (
            _planning_case("case-low", ("retrieval",), 0.4),
            _planning_case("case-high", ("retrieval", "latency"), 0.9),
        ),
        ("retrieval", "latency"),
    )
    adapted = CaseBasedPlanner().adapt(case, ("retrieval", "latency"), adapted_plan_id="adapted")
    assert adapted.policy_validation_preserved is True
    assert adapted.direct_execution_allowed is False

    selection = ContextBucketStrategySelector().select(
        StrategySelectionPolicy(allowlisted_strategy_ids=("safe-retry", "tighten-retrieval")),
        "retrieval-latency",
        (
            StrategyStats(strategy_id="safe-retry", alpha=2, beta=2),
            StrategyStats(strategy_id="tighten-retrieval", alpha=5, beta=1),
        ),
    )
    assert selection.selected_strategy_id == "tighten-retrieval"
    assert selection.shadow_mode is True

    learner = PreferenceLearner()
    distribution = PreferenceDistribution(
        distribution_id="pref-v1",
        user_scope_id="user-local",
        preference_key="concise_status",
    )
    with pytest.raises(ValueError, match="approval is required"):
        learner.update(
            distribution,
            UserPreferenceSignal(
                signal_id="signal-1",
                user_scope_id="user-local",
                preference_key="concise_status",
                positive=True,
                confidence=0.8,
                impact="high",
            ),
        )
    updated = learner.update(
        distribution,
        UserPreferenceSignal(
            signal_id="signal-2",
            user_scope_id="user-local",
            preference_key="concise_status",
            positive=True,
            confidence=0.8,
            impact="high",
        ),
        approval_granted=True,
    )
    assert updated.version == 2
    with pytest.raises(ValueError, match="protected attribute"):
        UserPreferenceSignal(
            signal_id="signal-3",
            user_scope_id="user-local",
            preference_key="age",
            positive=True,
            confidence=0.5,
        )

    current_skill = ProceduralSkillRecord(
        skill_id="triage-loop",
        version=1,
        status="active",
        procedure_steps=("observe", "test", "report"),
        policy_gate_passed=True,
        approval_status="approved",
    )
    candidate_skill = ProceduralSkillEvolution().propose(
        current_skill,
        candidate_steps=("observe", "test", "rollback", "report"),
    )
    with pytest.raises(ValueError, match="approval is required"):
        ProceduralSkillEvolution().promote(
            candidate_skill,
            policy_gate_passed=True,
            approval_granted=False,
        )
    promoted = ProceduralSkillEvolution().promote(
        candidate_skill,
        policy_gate_passed=True,
        approval_granted=True,
    )
    assert promoted.status == "active"
    assert promoted.direct_runtime_activation_enabled is False


def test_integrated_dry_run_uses_temp_worktree_and_simulated_pr_ci_merge_only(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)
    base_sha = _git(repo, "rev-parse", "HEAD")
    worktree = tmp_path / "candidate-worktree"
    worktree_result = WorktreeManager(SubprocessGitCommandRunner()).create(
        WorktreeRequest(
            proposal_id="proposal-174",
            repo_path=repo,
            worktree_path=worktree,
            base_sha=base_sha,
        )
    )
    assert worktree_result.isolated is True

    patch = DeterministicTestPatchGenerator().generate(
        PatchRequest(
            proposal_id="proposal-174",
            base_sha=base_sha,
            allowed_paths=(
                "services/brain-api/tests/fixtures/retrieval.txt",
                "services/brain-api/tests/test_retrieval_regression.py",
            ),
            regression_test_path="services/brain-api/tests/test_retrieval_regression.py",
            target_paths=("services/brain-api/tests/fixtures/retrieval.txt",),
        )
    )
    assert patch.source_applied is False
    evidence = TestFirstVerifier().verify_baseline_failure(
        RegressionTestSpec(
                proposal_id="proposal-174",
                test_file_path="services/brain-api/tests/test_retrieval_regression.py",
                test_name="test_retrieval_regression",
                command=("pytest", "services/brain-api/tests/test_retrieval_regression.py"),
            ),
            TestCommandResult(
                command=("pytest", "services/brain-api/tests/test_retrieval_regression.py"),
                exit_code=1,
            ),
    )
    assert (
        TestFirstVerifier()
        .verify_candidate_pass(
            evidence,
            TestCommandResult(
                command=("pytest", "services/brain-api/tests/test_retrieval_regression.py"),
                exit_code=0,
            ),
        )
        .candidate_passed
        is True
    )

    rewrite_approval = RewriteApprovalBinding(
        proposal_id="proposal-174",
        approval_status="approved",
        approved_commit_sha=base_sha,
        approved_diff_hash=patch.diff_hash,
        approved_benchmark_fingerprint=_sha256("b"),
        approved_rollback_commit=base_sha,
        approved_deployment_scope="local-test-only",
        current_commit_sha=base_sha,
        current_diff_hash=patch.diff_hash,
        current_benchmark_fingerprint=_sha256("b"),
        current_rollback_commit=base_sha,
        approver_actor_ids=("owner",),
        created_at=utc_now(),
    )
    pull_request = PullRequestController(DeterministicTestPullRequestAdapter()).create_pull_request(
        approval=rewrite_approval,
        request=PullRequestCreateRequest(
            proposal_id="proposal-174",
            branch_name="phase/test-only-self-improvement",
            head_sha=base_sha,
            diff_hash=patch.diff_hash,
            title="test-only self-improvement",
            body="synthetic local dry-run only",
        ),
    )
    ci_report = CIMonitor(
        DeterministicTestCIMonitorAdapter(proposal_id="proposal-174")
    ).checks_for_pull_request(pull_request.pr_number, pull_request.head_sha)
    merge_result = MergeController(DeterministicTestMergeAdapter()).merge_when_safe(
        approval=rewrite_approval,
        pull_request=pull_request,
        ci_report=ci_report,
        current_head_sha=base_sha,
        current_benchmark_fingerprint=_sha256("b"),
    )
    assert merge_result.status == "merged"

    plan = _canary_plan()
    result = IntegratedSelfImprovementDryRun().run(
        plan=plan,
        approval=plan.approval_binding(approver_actor_ids=("owner",)),
        healthy_observations=(_observation("healthy-integrated", _metrics()),),
        degrading_observations=(
            _observation("degraded-integrated", _metrics(task_success=0.5)),
        ),
    )

    assert result.synthetic_failure_injected is True
    assert result.isolated_worktree_created is True
    assert result.simulated_branch_and_pr_created is True
    assert result.simulated_ci_success is True
    assert result.simulated_merge_completed is True
    assert result.disabled_local_canary_started is True
    assert result.healthy_metrics_promoted is True
    assert result.degrading_metrics_rolled_back is True
    assert result.canonical_repository_modified is False
    assert result.real_github_pr_created is False
    assert result.production_deployment_activated is False
    assert result.production_self_rewrite_activated is False
    assert len(result.outcome_ledger.records) >= 10


class SubprocessGitCommandRunner:
    def run_git(self, cwd: Path, args: Sequence[str]) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()


def _canary_plan() -> CanaryPlan:
    return CanaryPlan(
        plan_id="canary-plan-174",
        proposal_id="proposal-174",
        merge_commit_sha=_sha1("a"),
        deployment_artifact_fingerprint=_sha256("d"),
        exposure_budget=CanaryExposureBudget(
            budget_id="budget-174",
            max_exposure_percentage=5.0,
            max_subjects=10,
            max_duration_minutes=30,
        ),
        monitoring_duration_minutes=30,
        rollback_commit_sha=_sha1("c"),
        metric_thresholds=(
            CanaryMetricThreshold(
                metric_name="task_success",
                threshold=0.8,
                higher_is_better=True,
                rollback_trigger="task_success_degradation",
            ),
            CanaryMetricThreshold(
                metric_name="user_correction_rate",
                threshold=0.1,
                higher_is_better=False,
                rollback_trigger="user_correction_increase",
            ),
            CanaryMetricThreshold(
                metric_name="latency",
                threshold=100.0,
                higher_is_better=False,
                rollback_trigger="latency_budget_breach",
            ),
        ),
        metric_threshold_fingerprint=_sha256("e"),
    )


def _observation(observation_id: str, metrics: tuple[BenchmarkMetric, ...]) -> CanaryObservation:
    return CanaryObservation(
        observation_id=observation_id,
        plan_id="canary-plan-174",
        metrics=metrics,
    )


def _metrics(
    *,
    task_success: float = 1.0,
    user_correction_rate: float = 0.0,
    latency: float = 50.0,
) -> tuple[BenchmarkMetric, ...]:
    values = {
        "task_success": task_success,
        "user_correction_rate": user_correction_rate,
        "latency": latency,
    }
    metrics: list[BenchmarkMetric] = []
    for name in REQUIRED_BENCHMARK_METRICS:
        higher = name in HIGHER_IS_BETTER_METRICS
        value = values.get(name, 1.0 if higher else 0.0)
        threshold = 0.8 if higher else 0.1
        if name == "latency":
            threshold = 100.0
        metrics.append(
            BenchmarkMetric(
                metric_name=name,
                value=value,
                threshold=threshold,
                higher_is_better=higher,
                unit="score" if name not in LOWER_IS_BETTER_METRICS else "count",
            )
        )
    return tuple(metrics)


def _planning_case(case_id: str, tags: tuple[str, ...], score: float) -> PlanningCase:
    return PlanningCase(
        case_id=case_id,
        context_tags=tags,
        plan_template=("check policy", "run regression", "record outcome"),
        success_score=score,
        policy_validated=True,
    )


def _git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "git", "init", "-b", "main")
    _run(repo, "git", "config", "user.email", "aion@example.invalid")
    _run(repo, "git", "config", "user.name", "AION Test")
    (repo / "fixtures").mkdir()
    (repo / "fixtures/retrieval.txt").write_text("baseline\n")
    _run(repo, "git", "add", ".")
    _run(repo, "git", "commit", "-m", "baseline")
    return repo


def _git(cwd: Path, *args: str) -> str:
    return _run(cwd, "git", *args).stdout.strip()


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _sha1(char: str) -> str:
    return char * 40


def _sha256(char: str) -> str:
    return char * 64
