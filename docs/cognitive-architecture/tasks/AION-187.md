# AION-187 World-Model Evaluation and Workspace Authorization

## Task Purpose

AION-187 evaluates the AION-186 predictive world model, formally closes
`AION-185-CA-0002`, and creates the next bounded implementation authorization
for AION-188 global cognitive workspace work.

## Evaluation

- Evaluation ID: `AION-PWME-001`
- Evaluated task: `AION-186`
- Evaluated implementation PR: `#97`
- Evaluated implementation merge commit:
  `d8762dd881974a8540cde3c9aac068f015eff4e3`
- Decision: `WORLD_MODEL_EVALUATION_PASS_AUTHORIZE_GLOBAL_WORKSPACE`

## Closed Authorization

`AION-185-CA-0002` is closed by AION-187 after AION-186 passed predictive
world-model evaluation. The authorization is inactive, consumed, expired, and
non-reusable. The consuming implementation task is AION-186 and the formal
closeout task is AION-187.

## Hard PASS Conditions

- transition top-1 accuracy: at least 0.80
- Brier score: at most 0.20
- probability sum error: at most 0.000000001
- unknown-state fail-closed rate: 100%
- deterministic replay rate: 100%
- forbidden side effects: 0

## New Authorization

AION-187 creates exactly one active implementation authorization:
`AION-187-CA-0003`.

This authorization permits AION-188 only. It does not permit runtime activation,
API route exposure, network calls, connector calls, model-provider calls, source
rewrite operations, Git mutations by runtime code, deployment, or model-weight
training.

## AION-188 Scope

`global-cognitive-workspace-attention-salience-broadcast-core`

AION-188 may implement deterministic global cognitive workspace contracts and
local services for immutable workspace items, specialist bids, salience scoring,
attention decisions, bounded broadcasts, specialist responses, cycle state,
workspace snapshots, and audit events.

## Source Boundaries

Allowed source paths for AION-188 are limited to:

- `services/brain-api/src/aion_brain/workspace/`
- `services/brain-api/src/aion_brain/contracts/workspace.py`
- `services/brain-api/tests/test_cognitive_global_workspace.py`
- `services/brain-api/tests/test_cognitive_global_workspace_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-global-workspace-check.sh`
- `scripts/cognitive-global-workspace-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

Prohibited paths include API routes, workflow files, migrations, package
manifests, lock files, Git controllers, pull-request controllers, merge
controllers, deployment controllers, unrestricted connector adapters,
unrestricted provider clients, and credential stores.

## Required Gates

- focused AION-187 closeout tests
- AION-186 predictive world-model focused tests
- cognitive world-model closeout no-go gate
- cognitive world-model closeout gate
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
- no API route
- no network, connector, or model-provider call
- no secrets, raw prompts, hidden reasoning, raw diffs, or unredacted personal data in evidence

## Completion Conditions

- AION-186 evaluation evidence is PASS
- AION-185-CA-0002 is inactive, consumed, expired, and non-reusable
- AION-187-CA-0003 is the only active cognitive implementation authorization
- AION-187-CA-0003 authorizes AION-188 only
- no runtime activation, route, migration, package file, dependency file, external call, provider call, connector call, or model-weight training is introduced
- AION-187 PR merges after all required checks pass

## Next Task

`AION-188`
