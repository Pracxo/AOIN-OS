# Golden Path Scenario Harness

AION Golden Path is the local deterministic end-to-end harness for Brain v0.1.
It verifies that core layers can work together through scenario-owned records,
fixture packs, dry-run steps, assertions, reports, and release smoke checks.

It is not a production workload, frontend demo, load test, model benchmark, or
domain test suite.

## Boundaries

Golden path runs may seed synthetic fixtures, call existing Brain services
through local interfaces, create scenario-owned records, record audit and
telemetry, create reports, and raise operator recommendations for failures.

Golden path runs must not bypass policy, autonomy, or approval gates. They must
not call external services, call model providers, execute tools, execute action
proposals, execute handoffs in controlled mode by default, hard-delete fixtures,
or mutate non-scenario source records.

## Default Scenarios

The default catalog contains deterministic scenarios for boot readiness, self
description, dialogue, instruction resolution, prompt governance, model output
governance, grounding, dry-run action proposal, dry-run execution handoff, run
supervision, notification, scheduler tick, incident correlation, resource
registry validation, lifecycle evaluation, contract scan, extension intake,
module binding validation, conformance readiness, and operator overview.

## Fixtures

Fixture packs are synthetic and scenario-owned. They are safe to seed in dry-run
mode and remain separate from real user data or production records.

## Assertions

Assertions are deterministic metadata checks. They support status checks,
presence checks, count checks, policy checks, and guard assertions such as
`no_external_call`, `no_execution`, `no_secret`, `no_hidden_reasoning`, and
`no_domain_drift`.

Unknown assertion types fail closed.

## Release Smoke

The release smoke matrix reads local service availability and the latest golden
path report. It does not spawn shells, run subprocesses, call external services,
or package releases.

## Local Commands

Run the local harness through the Brain API:

```bash
./scripts/golden-path.sh
./scripts/release-smoke.sh
```

Run through `aionctl`:

```bash
./scripts/aionctl.sh golden-path scenarios
./scripts/aionctl.sh golden-path fixtures
./scripts/aionctl.sh golden-path run
./scripts/aionctl.sh golden-path release-smoke
```

## Failure Handling

Failed or blocked runs generate reports and may create operator action items.
They do not hide failures or weaken the release/freeze gates.

## Release Handoff Usage

For v0.1 release handoff, run:

```bash
./scripts/golden-path.sh --offline-ok
./scripts/release-smoke.sh --offline-ok
```

Golden path or release smoke critical failures are no-go conditions.
