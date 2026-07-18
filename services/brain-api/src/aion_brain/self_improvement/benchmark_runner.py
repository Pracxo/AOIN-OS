"""Deterministic benchmark runner for governed self-improvement candidates."""

from __future__ import annotations

from collections.abc import Iterable

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning_synthesis import LearningSynthesisRun
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.benchmark_contracts import (
    BenchmarkBaseline,
    BenchmarkCandidateResult,
    BenchmarkDriftReport,
    BenchmarkEvaluationBundle,
    BenchmarkManifest,
    BenchmarkMetric,
    BenchmarkSafetyGate,
)
from aion_brain.self_improvement.comparison import compare_baseline_to_candidate
from aion_brain.self_improvement.evaluation_evidence import (
    evaluator_record_refs,
    learning_synthesis_refs,
)
from aion_brain.self_improvement.holdout import assert_holdout_controls


def run_candidate_benchmark(
    *,
    manifest: BenchmarkManifest,
    baseline: BenchmarkBaseline,
    proposal_id: str,
    candidate_result_id: str,
    candidate_metrics: tuple[BenchmarkMetric, ...],
    safety_gate: BenchmarkSafetyGate,
    evaluator_records: Iterable[EvaluationRecord] = (),
    learning_synthesis_runs: Iterable[LearningSynthesisRun] = (),
    candidate_changed_paths: Iterable[str] = (),
    candidate_modified_baseline: bool = False,
    candidate_modified_holdout: bool = False,
) -> BenchmarkCandidateResult:
    """Create a candidate result after enforcing manifest, baseline, and holdout controls."""

    if baseline.manifest_id != manifest.manifest_id:
        raise ValueError("baseline must reference the manifest being evaluated")
    if baseline.manifest_fingerprint != manifest.manifest_fingerprint:
        raise ValueError("baseline manifest fingerprint must match manifest")

    assert_holdout_controls(
        manifest,
        candidate_changed_paths=candidate_changed_paths,
        candidate_modified_baseline=candidate_modified_baseline,
        candidate_modified_holdout=candidate_modified_holdout,
    )

    return BenchmarkCandidateResult(
        candidate_result_id=candidate_result_id,
        proposal_id=proposal_id,
        manifest_id=manifest.manifest_id,
        manifest_fingerprint=manifest.manifest_fingerprint,
        baseline_id=baseline.baseline_id,
        metrics=candidate_metrics,
        safety_gate=safety_gate,
        read_only_evaluator_refs=evaluator_record_refs(evaluator_records),
        read_only_learning_synthesis_refs=learning_synthesis_refs(learning_synthesis_runs),
        candidate_modified_baseline=candidate_modified_baseline,
        candidate_modified_holdout=candidate_modified_holdout,
        created_at=utc_now(),
    )


def build_evaluation_bundle(
    *,
    bundle_id: str,
    manifest: BenchmarkManifest,
    baseline: BenchmarkBaseline,
    candidate_result: BenchmarkCandidateResult,
    comparison_id: str,
    drift_report_id: str,
    provenance_refs: tuple[str, ...] = (),
) -> BenchmarkEvaluationBundle:
    """Build a complete evaluation bundle with fail-closed drift and safety checks."""

    comparison = compare_baseline_to_candidate(
        comparison_id=comparison_id,
        baseline=baseline,
        candidate_result=candidate_result,
    )
    drift_report = BenchmarkDriftReport(
        drift_report_id=drift_report_id,
        manifest_id=manifest.manifest_id,
        baseline_manifest_fingerprint=baseline.manifest_fingerprint,
        current_manifest_fingerprint=manifest.manifest_fingerprint,
        drift_detected=baseline.manifest_fingerprint != manifest.manifest_fingerprint,
        threshold_changes=(),
        threshold_changes_audited=True,
        created_at=utc_now(),
    )
    return BenchmarkEvaluationBundle(
        bundle_id=bundle_id,
        manifest=manifest,
        baseline=baseline,
        candidate_result=candidate_result,
        comparison=comparison,
        drift_report=drift_report,
        provenance_refs=provenance_refs,
        change_eligible=(
            candidate_result.safety_gate.change_eligible
            and comparison.change_eligible
            and not drift_report.drift_detected
        ),
        created_at=utc_now(),
    )


__all__ = ["build_evaluation_bundle", "run_candidate_benchmark"]
