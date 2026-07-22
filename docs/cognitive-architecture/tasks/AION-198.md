# AION-198 Integrated Cognitive Shadow-Runtime Authorization

## Task Purpose

AION-198 creates the bounded implementation authorization
`AION-198-CA-0008` for AION-199. The authorization is based on the AION-197
integrated cognitive architecture evaluation, `AION-CAE-001`, and permits only
an operator-invoked local offline shadow runtime implementation. This task does
not implement that runtime.

## Authorization ID

- Program ID: `AION-COGNITIVE-ARCHITECTURE-001`
- Authorization ID: `AION-198-CA-0008`
- Parent task: `AION-197`
- Parent evaluation: `AION-CAE-001`
- Parent PR: `108`
- Parent merge commit: `770a195eae98de12a67370c790f2c7eb36e91aec`
- Implementation task: `AION-199`
- Formal closeout task: `AION-200`

## Exact Scope

AION-198 authorizes AION-199 for exactly:

`operator-invoked-local-offline-integrated-cognitive-shadow-runtime`

The authorized implementation branch is `phase/cognitive-shadow-runtime`.
The runtime must be explicit, local offline, bounded, non-production,
non-networked, and non-effectful outside its approved local evidence and state
repository boundaries.

## Role Comparison

AION-198 is an authorization task. It creates one active non-reusable
implementation authorization for AION-199 and records source, resource, test,
rollback, expiry, and closeout limits. AION-199 is the later implementation
task that may add the bounded shadow-runtime source surface. AION-198 adds no
runtime implementation source, no API route, no startup registration, no
scheduler, and no command-line installation.

## Source Boundaries

AION-198 may change only governance, authorization evidence, tests, and gate
scripts:

- `docs/cognitive-architecture/tasks/AION-198.md`
- `docs/cognitive-architecture/program-ledger.json`
- `docs/cognitive-architecture/authorization-ledger.json`
- `examples/cognitive-architecture/aion-198-shadow-runtime-authorization.json`
- `services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py`
- `scripts/cognitive-shadow-runtime-authorization-check.sh`
- `scripts/cognitive-shadow-runtime-authorization-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`
- exact historical governance tests and scanner allowlists required to recognize
  `AION-198-CA-0008`

AION-199 is authorized to add only bounded local shadow-runtime source under the
explicit paths recorded in the authorization ledger. It may not add package
files, lockfiles, migrations, workflows, production API routes, deployment code,
connector integrations, model-provider integrations, credential storage,
source-rewrite runtime paths, Git automation, real pull-request creation,
approval creation, merge execution, or production canary paths.

## Required Contracts

AION-199 is authorized to implement these contracts:

- `CognitiveSessionManifest`
- `CognitiveSessionState`
- `CognitiveCycleInput`
- `CognitiveCycleOutput`
- `CognitiveRuntimeBudget`
- `CognitiveRuntimeDiagnostics`
- `CognitiveRuntimeIncident`
- `CognitiveRuntimeEvidence`

## Required Services

AION-199 is authorized to implement:

- `ControlledCognitiveShadowRuntime`

The runtime may coordinate the existing persistent state, world model, global
workspace, planning, information-acquisition, memory-consolidation, and
continual-learning candidate services only through bounded local contracts.

## Required Tests

- `services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py`
- inherited AION-197 integrated evaluation tests
- inherited cognitive governance document tests

The AION-199 implementation must add focused tests for manifest validation,
authorization validation, approved local state loading, one approved
observation, bounded cycle execution, kill-switch behavior, budget enforcement,
deterministic replay, corrupted or stale state rejection, and zero external
effects.

## Required Gates

- `scripts/cognitive-shadow-runtime-authorization-no-go-regression.sh`
- `scripts/cognitive-shadow-runtime-authorization-check.sh`
- inherited AION-197 integrated evaluation gate
- cognitive architecture authorization gate
- docs check
- final docs audit
- domain-drift validation
- boundary check
- repository health
- full repository check
- `git diff --check`

## Security Invariants

- Production cognitive runtime remains disabled.
- Production input and user traffic are prohibited.
- Network, connector, and model-provider access remain disabled.
- No API runtime route is added.
- No startup registration, scheduler, background loop, or command-line
  installation is added.
- No source rewrite, Git mutation, real pull-request creation, approval
  creation, merge, deployment, production canary, consequential external action,
  model-weight training, or model-weight change is authorized.
- No credentials, tokens, private keys, cookies, raw messages, source patches,
  raw diffs, holdout content, hidden reasoning, or unredacted personal data may
  be stored in evidence.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

AION-199 is bounded by explicit operator invocation, synthetic or redacted input,
an explicit local state repository, a maximum of 100 cognitive cycles per
invocation, maximum concurrency of 1, a 1800 second wall-clock cap per
invocation, a required kill switch, and zero network, connector, provider, Git,
deployment, production, approval, merge, source-rewrite, or model-weight
operations.

## Completion Conditions

- `AION-198-CA-0008` is the only active cognitive implementation authorization.
- The authorization is active, unconsumed, unexpired, non-reusable, and bound to
  AION-199.
- The parent AION-197 evaluation remains PASS and unchanged.
- Active cognitive implementation authorization count is `1`.
- Runtime implementation remains absent in AION-198.
- Production runtime, network access, connector access, provider access, source
  rewrite, Git mutation, real pull-request creation, approval creation, merge,
  deployment, canary, and model-weight training remain disabled.
- Focused, inherited, documentation, boundary, no-go, and full repository gates
  pass before merge.

## Next Task

AION-199 implements the operator-invoked local offline integrated cognitive
shadow runtime under authorization `AION-198-CA-0008`. Its formal closeout task
is AION-200 under evaluation `AION-CSE-001`.
