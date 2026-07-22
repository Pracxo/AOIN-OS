# AION-196 Governed Continual Learning

## Task Purpose

AION-196 implements a local governed continual-learning candidate core under
authorization `AION-195-CA-0007`. It creates immutable replay samples, isolated
learning candidates, protected-holdout evaluations, approval-bound promotion
records, and rollback plans. It does not train model weights, promote candidates
automatically, mutate source, call external systems, add runtime routes, or
enable background learning.

## Authorization

- Program ID: `AION-COGNITIVE-ARCHITECTURE-001`
- Authorization ID: `AION-195-CA-0007`
- Authorized task: `AION-196`
- Candidate ID: `governed-continual-learning-core`
- Scope: `governed-continual-learning-replay-adapter-policy-skill-candidate-core`
- Branch: `phase/cognitive-governed-continual-learning`
- Formal closeout task: `AION-197`
- Evaluation ID: `AION-CAE-001`

## Role Comparison

AION-196 is an implementation task. It consumes the AION-195 authorization by
adding contracts, local services, tests, examples, and gates for governed
continual-learning candidates. It does not close `AION-195-CA-0007`; AION-197
performs the integrated evaluation and closeout.

## Source Boundaries

Allowed source paths are limited to:

- `services/brain-api/src/aion_brain/continual_learning/`
- `services/brain-api/src/aion_brain/contracts/continual_learning.py`
- `services/brain-api/tests/test_cognitive_continual_learning.py`
- `services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-continual-learning-check.sh`
- `scripts/cognitive-continual-learning-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

Prohibited paths remain `.github/workflows/`, migrations, package files and
lockfiles, API routes, git automation, pull-request automation, deployment code,
connectors, model providers, credentials, SDK source, and model-weight training
paths.

## Learning Levels

AION-196 implements candidate generation for:

- Memory candidate
- Retrieval-policy candidate
- Planning-policy candidate
- Procedural-skill candidate
- World-model adapter candidate
- Strategy-selection candidate

## Required Contracts

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

- `ExperienceReplayService`
- `CandidateLearningService`
- `CatastrophicForgettingEvaluator`
- `LearningBenchmarkEvaluator`
- `CandidatePromotionPolicy`
- `LearningRollbackService`

## Algorithm

`ExperienceReplayService` selects deterministic replay samples from local
episodes and excludes protected holdout episodes. `CandidateLearningService`
generates isolated versioned candidates for all six learning levels.
`CatastrophicForgettingEvaluator` and `LearningBenchmarkEvaluator` compare each
candidate against the immutable baseline and protected holdout. `CandidatePromotionPolicy`
records operator-review or externally approved promotion requests without
performing promotion. `LearningRollbackService` creates a rollback plan that
keeps the immutable baseline and protected holdout unchanged.

## Required Tests

- `services/brain-api/tests/test_cognitive_continual_learning.py`
- `services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py`

The tests cover immutable fingerprints, secret rejection, replay determinism,
protected holdout exclusion, all six learning candidate levels, candidate
isolation, catastrophic-forgetting checks, approval-bound promotion, self-approval
rejection, rollback availability, script execution, import side effects, and
absence of runtime wiring.

## Required Gates

- `scripts/cognitive-continual-learning-no-go-regression.sh`
- `scripts/cognitive-continual-learning-check.sh`
- inherited information-acquisition closeout gate
- docs check
- final docs audit
- domain-drift validation
- boundary check
- repository health
- full repository check
- `git diff --check`

## Security Invariants

- No API route is added.
- No kernel registration is added.
- No background continual-learning loop is added.
- No network calls are introduced.
- No connector calls are introduced.
- No model-provider calls are introduced.
- No model-weight training is implemented.
- No model weights are changed.
- No candidate is promoted automatically.
- No candidate self-approval is allowed.
- No unauthorized promotion is allowed.
- No protected holdout episode enters replay.
- No source mutation, git mutation, deployment, or production exposure is
  introduced.
- No credentials, tokens, prompt logs, hidden reasoning, raw user messages,
  source patches, raw diffs, holdout content, or private data storage are
  introduced.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

Continual learning remains deterministic and bounded to local in-memory records.
Replay samples operate on explicit `LearningEpisode` inputs. External counters
for network, connector, model-provider, model-weight training, tool, git,
source-mutation, deployment, production exposure, self-approval, unauthorized
promotion, and holdout leakage remain zero.

## Completion Conditions

- AION-196 contracts and services exist under the allowed paths.
- The implementation evidence example validates.
- The program ledger records AION-196 as implemented pending AION-197
  evaluation.
- The authorization ledger updates `AION-195-CA-0007` to implemented pending
  AION-197 evaluation while keeping it active, non-reusable, not expired, and
  not closed.
- Focused tests and no-go gates pass.
- Full repository validation passes before merge.

## Next Task

AION-197 evaluates the integrated cognitive architecture under `AION-CAE-001`
and closes `AION-195-CA-0007` if AION-196 passes its benchmark and boundary
requirements.
