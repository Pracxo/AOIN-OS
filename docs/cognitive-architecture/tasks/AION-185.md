# AION-185 Persistent-State Evaluation and World-Model Authorization

## Task Purpose

AION-185 evaluates the AION-184 persistent cognitive-state implementation,
formally closes `AION-183-CA-0001`, and creates the next bounded implementation
authorization for AION-186 predictive world-model work.

## Evaluation

- Evaluation ID: `AION-PCSE-001`
- Evaluated task: `AION-184`
- Evaluated implementation PR: `#95`
- Evaluated implementation merge commit:
  `9482a148d2a71862a69d8187ea2649b7ca8f8061`
- Decision: `PERSISTENT_STATE_EVALUATION_PASS_AUTHORIZE_WORLD_MODEL`

## Closed Authorization

`AION-183-CA-0001` is closed by AION-185 after AION-184 passed persistent-state
evaluation. The authorization is inactive, consumed, expired, and non-reusable.
The consuming implementation task is AION-184 and the formal closeout task is
AION-185.

## Hard PASS Conditions

- replay equality rate: 100%
- state invariant violations: 0
- lost committed events: 0
- duplicate applied events: 0
- forbidden side effects: 0

## New Authorization

AION-185 creates exactly one active implementation authorization:
`AION-185-CA-0002`.

This authorization permits AION-186 only. It does not permit runtime activation,
API route exposure, network calls, connector calls, model-provider calls, source
rewrite operations, Git mutations by runtime code, deployment, or model-weight
training.

## AION-186 Scope

`predictive-world-model-transition-outcome-uncertainty-counterfactual-core`

AION-186 may implement deterministic predictive world-model contracts and local
services for state encoding, transition evidence, transition prediction, outcome
prediction, uncertainty estimation, causal hypotheses, counterfactual scenarios,
counterfactual rollouts, snapshots, and evaluation artifacts.

## Source Boundaries

Allowed source paths for AION-186 are limited to:

- `services/brain-api/src/aion_brain/world_model/`
- `services/brain-api/src/aion_brain/contracts/world_model.py`
- `services/brain-api/tests/test_cognitive_predictive_world_model.py`
- `services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-world-model-check.sh`
- `scripts/cognitive-world-model-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

Prohibited paths include API routes, workflow files, migrations, package
manifests, lock files, Git controllers, pull-request controllers, merge
controllers, deployment controllers, unrestricted connector adapters,
unrestricted provider clients, and credential stores.

## Required Gates

- focused AION-185 closeout tests
- AION-184 persistent-state focused tests
- cognitive persistent-state closeout no-go gate
- cognitive persistent-state closeout gate
- docs checks
- final docs audit
- no-domain-drift validation
- boundary checks
- repository-health checks
- one full `./scripts/check.sh` on the final task head
- `git diff --check`

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
- no action execution
- no default hidden persistence path
- no secrets, raw prompts, hidden reasoning, raw diffs, or unredacted personal data in evidence

## Completion Conditions

- AION-184 evaluation evidence is PASS
- AION-183-CA-0001 is inactive, consumed, expired, and non-reusable
- AION-185-CA-0002 is the only active cognitive implementation authorization
- AION-185-CA-0002 authorizes AION-186 only
- no runtime activation, route, migration, package file, dependency file, external call, provider call, connector call, or model-weight training is introduced
- AION-185 PR merges after all required checks pass

## Next Task

`AION-186`
