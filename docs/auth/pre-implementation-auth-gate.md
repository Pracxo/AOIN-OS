# Pre-Implementation Auth Gate

## Purpose

This gate defines what must be true before any AION-105 or later auth
implementation task can move beyond docs, design, and evidence planning.

## Must Be True Before AION-105+

- `./scripts/auth-prototype-review.sh` passes.
- `./scripts/auth-no-go-regression.sh` passes.
- `./scripts/operator-platform-regression.sh` passes on the candidate branch.
- CI is green on the branch.
- A new ADR explicitly approves the implementation class and threat model.
- Production auth, protected material lifecycle, provider integration, browser
  session lifecycle, migrations, and rollback path are documented before code.

## Gate Fail Conditions

The gate fails if the branch adds login/logout, credentials, token issuance,
cookie issuance, persisted sessions, external identity runtime, provider SDKs,
package files, build tooling, migrations, API routers, writes, activation,
execution, hard delete, external calls, or privileged bypass without a specific
approved implementation ADR.

## Required Scripts

```bash
./scripts/auth-prototype-review.sh
./scripts/auth-no-go-regression.sh
./scripts/auth-runtime-check.sh
./scripts/production-auth-architecture-check.sh
./scripts/local-auth-check.sh
./scripts/local-session-check.sh
./scripts/role-filter-check.sh
./scripts/action-authorization-check.sh
./scripts/ui-release-gate.sh
```

## Required CI State

All required GitHub checks must be green. Local-only success is not sufficient
for implementation work.

## Required ADR State

ADR 0095 keeps auth disabled/mock-only. Any implementation phase needs a later
ADR that supersedes only the specific boundary it is approved to change.

## Rollback Path

If a future branch fails this gate, remove the runtime or dependency addition,
restore the disabled/mock-only boundary, rerun the narrow failing script, and
then rerun the review and no-go regression scripts.

## Next Approved Work Types

Allowed next work types are design review, threat model refinement, connector
boundary review, credential lifecycle design, migration design, CI gate design,
and rollback design. Runtime auth remains blocked until a later ADR changes
that boundary.
