from __future__ import annotations

import time
from typing import Any

import pytest
from pydantic import ValidationError

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning_synthesis import LearningSynthesisRun
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement import (
    EVALUATION_AUTHORIZATION_SCOPE,
    EVALUATION_AUTHORIZATION_TRANSACTION_ID,
    EVALUATION_IMPLEMENTATION_TASK,
    BenchmarkBaseline,
    BenchmarkCaseReference,
    BenchmarkComparison,
    BenchmarkDriftReport,
    BenchmarkManifest,
    BenchmarkMetric,
    BenchmarkMetricDelta,
    BenchmarkSafetyGate,
    build_evaluation_bundle,
    run_candidate_benchmark,
)
from aion_brain.self_improvement.benchmark_contracts import (
    REQUIRED_BENCHMARK_METRICS,
    BenchmarkMetricName,
    manifest_fingerprint,
    sha256_json,
)
from aion_brain.self_improvement.comparison import (
    compare_baseline_to_candidate,
    deterministic_paired_delta_interval,
)
from aion_brain.self_improvement.evaluation_evidence import (
    benchmark_metrics_from_evaluator_records,
    capture_evaluation_provenance,
)
from aion_brain.self_improvement.holdout import (
    assert_holdout_controls,
    opaque_case_id,
    patch_generator_case_ids,
)


def test_aion168_contract_constants_match_evaluation_authorization() -> None:
    assert EVALUATION_AUTHORIZATION_TRANSACTION_ID == "AION-167-SI-0002"
    assert EVALUATION_IMPLEMENTATION_TASK == "AION-168"
    assert EVALUATION_AUTHORIZATION_SCOPE == "immutable-self-improvement-evaluation-plane"
    assert REQUIRED_BENCHMARK_METRICS == (
        "task_success",
        "evidence_grounding",
        "user_correction_rate",
        "retrieval_precision",
        "plan_success",
        "policy_violation_count",
        "regression_count",
        "latency",
        "compute_cost",
        "rollback_count",
        "improvement_survival",
    )


def test_benchmark_manifest_is_immutable_fingerprinted_and_strict() -> None:
    manifest = benchmark_manifest()

    assert len(manifest.manifest_fingerprint) == 64
    assert manifest.manifest_fingerprint == manifest_fingerprint(manifest)
    with pytest.raises(ValidationError):
        BenchmarkMetric.model_validate(
            {
                "metric_name": "task_success",
                "value": 1.0,
                "threshold": 0.8,
                "higher_is_better": True,
                "unit": "score",
                "unexpected": True,
            }
        )
    with pytest.raises(ValidationError):
        manifest.manifest_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError, match="full AION-168 required metric set"):
        BenchmarkManifest(
            manifest_id="manifest-missing-metric",
            benchmark_version="2026-07-18",
            case_references=manifest.case_references,
            metric_definitions=manifest.metric_definitions[:-1],
            created_at=utc_now(),
        )
    with pytest.raises(ValidationError, match="manifest_fingerprint"):
        BenchmarkManifest(
            manifest_id="manifest-bad-fingerprint",
            benchmark_version="2026-07-18",
            case_references=manifest.case_references,
            metric_definitions=manifest.metric_definitions,
            manifest_fingerprint="0" * 64,
            created_at=utc_now(),
        )


def test_hard_gate_formula_is_exact_and_quality_cannot_offset_safety() -> None:
    gate = safety_gate()
    assert gate.change_eligible is True

    with pytest.raises(ValidationError, match="hard safety-gate formula"):
        BenchmarkSafetyGate(
            all_required_tests_pass=False,
            all_security_checks_pass=True,
            all_policy_checks_pass=True,
            protected_boundaries_pass=True,
            holdout_score_meets_threshold=True,
            no_critical_regression=True,
            rollback_plan_present=True,
            change_eligible=True,
        )

    with pytest.raises(ValidationError, match="quality gains must never offset safety failures"):
        BenchmarkComparison(
            comparison_id="comparison-unsafe",
            baseline_id="baseline-001",
            candidate_result_id="candidate-001",
            metric_deltas=(
                BenchmarkMetricDelta(
                    metric_name="task_success",
                    baseline_value=0.1,
                    candidate_value=1.0,
                    delta=0.9,
                    improved=True,
                ),
            ),
            baseline_quality_score=0.1,
            candidate_quality_score=1.0,
            quality_score_delta=0.9,
            confidence_interval_low=0.9,
            confidence_interval_high=0.9,
            safety_passed=False,
            change_eligible=True,
            created_at=utc_now(),
        )


def test_holdout_controls_expose_only_opaque_ids_and_block_tampering() -> None:
    manifest = benchmark_manifest()
    exposed = patch_generator_case_ids(manifest)

    assert exposed == (manifest.case_references[0].opaque_case_id,)
    assert manifest.case_references[0].holdout_path not in exposed

    assert_holdout_controls(manifest, candidate_changed_paths=("services/brain-api/tests/x.py",))
    with pytest.raises(ValueError, match="cannot modify the holdout"):
        assert_holdout_controls(
            manifest,
            candidate_changed_paths=("docs/self-improvement/holdout/hidden-case.json",),
        )
    with pytest.raises(ValueError, match="cannot update its own baseline"):
        assert_holdout_controls(
            manifest,
            candidate_changed_paths=(),
            candidate_modified_baseline=True,
        )
    with pytest.raises(ValidationError, match="protected holdout boundary"):
        BenchmarkCaseReference(
            opaque_case_id=opaque_case_id(manifest_id="manifest", raw_case_id="case"),
            case_family="tamper",
            hidden=True,
            holdout_path="docs/public/hidden-case.json",
            content_fingerprint=sha256_json({"case": "tamper"}),
        )


def test_drift_reports_require_audited_threshold_changes() -> None:
    manifest = benchmark_manifest()
    changed_fingerprint = sha256_json({"manifest": "changed"})

    with pytest.raises(ValidationError, match="drift_detected"):
        BenchmarkDriftReport(
            drift_report_id="drift-bad",
            manifest_id=manifest.manifest_id,
            baseline_manifest_fingerprint=manifest.manifest_fingerprint,
            current_manifest_fingerprint=changed_fingerprint,
            drift_detected=False,
            threshold_changes=(),
            threshold_changes_audited=True,
            created_at=utc_now(),
        )
    with pytest.raises(ValidationError, match="threshold changes must be audited"):
        BenchmarkDriftReport(
            drift_report_id="drift-threshold",
            manifest_id=manifest.manifest_id,
            baseline_manifest_fingerprint=manifest.manifest_fingerprint,
            current_manifest_fingerprint=changed_fingerprint,
            drift_detected=True,
            threshold_changes=("task_success threshold changed",),
            threshold_changes_audited=False,
            created_at=utc_now(),
        )


def test_runner_builds_eligible_bundle_from_read_only_evaluator_and_synthesis_inputs() -> None:
    manifest = benchmark_manifest()
    baseline = benchmark_baseline(manifest, metrics=metric_set(task_success=0.7))
    evaluator_record = EvaluationRecord(
        evaluation_id="evaluation-001",
        trace_id="trace-001",
        scores={
            "goal_completion_score": 0.92,
            "evidence_grounding_score": 0.91,
            "memory_relevance_score": 0.88,
            "plan_quality_score": 0.9,
            "policy_compliance_score": 0.95,
        },
        lessons=["deterministic_loop_completed"],
        created_at=utc_now(),
    )
    synthesis_run = LearningSynthesisRun(
        synthesis_run_id="synthesis-001",
        status="dry_run",
        mode="dry_run",
        owner_scope=["workspace:main"],
        created_at=utc_now(),
    )
    candidate_metrics = benchmark_metrics_from_evaluator_records(
        (evaluator_record,),
        latency=4.0,
        compute_cost=0.2,
    )

    candidate = run_candidate_benchmark(
        manifest=manifest,
        baseline=baseline,
        proposal_id="proposal-001",
        candidate_result_id="candidate-001",
        candidate_metrics=candidate_metrics,
        safety_gate=safety_gate(),
        evaluator_records=(evaluator_record,),
        learning_synthesis_runs=(synthesis_run,),
        candidate_changed_paths=("services/brain-api/tests/test_generated_regression.py",),
    )
    bundle = build_evaluation_bundle(
        bundle_id="bundle-001",
        manifest=manifest,
        baseline=baseline,
        candidate_result=candidate,
        comparison_id="comparison-001",
        drift_report_id="drift-001",
    )
    provenance = capture_evaluation_provenance(
        provenance_record_id="provenance-001",
        proposal_id="proposal-001",
        evaluator_records=(evaluator_record,),
        learning_synthesis_runs=(synthesis_run,),
        summary="Read-only evaluation evidence captured for benchmark comparison.",
    )

    assert candidate.read_only_evaluator_refs == ("evaluation:evaluation-001:trace:trace-001",)
    assert candidate.read_only_learning_synthesis_refs == (
        "learning-synthesis:synthesis-001:dry_run",
    )
    assert bundle.change_eligible is True
    assert bundle.comparison.quality_score_delta > 0.0
    assert provenance.output_evidence["read_only_inputs"] is True


def test_deterministic_comparison_interval_and_performance_are_stable() -> None:
    mean_delta, interval_low, interval_high = deterministic_paired_delta_interval(
        [1.0, 2.0, 3.0],
        [2.0, 3.0, 4.0],
    )
    assert mean_delta == 1.0
    assert interval_low == 1.0
    assert interval_high == 1.0

    manifest = benchmark_manifest()
    baseline = benchmark_baseline(manifest, metrics=metric_set(task_success=0.8))
    candidate = run_candidate_benchmark(
        manifest=manifest,
        baseline=baseline,
        proposal_id="proposal-performance",
        candidate_result_id="candidate-performance",
        candidate_metrics=metric_set(task_success=0.9, latency=3.0, compute_cost=0.2),
        safety_gate=safety_gate(),
    )

    started = time.perf_counter()
    for index in range(100):
        comparison = compare_baseline_to_candidate(
            comparison_id=f"comparison-performance-{index}",
            baseline=baseline,
            candidate_result=candidate,
        )
        assert comparison.change_eligible is True
    assert time.perf_counter() - started < 2.0


def benchmark_manifest() -> BenchmarkManifest:
    return BenchmarkManifest(
        manifest_id="self-improvement-benchmark-v1",
        benchmark_version="2026-07-18",
        case_references=(
            BenchmarkCaseReference(
                opaque_case_id=opaque_case_id(
                    manifest_id="self-improvement-benchmark-v1",
                    raw_case_id="hidden-case-001",
                ),
                case_family="policy-regression",
                hidden=True,
                holdout_path="docs/self-improvement/holdout/aion-168-hidden-case-001.json",
                content_fingerprint=sha256_json({"case": "hidden-case-001"}),
                metadata={"content_stored_separately": True},
            ),
        ),
        metric_definitions=metric_set(),
        created_at=utc_now(),
    )


def benchmark_baseline(
    manifest: BenchmarkManifest,
    *,
    metrics: tuple[BenchmarkMetric, ...],
) -> BenchmarkBaseline:
    return BenchmarkBaseline(
        baseline_id="baseline-001",
        manifest_id=manifest.manifest_id,
        manifest_fingerprint=manifest.manifest_fingerprint,
        metrics=metrics,
        evaluator_refs=("evaluation:baseline:trace",),
        learning_synthesis_refs=("learning-synthesis:baseline:dry_run",),
        created_at=utc_now(),
    )


def safety_gate() -> BenchmarkSafetyGate:
    return BenchmarkSafetyGate(
        all_required_tests_pass=True,
        all_security_checks_pass=True,
        all_policy_checks_pass=True,
        protected_boundaries_pass=True,
        holdout_score_meets_threshold=True,
        no_critical_regression=True,
        rollback_plan_present=True,
        change_eligible=True,
        rollback_plan_ref="rollback-plan-001",
    )


def metric_set(**overrides: float) -> tuple[BenchmarkMetric, ...]:
    values: dict[BenchmarkMetricName, float] = {
        "task_success": 0.85,
        "evidence_grounding": 0.85,
        "user_correction_rate": 0.02,
        "retrieval_precision": 0.84,
        "plan_success": 0.86,
        "policy_violation_count": 0.0,
        "regression_count": 0.0,
        "latency": 5.0,
        "compute_cost": 0.5,
        "rollback_count": 0.0,
        "improvement_survival": 1.0,
    }
    values.update(overrides)  # type: ignore[arg-type]
    return tuple(_metric(name, values[name]) for name in REQUIRED_BENCHMARK_METRICS)


def _metric(metric_name: BenchmarkMetricName, value: float) -> BenchmarkMetric:
    thresholds: dict[BenchmarkMetricName, float] = {
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
    lower_is_better = {
        "user_correction_rate",
        "policy_violation_count",
        "regression_count",
        "latency",
        "compute_cost",
        "rollback_count",
    }
    units: dict[BenchmarkMetricName, str] = {
        "task_success": "score",
        "evidence_grounding": "score",
        "user_correction_rate": "rate",
        "retrieval_precision": "score",
        "plan_success": "score",
        "policy_violation_count": "count",
        "regression_count": "count",
        "latency": "seconds",
        "compute_cost": "cost_units",
        "rollback_count": "count",
        "improvement_survival": "score",
    }
    return BenchmarkMetric(
        metric_name=metric_name,
        value=value,
        threshold=thresholds[metric_name],
        higher_is_better=metric_name not in lower_is_better,
        unit=units[metric_name],
    )


def test_fixture_manifest_payload_has_no_holdout_content() -> None:
    manifest = benchmark_manifest()
    payload: dict[str, Any] = manifest.model_dump(mode="json")
    serialized = str(payload)

    assert "hidden-case-001" not in patch_generator_case_ids(manifest)[0]
    assert "prompt" not in serialized.lower()
    assert "chain-of-thought" not in serialized.lower()
