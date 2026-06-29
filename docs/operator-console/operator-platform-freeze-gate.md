# Operator Platform Freeze Gate

## Purpose

The AION-102 freeze gate proves the Operator Platform checkpoint can be frozen
for the next planning phase. It composes the long-running regression matrix,
source formatting checks, release tag checks, and static no-go checks into one
operator-facing command.

## Freeze gate flow

1. Run `./scripts/operator-platform-regression.sh`.
2. Run `git diff --check`.
3. Print the working tree status summary.
4. Verify `aion-v0.1.0` is still available and remains in local `main` or
   `origin/main` history when either ref is present.
5. Verify static console, auth runtime, write, activation, execution, provider,
   and external-call controls remain absent.

## Required checks

- `./scripts/operator-platform-regression.sh`
- `./scripts/static-console-ux-check.sh`
- `git diff --check`
- `./scripts/static-console-safety-check.sh`
- `./scripts/auth-runtime-check.sh`
- `./scripts/operator-actions-check.sh`
- `./scripts/action-authorization-check.sh`
- `./scripts/provider-dashboard-check.sh`
- `./scripts/module-lifecycle-dashboard-check.sh`

## No-go conditions

The freeze gate fails for any frontend dependency, package file, lockfile,
build tool, migration, AION-102 or AION-103 API router, production auth enablement,
login/logout behavior, session persistence, credential storage, write control,
activation control, execution control, provider-call control, external-call
control, package installation, external service call, privileged bypass, hard
delete, domain module logic, or production UI claim.

## Expected output

The final line should be:

```text
Operator platform freeze gate PASS
```

## Recovery path

Treat every failure as a fix-forward issue. Restore the failing local script,
remove the blocked artifact or control, rerun the narrow failing command, then
rerun the full freeze gate. Do not bypass, skip, xfail, or soften the safety
checks.

## Merge rules

Merge only from a PR branch. Do not push directly to `main`. The branch must
preserve `aion-v0.1.0`, keep the static console read-only, keep auth disabled
or mock-only, and keep all write, activation, execution, provider-call, and
external-call controls absent.
