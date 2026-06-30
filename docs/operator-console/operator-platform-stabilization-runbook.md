# Operator Platform Stabilization Runbook

## Local setup

Work only from the canonical repository:

```bash
cd "/Users/damilaremerotiwon/KITEV2/AOIN OS"
git status --short --branch
```

Use the `phase/operator-platform-stabilization` branch and do not use copied
workspaces.

## Run regression

Run:

```bash
./scripts/operator-platform-regression.sh
```

The command is long-running because it includes the full repository check.

## Run freeze gate

Run:

```bash
./scripts/operator-platform-freeze-gate.sh
```

This command reruns the regression matrix, checks whitespace, reports working
tree status, verifies the `aion-v0.1.0` tag relationship, and validates freeze
gate safety flags.

## Run static console UX check

For AION-103 and later static-console polish, also run:

```bash
./scripts/static-console-ux-check.sh
```

This command verifies the navigation groups, skip link, accessibility evidence,
safe local command copy allowlist, CSS focus styles, localhost guard, and
absence of frontend package files or build tooling.

## Interpret failures

Use the first failing script as the owner of the failure. Fix the boundary
regression, rerun the narrow script, then rerun the regression and freeze gate.
Do not skip, xfail, or soften blocked-file, auth, activation, execution,
provider, external-call, or package-file checks.

## Fix forward rules

Fix forward in the same branch. Do not revert unrelated user changes. Do not
move, delete, or recreate `aion-v0.1.0`. Do not add runtime subsystems,
migrations, API routes, SDK resources, CLI command implementations, frontend
dependencies, package files, lockfiles, build tooling, package installation,
external service calls, provider calls, activation, execution, hard delete, or
domain module logic.

## PR merge rules

Open or update a PR from the stabilization branch. Merge only after the freeze
gate, required local checks, and CI are green. Do not push directly to `main`.

## Branch cleanup rules

After merge, verify `main` contains the stabilization commit, verify
`aion-v0.1.0` remains reachable from `main`, then delete the branch only after
the PR and CI are closed cleanly.

## AION-117 Integration Checkpoint

The operator platform stabilization gate is now part of the AION-117
post-v0.1 platform integration checkpoint. Run
`./scripts/platform-integration-checkpoint.sh` and
`./scripts/platform-integration-freeze-check.sh` for cross-phase closeout.
The integration gate preserves the same no-runtime boundary: no production
auth, operator write execution, connector runtime implementation, module
activation, external calls, credential storage, token storage, sandbox
execution, package files, migrations, API routes, SDK resources, or CLI
implementations.

## AION-118 Release Candidate Gate

AION-118 composes this operator stabilization runbook into the post-v0.1
release candidate gate. Future operator implementation work must pass the
release candidate gate and a future scoped ADR before any write execution,
production auth, external call path, credential/token storage, sandbox
execution, package file, migration, API route, SDK resource, CLI command, v0.2
release, or v0.2 tag can be approved.
