# AION-186 Predictive World Model

## Task Purpose

AION-186 implements the first predictive world-model core for the AION cognitive architecture program. The work adds immutable contracts and pure local services for transition prediction, outcome uncertainty, causal hypotheses, and counterfactual rollouts.

## Authorization

- Authorization ID: AION-185-CA-0002
- Authorized task: AION-186
- Candidate: predictive-world-model-core
- Scope: predictive-world-model-transition-outcome-uncertainty-counterfactual-core
- Formal closeout task: AION-187

## Source Boundaries

Allowed source paths are limited to the world-model contracts, the `aion_brain.world_model` package, focused tests, examples, documentation, and governance scripts named by AION-185-CA-0002.

The task does not add API routes, kernel registration, migrations, workflow files, package files, connector code, deployment code, credential handling, provider calls, network calls, or model-weight training.

## Required Contracts

- WorldState
- WorldObservation
- WorldActionReference
- TransitionEvidence
- TransitionPrediction
- OutcomePrediction
- UncertaintyEstimate
- CausalHypothesis
- CounterfactualScenario
- CounterfactualRollout
- WorldModelSnapshot
- WorldModelEvaluation

## Required Services

- WorldStateEncoder
- TransitionModel protocol
- DeterministicTransitionModel
- ProbabilisticTransitionModel
- OutcomePredictor
- UncertaintyEstimator
- CausalHypothesisService
- CounterfactualSimulator
- WorldModelRepository protocol

## Algorithm

The initial implementation uses deterministic observed transition counts. The probabilistic model groups evidence by encoded source state and action, applies bounded additive smoothing over observed outcomes, normalizes probabilities to a maximum sum error of `1e-9`, and records confidence intervals from observed support counts.

The deterministic model uses the same evidence index and selects the highest-support outcome with deterministic tie breaking.

Unknown source-state and action pairs fail closed with no exposed outcome distribution. Counterfactual rollouts multiply branch probabilities over proposed action references without executing any action.

## Required Tests

Focused tests cover immutable contracts, fingerprint stability, secret-like payload rejection, append-only evidence storage, probability normalization, multiple possible futures, unknown-state fail-closed behavior, causal-hypothesis provenance, action-effect comparison, reversible and irreversible flags, counterfactual branches, deterministic replay, and import safety.

## Required Gates

- `scripts/cognitive-world-model-check.sh`
- `scripts/cognitive-world-model-no-go-regression.sh`
- focused Brain API pytest for predictive world-model tests
- inherited documentation, domain, boundary, and repository hygiene checks outside nested gate contexts

## Security Invariants

- Production cognitive runtime remains disabled.
- Runtime action execution remains disabled.
- Network, connector, and model-provider calls remain zero.
- API route and kernel registration are absent.
- Package files, migrations, and workflow files are unchanged.
- `aion-v0.1.0` remains untouched.
- No v0.2 tag or release is created.

## Completion Conditions

AION-186 is complete when the implementation is merged, focused gates pass, CI passes, the branch is cleaned up, and the program remains in `predictive_world_model_implemented_pending_evaluation` for AION-187.

## Next Task

AION-187 evaluates the predictive world model under AION-PWME-001, closes AION-185-CA-0002 on PASS, and may authorize AION-188 for the global cognitive workspace.
