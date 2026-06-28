# Operator Platform Release Readiness

## Readiness checklist

- Operator Platform checkpoint docs exist.
- Operator Platform evidence pack exists.
- Operator Platform risk register exists.
- Operator Platform next-phase plan exists.
- ADR 0092 exists and is indexed.
- ADR 0093 exists and is indexed.
- JSON evidence examples are valid.
- Static console remains local-only, read-only, and dependency-free.
- Auth remains disabled or mock-only.
- Write, activation, execution, provider-call, and external-call controls are absent.
- No package manager file, lockfile, frontend config, build tool, migration, or AION-101/AION-102 API router file is added.

## Required scripts

Run these commands before merge:

```bash
./scripts/operator-platform-checkpoint.sh
./scripts/operator-platform-regression.sh
./scripts/operator-platform-freeze-gate.sh
./scripts/ui-release-gate.sh
./scripts/static-console-safety-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
./scripts/check.sh
git diff --check
```

## Required CI status

CI must be green for the branch. Any failure in linting, type checks, backend
tests, SDK tests, architecture boundary checks, docs checks, or repository
health checks blocks merge.

## Required branch hygiene

The branch must be based on current `main`, must not push directly to `main`,
must preserve the `aion-v0.1.0` tag, and must contain only checkpoint or
stabilization docs, examples, scripts, and tests.

## Required PR review

Review must verify the checkpoint is evidence-only, the risk register has no
unowned no-go condition, and the next phase remains planning-safe.

## Required no-go review

Any production auth, runtime auth enablement, login/logout, token or cookie
issuance, session persistence, credential storage, frontend dependency, build
tool, provider call, external call, write path, activation path, execution path,
runtime registration, code loading, hard delete, or domain module logic blocks
merge.

## Not production UI

This checkpoint is not production UI. It is a local static evidence checkpoint
for planning the next Operator Platform phase.
