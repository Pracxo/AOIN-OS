# Operator Platform Long-Running Checks

## Why long-running checks exist

AION-101 produced a checkpoint. AION-102 makes that checkpoint repeatable by
running the full local quality stack behind a single stabilization command.
The longer runtime is intentional because the gate protects future UI, auth,
activation, connector, and operator-action planning from silent boundary drift.

## What is covered

The long-running checks cover static console safety, UI release gate, module
lifecycle dashboard, provider hardening dashboard, operator actions, dry-run
authorization, local auth, local session preview, role filtering, production
auth architecture, disabled auth runtime, docs audits, no-domain-drift,
architecture boundary checks, backend tests, SDK tests, type checks, lint, and
repository health.

## What remains excluded

The checks do not install packages, run frontend builds, call external
services, invoke providers, send notifications, activate modules, activate
capabilities, load code, register runtime routes, execute tools, execute action
proposals, persist production sessions, or mutate the v0.1 release baseline.

## When to run

Run `./scripts/operator-platform-regression.sh` before any AION Operator
Platform stabilization merge. Run `./scripts/operator-platform-freeze-gate.sh`
before declaring a phase checkpoint ready for review.

## CI relationship

CI should continue to run the existing fast and full checks. The stabilization
gate is the local operator-facing aggregate that mirrors those checks and adds
checkpoint-specific evidence validation.

## Local relationship

Local runs are authoritative for phase handoff evidence. If CI fails but local
passes, inspect the CI environment and fix branch/ref assumptions without
weakening the no-go checks.

## How to interpret failures

Failures are release blockers. Prefer the narrow failing command first, then
rerun the regression script. Never skip safety checks to get a green gate.
