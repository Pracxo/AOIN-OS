# ADR 0109: Post-v0.1 Release Candidate Gate

## Status

Accepted

## Context

AION-101 through AION-117 established operator platform checkpoint and
stabilization evidence, static console UX and safety evidence, local auth
prototype review evidence, module activation design review evidence, connector
boundary and runtime-disabled evidence, connector simulator, policy, sandbox,
credential, release, checkpoint, and stabilization evidence, and the
cross-phase operator and connector platform integration checkpoint.

AION now needs a stable post-v0.1 candidate baseline before v0.2 planning can
begin.

## Decision

Decision: add post-v0.1 release candidate gate.

Decision: no v0.2 release or tag is created by AION-118.

Decision: runtime implementation remains unapproved.

Decision: future v0.2 work requires explicit planning and ADR gates.

Decision: preserve `aion-v0.1.0` without moving, deleting, or recreating it.

## Reason

AION needs a stable post-v0.1 candidate baseline before v0.2 planning. The
release candidate gate gives the operator, connector, auth, module, static UI,
docs, and boundary evidence one consolidated checkpoint while avoiding implicit
runtime approval.

## Consequences

v0.2 work starts from a frozen evidence baseline. Future tasks must add
explicit ADRs and gates before implementation work can set any approval boolean
true or create runtime behavior.

The release candidate gate is a blocker for future v0.2 planning drift. It is
not a release artifact and does not create or imply a v0.2 tag.

## Constraints

Constraint: no runtime enablement.

Constraint: no external calls.

Constraint: no credentials/tokens.

Constraint: no sandbox execution.

Constraint: no privileged bypass.

Constraint: no operator write execution.

Constraint: no connector runtime implementation.

Constraint: no production auth implementation.

Constraint: no module activation, capability activation, code loading, or
runtime registration.

Constraint: no package manager files, lockfiles, frontend dependencies,
migrations, runtime API execution routes, SDK resource implementations, or CLI
command implementations.

Constraint: no v0.2 tag or release.

Constraint: no mutation of `aion-v0.1.0`.

## Verification

```bash
./scripts/post-v01-release-candidate-gate.sh
./scripts/post-v01-release-candidate-freeze.sh
./scripts/post-v01-release-candidate-no-go-regression.sh
./scripts/check.sh
git diff --check
```
