# AION-183 Program Charter and Persistent-State Authorization

## Task Purpose

AION-183 establishes `AION-COGNITIVE-ARCHITECTURE-001` as a governed functional-cognition program and creates exactly one active implementation authorization for AION-184.

## Authorization ID

`AION-183-CA-0001`

## Exact Scope

Authorize AION-184 to implement persistent cognitive-state contracts and services for belief, goal, hypothesis, uncertainty, resource, contradiction, action-effect, snapshot, checkpoint, replay, provenance, and explicit local persistence behavior.

## Role Comparison

AION-183 is an authorization and charter task. AION-184 is the implementation task. AION-185 is the evaluation and formal closeout task for this authorization.

## Source Boundaries

Allowed source paths for AION-184 are limited to:

- `services/brain-api/src/aion_brain/cognitive_architecture/`
- `services/brain-api/src/aion_brain/contracts/cognitive_state.py`
- `services/brain-api/tests/test_cognitive_persistent_state.py`
- `services/brain-api/tests/test_cognitive_persistent_state_repository.py`
- `services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-persistent-state-check.sh`
- `scripts/cognitive-persistent-state-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

Prohibited paths include Git controllers, pull-request controllers, merge controllers, deployment controllers, production canary controllers, credential stores, unrestricted connector adapters, unrestricted provider clients, workflow files, package manifests, migrations, and API routes.

## Required Contracts

- `CognitiveStateSnapshot`
- `BeliefRecord`
- `BeliefRevision`
- `GoalFocus`
- `OpenHypothesis`
- `UncertaintyRecord`
- `ExpectedActionEffect`
- `ObservedActionEffect`
- `ResourceState`
- `ContradictionRecord`
- `CognitiveEvent`
- `CognitiveStateTransition`
- `CognitiveStateCheckpoint`
- `CognitiveStateProvenance`

## Required Services

- `CognitiveStateProjector`
- `CognitiveStateRepository`
- `InMemoryCognitiveStateRepository`
- `ExplicitLocalCognitiveStateRepository`
- `CognitiveStateService`
- `ContradictionDetector`
- `BeliefRevisionService`
- `UncertaintyTracker`

## Required Tests

AION-184 must cover deterministic replay, duplicate event rejection, stale version rejection, concurrent writers, contradiction detection, belief revision, uncertainty increase and reduction, checkpoint corruption, provenance, retention, repository-path rejection, deterministic fingerprints, and a performance smoke test.

## Required Gates

- focused persistent-state tests
- inherited self-improvement runtime holds
- cognitive persistent-state no-go gate
- cognitive persistent-state implementation gate
- docs checks
- final docs audit
- no-domain-drift validation
- boundary checks
- repository-health checks
- one full `./scripts/check.sh` on the final task head
- `git diff --check`
- cached diff check

## Security Invariants

Until a later exact authorization changes one bounded field, every cognitive service must preserve:

- `runtime_effect=false`
- `source_modified=false`
- `git_mutated=false`
- `pull_request_created=false`
- `approval_created=false`
- `merged=false`
- `production_exposure=false`
- `model_weights_changed=false`

The program excludes biological, subjective-state, identity, and personality simulation. Machine salience, uncertainty, information gain, reversibility, risk, resource pressure, and goal progress may be used only as functional control signals.

## Performance Limits

AION-184 must keep local deterministic tests under bounded memory and wall-clock budgets, with the performance smoke test proving replay and checkpoint operations remain stable on the synthetic workload declared in the authorization ledger.

## Completion Conditions

AION-183 is complete when the program ledger, authorization ledger, roadmap, security boundary, operator model, focused tests, and authorization gate are merged to `main`, with exactly one active implementation authorization for AION-184 and all runtime effect flags still false.

## Next Task

`AION-184`
