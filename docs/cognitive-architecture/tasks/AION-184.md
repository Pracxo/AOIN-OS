# AION-184 Persistent Cognitive State

## Task Purpose

AION-184 implements the persistent cognitive-state core authorized by
AION-183-CA-0001. The work provides immutable contracts, append-only event
storage, deterministic replay, checkpoint verification, and local explicit
persistence for belief, goal, hypothesis, uncertainty, resource, contradiction,
and action-effect state.

## Authorization

- Authorization ID: AION-183-CA-0001
- Program ID: AION-COGNITIVE-ARCHITECTURE-001
- Candidate ID: persistent-cognitive-state-core
- Scope: persistent-cognitive-state-belief-goal-hypothesis-uncertainty-resource-core
- Workstream: persistent-cognitive-state

## Role Comparison

AION-184 is an implementation task. It consumes the AION-183 implementation
authorization by adding disabled, local-only cognitive-state primitives. It does
not close the authorization; AION-185 performs the formal evaluation closeout
and, on PASS, may issue the next authorization.

## Source Boundaries

Allowed source paths:

- services/brain-api/src/aion_brain/cognitive_architecture/
- services/brain-api/src/aion_brain/contracts/cognitive_state.py
- services/brain-api/tests/test_cognitive_persistent_state.py
- services/brain-api/tests/test_cognitive_persistent_state_repository.py
- services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py
- docs/cognitive-architecture/
- examples/cognitive-architecture/
- scripts/cognitive-persistent-state-check.sh
- scripts/cognitive-persistent-state-no-go-regression.sh
- scripts/lib/cognitive_architecture_governance.py

Prohibited source paths:

- API routes
- kernel runtime registration
- deployment, PR, merge, Git, connector, credential, or provider controllers
- package and lock files
- migrations

## Required Contracts

- CognitiveStateSnapshot
- BeliefRecord
- BeliefRevision
- GoalFocus
- OpenHypothesis
- UncertaintyRecord
- ExpectedActionEffect
- ObservedActionEffect
- ResourceState
- ContradictionRecord
- CognitiveEvent
- CognitiveStateTransition
- CognitiveStateCheckpoint
- CognitiveStateProvenance

## Required Services

- CognitiveStateProjector
- CognitiveStateRepository protocol
- InMemoryCognitiveStateRepository
- ExplicitLocalCognitiveStateRepository
- CognitiveStateService
- ContradictionDetector
- BeliefRevisionService
- UncertaintyTracker

## Required Tests

- crash-safe replay
- duplicate event rejection
- stale version rejection
- concurrent writers
- contradiction detection
- belief revision
- uncertainty increase and reduction
- checkpoint corruption
- provenance
- retention
- repository-path rejection
- deterministic fingerprints
- performance smoke

## Required Gates

- services/brain-api/.venv/bin/python -m pytest services/brain-api/tests/test_cognitive_persistent_state.py services/brain-api/tests/test_cognitive_persistent_state_repository.py services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py -q
- ./scripts/cognitive-persistent-state-no-go-regression.sh
- ./scripts/cognitive-persistent-state-check.sh
- repository lint, typecheck, docs, final audit, domain-drift, boundary, repository-health, and full check
- git diff --check

## Security Invariants

- runtime_effect=false
- source_modified=false
- git_mutated=false
- pull_request_created=false
- approval_created=false
- merged=false
- production_exposure=false
- model_weights_changed=false
- no background loop
- no direct action execution
- no default hidden persistence path
- no secrets, raw prompts, hidden reasoning, raw diffs, or unredacted personal data in evidence

## Performance Limits

- maximum_events_per_replay_test: 1000
- maximum_snapshot_bytes: 1048576
- maximum_checkpoint_bytes: 1048576
- maximum_test_wall_clock_seconds: 120
- maximum_local_sqlite_files: 1

## Completion Conditions

- immutable contracts are present
- event application is append-only, idempotent, and monotonic
- stale writes are rejected
- deterministic replay and checkpoint restore are verified
- explicit local SQLite persistence is opt-in and path guarded
- no API route, kernel registration, background loop, external call, package file, lockfile, migration, or runtime activation is added
- AION-184 PR merges after all required checks pass

## Next Task

AION-185 evaluates AION-184, closes AION-183-CA-0001 on PASS, and authorizes
AION-186 predictive world-model implementation.
