"""Read-only evidence adapters for benchmark evaluation inputs."""

from __future__ import annotations

import statistics
from collections.abc import Iterable
from typing import Any

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning_synthesis import LearningSynthesisRun
from aion_brain.contracts.self_improvement import ImprovementProvenanceRecord, utc_now
from aion_brain.self_improvement.benchmark_contracts import BenchmarkMetric
from aion_brain.self_improvement.evidence import redact_evidence_payload


def evaluator_record_refs(records: Iterable[EvaluationRecord]) -> tuple[str, ...]:
    """Return stable read-only references to evaluator records."""

    return tuple(f"evaluation:{record.evaluation_id}:trace:{record.trace_id}" for record in records)


def learning_synthesis_refs(runs: Iterable[LearningSynthesisRun]) -> tuple[str, ...]:
    """Return stable read-only references to learning-synthesis runs."""

    return tuple(f"learning-synthesis:{run.synthesis_run_id}:{run.status}" for run in runs)


def benchmark_metrics_from_evaluator_records(
    records: Iterable[EvaluationRecord],
    *,
    latency: float = 0.0,
    compute_cost: float = 0.0,
    rollback_count: float = 0.0,
    regression_count: float = 0.0,
) -> tuple[BenchmarkMetric, ...]:
    """Build required benchmark metrics from current evaluator outputs as read-only input."""

    materialized = tuple(records)
    score = _average_scores(materialized)
    policy_violations = sum(
        1 for record in materialized if record.scores.get("policy_compliance_score", 0.0) < 0.8
    )
    return (
        _metric("task_success", score.get("goal_completion_score", 0.0), 0.8, True, "score"),
        _metric(
            "evidence_grounding",
            score.get("evidence_grounding_score", 0.0),
            0.8,
            True,
            "score",
        ),
        _metric("user_correction_rate", 0.0, 0.05, False, "rate"),
        _metric(
            "retrieval_precision",
            score.get("memory_relevance_score", 0.0),
            0.75,
            True,
            "score",
        ),
        _metric("plan_success", score.get("plan_quality_score", 0.0), 0.8, True, "score"),
        _metric("policy_violation_count", float(policy_violations), 0.0, False, "count"),
        _metric("regression_count", regression_count, 0.0, False, "count"),
        _metric("latency", latency, 10.0, False, "seconds"),
        _metric("compute_cost", compute_cost, 1.0, False, "cost_units"),
        _metric("rollback_count", rollback_count, 0.0, False, "count"),
        _metric("improvement_survival", 1.0, 1.0, True, "score"),
    )


def capture_evaluation_provenance(
    *,
    provenance_record_id: str,
    proposal_id: str,
    evaluator_records: Iterable[EvaluationRecord],
    learning_synthesis_runs: Iterable[LearningSynthesisRun],
    summary: str,
) -> ImprovementProvenanceRecord:
    """Create redacted provenance that records only read-only input references."""

    evaluation_refs = evaluator_record_refs(evaluator_records)
    synthesis_refs = learning_synthesis_refs(learning_synthesis_runs)
    input_evidence = redact_evidence_payload(
        {
            "evaluator_refs": evaluation_refs,
            "learning_synthesis_refs": synthesis_refs,
        }
    )
    output_evidence = redact_evidence_payload(
        {
            "read_only_inputs": True,
            "source_mutation_enabled": False,
            "benchmark_mutation_enabled": False,
        }
    )
    return ImprovementProvenanceRecord(
        provenance_record_id=provenance_record_id,
        proposal_id=proposal_id,
        source_refs=(*evaluation_refs, *synthesis_refs),
        redacted_summary=summary,
        input_evidence=input_evidence,
        output_evidence=output_evidence,
        created_at=utc_now(),
    )


def _average_scores(records: tuple[EvaluationRecord, ...]) -> dict[str, float]:
    if not records:
        return {}
    names = sorted({name for record in records for name in record.scores})
    averaged: dict[str, float] = {}
    for name in names:
        values = [record.scores[name] for record in records if name in record.scores]
        averaged[name] = statistics.fmean(values)
    return averaged


def _metric(
    metric_name: Any,
    value: float,
    threshold: float,
    higher_is_better: bool,
    unit: str,
) -> BenchmarkMetric:
    return BenchmarkMetric(
        metric_name=metric_name,
        value=value,
        threshold=threshold,
        higher_is_better=higher_is_better,
        unit=unit,
    )


__all__ = [
    "benchmark_metrics_from_evaluator_records",
    "capture_evaluation_provenance",
    "evaluator_record_refs",
    "learning_synthesis_refs",
]
