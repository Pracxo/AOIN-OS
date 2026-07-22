# AION-201 Controlled Local-Offline Pilot Authorization

## Task Purpose

AION-201 creates one bounded implementation authorization,
`AION-201-CA-0009`, for the AION-202 controlled local-offline cognitive pilot.
It binds that pilot to exact AION-199, AION-200, environment, reference,
state-store, output, benchmark, budget, monitoring, kill-switch, retention,
operator-principal, and expiry evidence. It does not execute the pilot.

## Authorization ID

- Program ID: `AION-COGNITIVE-ARCHITECTURE-001`
- Authorization ID: `AION-201-CA-0009`
- Parent evaluation: `AION-CSE-001`
- Parent evaluation merge commit:
  `ca1f7eb4b72b65fd7f32cfeae08a065d9054d6ec`
- AION-199 implementation commit:
  `c1479e805ee95e11f7f2d8719607189ccbf9ed4b`
- AION-199 implementation merge commit:
  `cf1fd2ca6a45aeb3e034a95799edf9833ca24b14`
- AION-200 evaluation fingerprint:
  `4cb32ba5e5cfb0f0d78014aa2eb7bb959fe3c9a6e23d5a06740b578c3c8cc563`
- Authorized task: `AION-202`
- Closeout task: `AION-203`
- Closeout evaluation: `AION-CASE-001`
- Branch: `phase/cognitive-local-offline-pilot-authorization`
- Scope: `controlled-local-offline-operator-evaluation-pilot`

## Exact Scope

AION-201 may add authorization evidence, ledgers, scripts, tests, and
governance validators for `AION-201-CA-0009`. It may authorize AION-202 to run
the existing AION-199 shadow runtime only inside
`local_offline_operator_evaluation` with synthetic or redacted references,
fixed local state path `/tmp/aion-os/aion-201/pilot-state.sqlite`, and fixed
output directory `/tmp/aion-os/aion-201/redacted-pilot-evidence`.

## Role Comparison

AION-200 evaluated and closed the AION-198 implementation authorization without
creating a pilot authorization. AION-201 is the separate authorization review
that activates one non-reusable pilot authorization for AION-202. AION-202 may
execute the approved pilot and collect redacted evidence. AION-203 evaluates
that evidence and closes `AION-201-CA-0009`.

## Source Boundaries

AION-201 may add or update only:

- `docs/cognitive-architecture/tasks/AION-201.md`
- `docs/cognitive-architecture/program-ledger.json`
- `docs/cognitive-architecture/authorization-ledger.json`
- `examples/cognitive-architecture/aion-201-local-offline-pilot-authorization.json`
- `services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py`
- inherited cognitive governance tests needed to recognize AION-201 as the
  later active authorization
- `scripts/cognitive-local-offline-pilot-authorization-check.sh`
- `scripts/cognitive-local-offline-pilot-authorization-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

It must not add or change runtime source, API routes, kernel registration,
startup registration, scheduler registration, background loops, package files,
lockfiles, migrations, workflows, connector access, provider access,
credential storage, source rewrite code, Git automation, pull-request
automation, approval creation, merge automation, deployment code, production
canary code, or model-weight training.

## Required Contracts

AION-201 binds AION-202 to the existing AION-199 runtime contracts:

- `CognitiveSessionManifest`
- `CognitiveSessionState`
- `CognitiveCycleInput`
- `CognitiveCycleOutput`
- `CognitiveRuntimeBudget`
- `CognitiveRuntimeDiagnostics`
- `CognitiveRuntimeIncident`
- `CognitiveRuntimeEvidence`

## Required Services

- `ControlledCognitiveShadowRuntime`

AION-201 does not register the service in production, kernel, startup,
scheduler, web routing, command-line, connector, provider, or deployment
paths.

## Required Tests

- Authorization payload schema validation
- AION-199 implementation commit binding
- AION-200 evaluation fingerprint binding
- Synthetic environment manifest binding
- Redacted reference-set binding
- Fixed local state-store path and output directory binding
- Benchmark manifest validation
- Run-budget validation
- Monitoring, kill-switch, retention, and operator-principal validation
- Ledger activation of exactly one AION-201 authorization
- Proof that AION-201 does not execute the AION-202 pilot
- Runtime-disabled and no-go regression checks

## Required Gates

- `scripts/cognitive-local-offline-pilot-authorization-no-go-regression.sh`
- `scripts/cognitive-local-offline-pilot-authorization-check.sh`
- `scripts/cognitive-shadow-runtime-evaluation-check.sh`
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
- Production event subscriptions remain disabled.
- Production input and user traffic remain prohibited.
- Network, connector, provider, credential, and token access remain absent.
- No API route, kernel registration, startup hook, scheduler, background loop,
  or CLI installation is added.
- No source rewrite, Git mutation, real pull-request creation, approval
  creation, merge operation, deployment, production canary, consequential
  external action, model-weight training, or model-weight change is performed
  by AION-201.
- The pilot uses only synthetic inputs, redacted references, fixed local state,
  fixed redacted output, operator review, and fail-closed kill-switch evidence.
- `AION-201-CA-0009` is active, non-reusable, unconsumed, and unexpired until
  AION-203 closeout.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

- Environment: `local_offline_operator_evaluation`
- Maximum sessions: `10`
- Maximum cycles per session: `100`
- Maximum total cycles: `1000`
- Maximum wall clock per session: `1800` seconds
- Maximum concurrency: `2`
- Network calls: `0`
- Source mutations: `0`
- Git operations: `0`
- Real PRs: `0`
- Approvals created: `0`
- Deployments: `0`
- Production exposure: `0`
- Model-weight changes: `0`

## Completion Conditions

- `AION-201-CA-0009` is the single active cognitive implementation
  authorization.
- The authorization is bound to the exact AION-199 implementation commit and
  AION-200 evaluation fingerprint.
- The exact environment, redacted reference set, state-store path, output
  directory, benchmark, run budget, monitoring, kill-switch, retention,
  operator principal, and expiry are present in the authorization payload.
- AION-202 pilot execution evidence is absent.
- Runtime source, production paths, external access, Git automation, approval
  creation, deployment, canary, and model-weight changes remain absent.

## Next Task

AION-202 must execute only the exact pilot approved by `AION-201-CA-0009` and
commit only redacted pilot evidence, reports, tests, and closeout tooling.
