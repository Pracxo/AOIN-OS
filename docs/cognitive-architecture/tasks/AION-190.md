# AION-190 Memory Consolidation and Replay

## Task Purpose

AION-190 implements the authorized
`episodic-replay-semantic-consolidation-procedural-candidate-core` scope under
implementation authorization `AION-189-CA-0004`.

The implementation adds immutable contracts and pure local services for replay
selection, semantic consolidation candidates, procedural candidates,
contradiction-resolution candidates, non-destructive forgetting candidates, and
operator-review checkpoints. It does not promote candidates, mutate stored
memory, create source rewrites, enable background consolidation, call external
services, or change model weights.

## Authorization

- Authorization ID: `AION-189-CA-0004`
- Authorized task: `AION-190`
- Candidate ID: `memory-consolidation-replay-core`
- Scope: `episodic-replay-semantic-consolidation-procedural-candidate-core`
- Workstream: `memory-consolidation`
- Closeout task: `AION-191`
- Parent evaluation: `AION-GWE-001`
- Parent PR: `99`
- Parent commit: `faee81fd999cf9aca4a889548f3a27796dd7b884`

AION-190 moves the authorization state to
`implemented_pending_aion_191_evaluation`. The authorization remains active,
not consumed, not expired, and non-reusable until AION-191 performs the formal
evaluation closeout.

## Source Boundaries

AION-190 may use only these implementation source paths:

- `services/brain-api/src/aion_brain/memory_consolidation/`
- `services/brain-api/src/aion_brain/contracts/memory_consolidation.py`
- `services/brain-api/tests/test_cognitive_memory_consolidation.py`
- `services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-memory-consolidation-check.sh`
- `scripts/cognitive-memory-consolidation-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

AION-190 may not add or change package files, lockfiles, migrations, workflows,
production API runtime execution routes, deployment code, connector runtime
paths, model-provider runtime paths, credential storage, pull-request
automation, git mutation paths, source-rewrite runtime paths, or kernel runtime
registration.

## Required Contracts

- `EpisodicMemoryReference`
- `ReplayBatch`
- `ConsolidationCandidate`
- `SemanticCandidate`
- `ProceduralCandidate`
- `ContradictionResolutionCandidate`
- `ForgettingCandidate`
- `ConsolidationEvidence`
- `ConsolidationCheckpoint`
- `ConsolidationOutcome`

All contracts are immutable, fingerprinted, explicit about provenance, and
fail closed on runtime side-effect flags.

## Required Services

- `EpisodicReplayPlanner`
- `ReplaySelector`
- `SemanticConsolidator`
- `ProceduralCandidateSynthesizer`
- `ContradictionResolver`
- `MemoryCompactor`
- `ForgettingPolicyEvaluator`
- `ConsolidationService`

All services are local and deterministic. They accept explicit episode inputs
and return review artifacts without persistence, background scheduling, network
access, provider calls, action execution, or deployment behavior.

## Pipeline

1. Operational episodes
2. Replay selection
3. Clustering
4. Contradiction analysis
5. Semantic candidates
6. Procedural candidates
7. Benchmark evidence
8. Operator review
9. Approved promotion by existing governance only

The pipeline ends at an operator-review checkpoint. Candidate promotion remains
blocked unless a later task uses the existing governance chain to approve it.

## Required Tests

- Contract immutability, deterministic fingerprints, and secret rejection.
- Deterministic replay ordering and duplicate rejection.
- Semantic candidate, procedural candidate, contradiction candidate, and
  forgetting candidate generation.
- Evidence floors for retained critical memories, contradiction loss,
  provenance coverage, unauthorized promotions, and forbidden side effects.
- Runtime-boundary tests proving no API route, kernel registration, background
  loop, network call, connector call, provider call, action execution, source
  rewrite, hidden memory mutation, or automatic promotion was added.

## Required Gates

- `services/brain-api/.venv/bin/python -m pytest services/brain-api/tests/test_cognitive_memory_consolidation.py services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py -q`
- `scripts/cognitive-memory-consolidation-check.sh`
- `scripts/cognitive-memory-consolidation-no-go-regression.sh`
- `scripts/cognitive-workspace-closeout-check.sh`
- `scripts/cognitive-workspace-closeout-no-go-regression.sh`
- `scripts/cognitive-global-workspace-check.sh`
- `scripts/auth-design-check.sh`
- `scripts/docs-check.sh`
- `scripts/final-docs-audit.sh`
- `scripts/verify-no-domain-drift.sh`
- `scripts/boundary-check.sh`
- `scripts/check.sh`

## Security Invariants

- No production cognitive runtime is enabled.
- No API runtime execution route is added.
- No kernel runtime registration is added.
- No background consolidation loop is enabled.
- No automatic semantic promotion is allowed.
- No automatic procedural promotion is allowed.
- No source rewrite is allowed.
- No model-weight update is allowed.
- No hidden memory mutation is allowed.
- No deletion is allowed without explicit policy evidence.
- No credentials, tokens, external connectors, or model-provider runtime calls
  are introduced.

## Completion Conditions

AION-190 is complete when:

- The required contracts and services are present in the scoped source paths.
- The replay-to-review pipeline produces deterministic local checkpoints.
- Consolidation candidates require operator review and record no approved
  promotions.
- Forgetting candidates remain non-destructive and require explicit policy
  evidence.
- The program and authorization ledgers record
  `implemented_pending_aion_191_evaluation`.
- AION-190 tests, governance scripts, inherited checks, and repository-wide
  checks pass locally and in CI.
- No runtime activation or forbidden side effect is introduced.

## Next Task

AION-191 evaluates the AION-190 memory-consolidation implementation, closes
authorization `AION-189-CA-0004` on PASS, and authorizes the next cognitive
architecture implementation scope.
