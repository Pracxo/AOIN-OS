# AION-202 Controlled Cognitive Pilot Execution

## Task Purpose

AION-202 executes the exact AION-201-approved controlled local-offline cognitive pilot as an operational evidence task. It uses the existing AION-199 local-offline cognitive shadow runtime and records redacted pilot evidence for AION-203 / AION-CASE-001 final evaluation.

## Authorization ID

Authorization `AION-201-CA-0009` authorizes this task only for `AION-202`.

The pilot remains bound to:

- AION-199 implementation commit `c1479e805ee95e11f7f2d8719607189ccbf9ed4b`
- AION-199 merge commit `cf1fd2ca6a45aeb3e034a95799edf9833ca24b14`
- AION-200 evaluation `AION-CSE-001`
- AION-200 canonical JSON SHA-256 fingerprint `4cb32ba5e5cfb0f0d78014aa2eb7bb959fe3c9a6e23d5a06740b578c3c8cc563`
- AION-201 authorization PR `112`
- AION-201 merge commit `b4ddd9c60dc9b5c236beb7c7e795cdd3222c6be0`

## Exact Scope

AION-202 executed 10 approved local-offline pilot sessions with 100 cycles per session, for 1000 total cycles.

The exact scope is `controlled-local-offline-operator-evaluation-pilot`.

The exact local state-store path was:

`/tmp/aion-os/aion-201/pilot-state.sqlite`

The exact local output directory was:

`/tmp/aion-os/aion-201/redacted-pilot-evidence`

The committed redacted evidence artifact is:

`examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json`

## Role Comparison

AION-201 authorized the pilot and defined its limits. AION-202 executes that approved pilot and records operational evidence. AION-203 evaluates the AION-202 evidence, closes `AION-201-CA-0009`, and decides final program closeout.

## Source Boundaries

AION-202 does not modify cognitive runtime source. It does not add API routes, kernel registration, startup registration, scheduler hooks, background loops, CLI installation paths, migrations, package files, provider integrations, connector integrations, deployment code, Git runtime code, pull-request runtime code, credential access, or production runtime exposure.

The pilot runtime created no source changes, Git operations, PRs, approvals, external actions, or production traffic.

## Required Contracts

- AION-201 authorization payload
- AION-202 redacted pilot evidence payload
- Existing AION-199 `CognitiveSessionManifest`
- Existing AION-199 `CognitiveCycleInput`
- Existing AION-199 `CognitiveCycleOutput`
- Existing AION-199 `CognitiveRuntimeEvidence`
- Existing AION-199 `CognitiveRuntimeDiagnostics`

## Required Services

- Existing `ControlledCognitiveShadowRuntime`
- Existing explicit local cognitive state repository
- Existing predictive world model
- Existing workspace arbitration
- Existing planning service
- Existing information-acquisition planner
- Existing memory consolidation service
- Existing governed learning candidate services

## Required Tests

- `services/brain-api/tests/test_cognitive_local_offline_pilot_docs.py`
- `services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py`

## Required Gates

- `scripts/cognitive-local-offline-pilot-check.sh`
- `scripts/cognitive-local-offline-pilot-no-go-regression.sh`
- `scripts/cognitive-local-offline-pilot-authorization-check.sh`
- `scripts/docs-check.sh`
- `scripts/final-docs-audit.sh`
- `scripts/verify-no-domain-drift.sh`
- `scripts/boundary-check.sh`
- `scripts/check.sh`

## Security Invariants

- `production_cognitive_runtime_enabled=false`
- `production_input=false`
- `user_traffic=false`
- `network_calls=0`
- `connector_calls=0`
- `model_provider_calls=0`
- `credential_access=false`
- `source_mutations=0`
- `git_operations_by_pilot=0`
- `real_pull_requests_by_pilot=0`
- `approvals_created_by_pilot=0`
- `external_actions_performed=false`
- `deployment_operations=0`
- `production_exposure=0`
- `model_weight_changes=0`
- `model_weight_training=0`
- `consequential_action_execution=0`

## Performance Limits

- Maximum sessions: 10
- Maximum cycles per session: 100
- Maximum total cycles: 1000
- Maximum wall clock per session: 1800 seconds
- Maximum concurrency: 2
- Observed concurrency: 1

## Completion Conditions

AION-202 is complete when the redacted evidence shows:

- all approved pilot sessions executed
- state continuity collected
- prediction accuracy collected
- uncertainty calibration collected
- workspace decisions collected
- planning success collected
- information-acquisition efficiency collected
- information-acquisition budgets met
- consolidation quality collected
- learning-candidate quality collected
- operator-review load collected
- latency collected
- compute cost collected
- safety violations equal zero
- kill-switch evidence collected
- repository integrity collected
- forbidden side effects equal zero

## Next Task

AION-203 performs final pilot evaluation and program closeout under `AION-CASE-001`, closes `AION-201-CA-0009`, and verifies retention or cleanup for temporary pilot data.
