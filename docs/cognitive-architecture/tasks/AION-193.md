# AION-193 Planning Evaluation and Information-Acquisition Authorization

## Task Purpose

AION-193 evaluates the AION-192 hierarchical counterfactual planning
implementation under evaluation `AION-HCPE-001`. On PASS it closes
implementation authorization `AION-191-CA-0005` and creates the next bounded
implementation authorization, `AION-193-CA-0006`, for AION-194 active
information acquisition.

This task is an evaluation and authorization checkpoint only. It records local
deterministic evidence and does not implement information-acquisition source,
add API runtime paths, enable background loops, acquire information, call
external services, execute tools, or change model weights.

## Authorization ID

- Closed authorization ID: `AION-191-CA-0005`
- New authorization ID: `AION-193-CA-0006`
- Evaluation ID: `AION-HCPE-001`
- Evaluated task: `AION-192`
- Implementation PR: `103`
- Implementation merge commit:
  `854c5e3fe34eeffa54cb1676e5524e28878cb078`

## Exact Scope

AION-193 authorizes AION-194 for exactly:

`active-information-need-observation-selection-information-gain-stopping-core`

The authorized implementation branch is
`phase/cognitive-active-information-acquisition`. The formal closeout task is
AION-195 under evaluation `AION-AIAE-001`.

## Role Comparison

AION-193 is an evaluation and authorization task, not an implementation task.
It evaluates AION-192 planning behavior, closes the consumed planning
authorization, and records a new implementation authorization. AION-194 is the
implementation task that may add active information-acquisition contracts and
local services within the authorized scope.

## Source Boundaries

AION-193 may change only governance, evidence, documentation, tests, and check
scripts:

- `docs/cognitive-architecture/tasks/AION-193.md`
- `docs/cognitive-architecture/program-ledger.json`
- `docs/cognitive-architecture/authorization-ledger.json`
- `examples/cognitive-architecture/aion-193-counterfactual-planning-evaluation.json`
- `examples/cognitive-architecture/aion-193-information-acquisition-authorization.json`
- `services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py`
- `scripts/cognitive-counterfactual-planning-closeout-check.sh`
- `scripts/cognitive-counterfactual-planning-closeout-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

AION-193 may not add package files, lockfiles, migrations, workflows, API
runtime execution routes, deployment code, connector runtime paths,
model-provider runtime paths, credential storage, pull-request automation, git
mutation paths, source-rewrite runtime paths, or action/tool execution paths.

## Required Contracts

AION-194 is authorized to implement these contracts:

- `InformationNeed`
- `KnowledgeGap`
- `ObservationCandidate`
- `ClarificationCandidate`
- `RetrievalCandidate`
- `ExperimentCandidate`
- `ExpectedInformationGain`
- `AcquisitionCost`
- `AcquisitionRisk`
- `InformationAcquisitionPlan`
- `InformationStoppingDecision`
- `InformationAcquisitionEvidence`

## Required Services

AION-194 is authorized to implement these local services:

- `KnowledgeGapDetector`
- `ObservationCandidateGenerator`
- `InformationGainEstimator`
- `AcquisitionCostEvaluator`
- `AcquisitionRiskEvaluator`
- `ClarificationPolicy`
- `InformationStoppingPolicy`
- `InformationAcquisitionPlanner`

The required decision is: What information would reduce decision-relevant
uncertainty enough to justify its cost and risk?

## Required Tests

- `services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py`

The tests validate the AION-193 evidence artifact against real AION-192 planner
outputs: goal decomposition, cross-level consistency, world-model rollouts,
counterfactual branch comparison, resource and risk constraints, reversibility,
replanning after changed observations, deterministic replay, and no action
execution.

## Required Gates

- `scripts/cognitive-counterfactual-planning-closeout-no-go-regression.sh`
- `scripts/cognitive-counterfactual-planning-closeout-check.sh`
- inherited counterfactual-planning gate
- inherited memory-consolidation closeout gate
- docs check
- final docs audit
- domain-drift validation
- boundary check
- repository health
- full repository check
- `git diff --check`

## Security Invariants

- No production cognitive runtime is enabled.
- No API runtime execution route is added.
- No kernel runtime registration is added.
- No background information-acquisition loop is enabled.
- No arbitrary URL access is allowed.
- No connector call is allowed.
- No provider call is allowed.
- No tool execution is allowed.
- No information acquisition may occur without permission.
- No acquisition may continue when expected value falls below cost.
- No credentials, tokens, private data storage, hidden reasoning, prompt log, raw
  user message, source patch, or raw diff storage is introduced.
- No source rewrite, git mutation, deployment, production exposure, or
  model-weight change is introduced.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

The AION-193 evaluation uses deterministic local fixtures only. Network,
connector, provider, git, source-rewrite, production-exposure, background-loop,
unauthorized information-acquisition, and action/tool-execution counters remain
zero.

## Completion Conditions

- AION-192 is recorded as PR `103`, merge commit
  `854c5e3fe34eeffa54cb1676e5524e28878cb078`, and
  `merged_evaluated_passed`.
- `AION-191-CA-0005` is closed, consumed, expired, and non-reusable.
- `AION-193-CA-0006` is the only active cognitive implementation
  authorization.
- AION-194 scope, contracts, services, source boundaries, resource limits, and
  prohibited behaviors are recorded in the ledgers and authorization artifact.
- Focused tests and no-go gates pass locally and in CI.
- No runtime activation or forbidden side effect is introduced.

## Next Task

AION-194 implements the authorized
`active-information-need-observation-selection-information-gain-stopping-core`
scope under authorization `AION-193-CA-0006`. Its closeout task is AION-195.
