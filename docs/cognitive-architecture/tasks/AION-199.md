# AION-199 Integrated Cognitive Shadow Runtime

## Task Purpose

AION-199 implements the bounded, operator-invoked, local offline integrated
cognitive shadow runtime authorized by `AION-198-CA-0008`. The runtime provides
an explicit Python API that can run one approved local shadow cycle and return
operator-review evidence. It performs no consequential external action.

## Authorization ID

- Program ID: `AION-COGNITIVE-ARCHITECTURE-001`
- Authorization ID: `AION-198-CA-0008`
- Implementation task: `AION-199`
- Authorized branch: `phase/cognitive-shadow-runtime`
- Candidate ID: `integrated-cognitive-shadow-runtime`
- Scope: `operator-invoked-local-offline-integrated-cognitive-shadow-runtime`
- Formal closeout task: `AION-200`
- Formal closeout evaluation: `AION-CSE-001`

## Exact Scope

AION-199 adds only the explicit local shadow-runtime contracts and service
surface needed to run one bounded cognitive cycle from approved synthetic or
redacted input. The runtime remains a Python API invoked by an operator. It is
not registered in startup, kernel, web routing, scheduler, command-line
installation, connector code, provider code, deployment code, or production
traffic paths.

## Role Comparison

AION-198 authorized this implementation and keeps `AION-198-CA-0008` active.
AION-199 implements the local runtime under that authorization and records the
implementation as pending AION-200 evaluation. AION-200 is the only task that
may evaluate and close the authorization.

## Source Boundaries

AION-199 may add or update only:

- `docs/cognitive-architecture/tasks/AION-199.md`
- `docs/cognitive-architecture/program-ledger.json`
- `docs/cognitive-architecture/authorization-ledger.json`
- `examples/cognitive-architecture/aion-199-cognitive-shadow-runtime.json`
- `services/brain-api/src/aion_brain/contracts/cognitive_runtime.py`
- `services/brain-api/src/aion_brain/cognitive_runtime/__init__.py`
- `services/brain-api/src/aion_brain/cognitive_runtime/runtime.py`
- `services/brain-api/tests/test_cognitive_shadow_runtime.py`
- `services/brain-api/tests/test_cognitive_shadow_runtime_no_runtime_effect.py`
- `scripts/cognitive-shadow-runtime-check.sh`
- `scripts/cognitive-shadow-runtime-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`
- inherited AION-197 and AION-198 tests required to recognize the
  post-authorization implementation state

The task must not add package files, lockfiles, migrations, workflows,
production API routes, startup registration, scheduler registration, deployment
code, connector integrations, provider integrations, credential storage, source
rewrite code, Git automation, pull-request creation, approval creation, merge
execution, production canary paths, or model-weight updates.

## Required Contracts

- `CognitiveSessionManifest`
- `CognitiveSessionState`
- `CognitiveCycleInput`
- `CognitiveCycleOutput`
- `CognitiveRuntimeBudget`
- `CognitiveRuntimeDiagnostics`
- `CognitiveRuntimeIncident`
- `CognitiveRuntimeEvidence`

The implementation also defines `ApprovedCognitiveObservation` to enforce the
single approved synthetic or redacted observation boundary for each cycle.

## Required Services

- `ControlledCognitiveShadowRuntime`

The service coordinates only existing local cognitive architecture services:
persistent cognitive state, world-model prediction, workspace arbitration,
hierarchical planning, information-acquisition planning, memory consolidation,
and governed learning candidates.

## Required Tests

- Manifest and authorization validation
- Approved local state loading
- One approved observation per cycle
- Belief and uncertainty update
- Approved memory reference use
- World-model prediction generation
- Workspace arbitration
- Hierarchical plan proposal generation
- Information-acquisition request generation
- Simulated outcome recording
- Consolidation candidate creation
- Learning candidate creation
- Operator-review evidence return
- Approved local state persistence
- Deterministic replay hash stability
- Stale state rejection
- Kill switch and budget fail-closed behavior
- No API route, no kernel registration, no startup surface, no prohibited
  external imports, and zero external effects

## Required Gates

- `scripts/cognitive-shadow-runtime-no-go-regression.sh`
- `scripts/cognitive-shadow-runtime-check.sh`
- `scripts/cognitive-shadow-runtime-authorization-check.sh`
- `scripts/cognitive-integrated-evaluation-check.sh`
- `scripts/docs-check.sh`
- `scripts/final-docs-audit.sh`
- `scripts/verify-no-domain-drift.sh`
- `scripts/boundary-check.sh`
- `scripts/repo-health.sh`
- `scripts/check.sh`
- `git diff --check`

## Security Invariants

- Production cognitive runtime remains disabled.
- Production input and user traffic remain prohibited.
- Network, connector, and model-provider access remain disabled.
- No API route, startup registration, scheduler, background loop, or
  command-line installation is added.
- No source rewrite, Git mutation, real pull-request creation, approval
  creation, merge, deployment, production canary, consequential external
  action, model-weight training, or model-weight change is performed.
- Evidence stores only sanitized references, fingerprints, counters, and review
  summaries.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

Each invocation is bounded to one explicit operator invocation, synthetic or
redacted input, a local state repository, a maximum of 100 cycles, maximum
concurrency of 1, at most 1800 wall-clock seconds, bounded workspace items,
bounded memory references, bounded learning episodes, and zero external
operation counters.

## Completion Conditions

- AION-199 implementation evidence is recorded as
  `implemented_pending_aion_200_evaluation`.
- `AION-198-CA-0008` remains the only active authorization, unconsumed,
  unexpired, and non-reusable.
- `ControlledCognitiveShadowRuntime` is available only as an explicit Python API.
- All required contracts and the required cycle are implemented.
- Operator-review evidence is returned for completed cycles.
- Direct action execution and external effects remain absent.
- Focused tests, no-go gates, inherited governance gates, and full repository
  checks pass before merge.

## Next Task

AION-200 formally evaluates the AION-199 integrated cognitive shadow runtime
under `AION-CSE-001` and may close `AION-198-CA-0008` only if the evaluation
passes all hard safety conditions.
