"""Governed self-improvement control-plane services."""

from aion_brain.self_improvement.approval import bind_human_approval
from aion_brain.self_improvement.benchmark_contracts import (
    EVALUATION_AUTHORIZATION_SCOPE,
    EVALUATION_AUTHORIZATION_TRANSACTION_ID,
    EVALUATION_IMPLEMENTATION_TASK,
    REQUIRED_BENCHMARK_METRICS,
    BenchmarkBaseline,
    BenchmarkCandidateResult,
    BenchmarkCaseReference,
    BenchmarkComparison,
    BenchmarkDriftReport,
    BenchmarkEvaluationBundle,
    BenchmarkManifest,
    BenchmarkMetric,
    BenchmarkMetricDelta,
    BenchmarkSafetyGate,
)
from aion_brain.self_improvement.benchmark_registry import BenchmarkRegistry
from aion_brain.self_improvement.benchmark_runner import (
    build_evaluation_bundle,
    run_candidate_benchmark,
)
from aion_brain.self_improvement.change_budget import evaluate_change_budget
from aion_brain.self_improvement.comparison import compare_baseline_to_candidate
from aion_brain.self_improvement.evaluation_evidence import (
    benchmark_metrics_from_evaluator_records,
    capture_evaluation_provenance,
)
from aion_brain.self_improvement.evidence import redact_evidence_payload
from aion_brain.self_improvement.experiment import (
    ApprovalTier,
    ImprovementEvidenceBundle,
    ImprovementExperimentPlan,
    ImprovementExperimentResult,
    ImprovementProposal,
    ProposalLifecycleState,
    approval_tier_for_risk,
)
from aion_brain.self_improvement.experiment_runner import (
    DeterministicExperimentCandidateProvider,
    DisabledExperimentCandidateProvider,
    ExperimentCandidateProvider,
    ImprovementExperimentRunner,
)
from aion_brain.self_improvement.governance import evaluate_governance
from aion_brain.self_improvement.holdout import (
    assert_holdout_controls,
    patch_generator_case_ids,
)
from aion_brain.self_improvement.hypothesis import (
    DeterministicTestHypothesisGenerator,
    DisabledHypothesisGenerator,
    HypothesisGenerator,
    ImprovementChangeType,
    ImprovementHypothesis,
    MetricDirection,
)
from aion_brain.self_improvement.ledger import SelfImprovementLedger
from aion_brain.self_improvement.lifecycle import (
    can_transition,
    require_valid_transition,
    transition_state,
)
from aion_brain.self_improvement.observation import (
    EXPERIMENT_AUTHORIZATION_SCOPE,
    EXPERIMENT_AUTHORIZATION_TRANSACTION_ID,
    EXPERIMENT_IMPLEMENTATION_TASK,
    ImprovementObservation,
    ObservationSourceType,
    observation_from_evaluation_record,
)
from aion_brain.self_improvement.pattern_intake import (
    ImprovementFailurePattern,
    ImprovementFailurePatternType,
    intake_failure_pattern,
)
from aion_brain.self_improvement.proposal_service import ImprovementProposalService
from aion_brain.self_improvement.protected_paths import (
    protected_path_decision,
    protected_path_decisions,
    touches_protected_core,
)
from aion_brain.self_improvement.regression_proposal import (
    DeterministicTestRegressionProposalGenerator,
    DisabledRegressionTestProposalGenerator,
    RegressionTestProposal,
    RegressionTestProposalGenerator,
)
from aion_brain.self_improvement.risk import assess_improvement_risk

__all__ = [
    "EVALUATION_AUTHORIZATION_SCOPE",
    "EVALUATION_AUTHORIZATION_TRANSACTION_ID",
    "EVALUATION_IMPLEMENTATION_TASK",
    "EXPERIMENT_AUTHORIZATION_SCOPE",
    "EXPERIMENT_AUTHORIZATION_TRANSACTION_ID",
    "EXPERIMENT_IMPLEMENTATION_TASK",
    "REQUIRED_BENCHMARK_METRICS",
    "ApprovalTier",
    "BenchmarkBaseline",
    "BenchmarkCandidateResult",
    "BenchmarkCaseReference",
    "BenchmarkComparison",
    "BenchmarkDriftReport",
    "BenchmarkEvaluationBundle",
    "BenchmarkManifest",
    "BenchmarkMetric",
    "BenchmarkMetricDelta",
    "BenchmarkRegistry",
    "BenchmarkSafetyGate",
    "DeterministicExperimentCandidateProvider",
    "DeterministicTestHypothesisGenerator",
    "DeterministicTestRegressionProposalGenerator",
    "DisabledExperimentCandidateProvider",
    "DisabledHypothesisGenerator",
    "DisabledRegressionTestProposalGenerator",
    "ExperimentCandidateProvider",
    "HypothesisGenerator",
    "ImprovementChangeType",
    "ImprovementEvidenceBundle",
    "ImprovementExperimentPlan",
    "ImprovementExperimentResult",
    "ImprovementFailurePattern",
    "ImprovementFailurePatternType",
    "ImprovementHypothesis",
    "ImprovementObservation",
    "ImprovementProposal",
    "ImprovementProposalService",
    "ImprovementExperimentRunner",
    "MetricDirection",
    "ObservationSourceType",
    "ProposalLifecycleState",
    "RegressionTestProposal",
    "RegressionTestProposalGenerator",
    "SelfImprovementLedger",
    "approval_tier_for_risk",
    "assess_improvement_risk",
    "assert_holdout_controls",
    "benchmark_metrics_from_evaluator_records",
    "bind_human_approval",
    "can_transition",
    "build_evaluation_bundle",
    "capture_evaluation_provenance",
    "compare_baseline_to_candidate",
    "evaluate_change_budget",
    "evaluate_governance",
    "intake_failure_pattern",
    "observation_from_evaluation_record",
    "patch_generator_case_ids",
    "protected_path_decision",
    "protected_path_decisions",
    "redact_evidence_payload",
    "require_valid_transition",
    "run_candidate_benchmark",
    "touches_protected_core",
    "transition_state",
]
