# AION-195 Information-Acquisition Evaluation and Continual-Learning Authorization

## Task Purpose

AION-195 evaluates the AION-194 active information-acquisition implementation
under evaluation `AION-AIAE-001`. On PASS it closes implementation
authorization `AION-193-CA-0006` and creates the next bounded implementation
authorization, `AION-195-CA-0007`, for AION-196 governed continual learning.

This task is an evaluation and authorization checkpoint only. It records local
deterministic evidence and does not implement continual-learning source, add API
runtime paths, enable background loops, acquire information, promote learning
candidates, call external services, execute tools, or change model weights.

## Authorization ID

- Closed authorization ID: `AION-193-CA-0006`
- New authorization ID: `AION-195-CA-0007`
- Evaluation ID: `AION-AIAE-001`
- Evaluated task: `AION-194`
- Implementation PR: `105`
- Implementation merge commit:
  `aeaae23db08c4dfe84e3544e4e393149a54c60cd`

## Exact Scope

AION-195 authorizes AION-196 for exactly:

`governed-continual-learning-replay-adapter-policy-skill-candidate-core`

The authorized implementation branch is
`phase/cognitive-governed-continual-learning`. The formal closeout task is
AION-197 under evaluation `AION-CAE-001`.

## Role Comparison

AION-195 is an evaluation and authorization task, not an implementation task.
It evaluates AION-194 information-acquisition behavior, closes the consumed
information-acquisition authorization, and records a new implementation
authorization. AION-196 is the implementation task that may add governed
continual-learning contracts and local services within the authorized scope.

## Source Boundaries

AION-195 may change only governance, evidence, documentation, tests, and check
scripts:

- `docs/cognitive-architecture/tasks/AION-195.md`
- `docs/cognitive-architecture/program-ledger.json`
- `docs/cognitive-architecture/authorization-ledger.json`
- `examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json`
- `examples/cognitive-architecture/aion-195-continual-learning-authorization.json`
- `services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py`
- `scripts/cognitive-information-acquisition-closeout-check.sh`
- `scripts/cognitive-information-acquisition-closeout-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

AION-195 may not add package files, lockfiles, migrations, workflows, API
runtime execution routes, deployment code, connector runtime paths,
model-provider runtime paths, credential storage, pull-request automation, git
mutation paths, source-rewrite runtime paths, automatic promotion paths,
self-approval paths, or action/tool execution paths.

## Required Contracts

AION-196 is authorized to implement these contracts:

- `ContinualLearningObservation`
- `LearningEpisode`
- `ReplaySample`
- `LearningCandidate`
- `RetrievalPolicyCandidate`
- `PlanningPolicyCandidate`
- `ProceduralSkillCandidate`
- `WorldModelAdapterCandidate`
- `StrategyCandidate`
- `ForgettingRisk`
- `LearningEvaluation`
- `PromotionRequest`
- `LearningRollbackPlan`

## Required Services

AION-196 is authorized to implement these local services:

- `ExperienceReplayService`
- `CandidateLearningService`
- `CatastrophicForgettingEvaluator`
- `LearningBenchmarkEvaluator`
- `CandidatePromotionPolicy`
- `LearningRollbackService`

The implementation must support memory, retrieval-policy, planning-policy,
procedural-skill, world-model-adapter, and strategy-selection candidates.

## Required Tests

- `services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py`

The tests validate the AION-195 evidence artifact against real AION-194 planner
outputs: uncertainty detection, expected information gain, candidate ranking,
cost and risk, clarification quality, stopping decisions, permission
enforcement, no unauthorized acquisition, and no runtime side effects.

## Required Gates

- `scripts/cognitive-information-acquisition-closeout-no-go-regression.sh`
- `scripts/cognitive-information-acquisition-closeout-check.sh`
- inherited information-acquisition gate
- inherited counterfactual-planning closeout gate
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
- No background continual-learning loop is enabled.
- No information is acquired by the evaluator.
- No learning candidate is promoted.
- No promotion request is approved by the system itself.
- No source mutation, git mutation, deployment, production exposure, or
  model-weight change is introduced.
- No model-weight training is authorized.
- No credentials, tokens, private data storage, hidden reasoning, prompt log, raw
  user message, source patch, raw diff, holdout content, or private data storage
  is introduced.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

The AION-195 evaluation uses deterministic local fixtures only. Network,
connector, provider, git, source-rewrite, production-exposure, background-loop,
unauthorized acquisition, automatic promotion, self-approval, and
action/tool-execution counters remain zero.

## Completion Conditions

- AION-194 is recorded as PR `105`, merge commit
  `aeaae23db08c4dfe84e3544e4e393149a54c60cd`, and
  `merged_evaluated_passed`.
- `AION-193-CA-0006` is closed, consumed, expired, and non-reusable.
- `AION-195-CA-0007` is the only active cognitive implementation
  authorization.
- AION-196 scope, contracts, services, source boundaries, resource limits, and
  prohibited behaviors are recorded in the ledgers and authorization artifact.
- Focused tests and no-go gates pass locally and in CI.
- No runtime activation, automatic promotion, or forbidden side effect is
  introduced.

## Next Task

AION-196 implements governed continual-learning candidates under authorization
`AION-195-CA-0007`. Its closeout task is AION-197.
