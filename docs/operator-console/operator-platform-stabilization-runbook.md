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
