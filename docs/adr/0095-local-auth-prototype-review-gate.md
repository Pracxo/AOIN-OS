# 0095: Local Auth Prototype Review Gate

## Status

Accepted

## Context

AION-093 through AION-099 established local auth design, dev identity
simulation, read-only local sessions, role filtering, dry-run action
authorization, production auth architecture, and a disabled auth runtime. AION
needs a stable auth safety baseline before implementation phases.

## Decision

Add a local auth prototype review gate.

Auth work remains disabled/mock-only after AION-104.

No auth implementation is allowed until the pre-implementation gate is
satisfied.

Local auth, session, action authorization, static console, and auth runtime
evidence becomes mandatory before future auth work.

## Reason

AION needs a stable auth safety baseline before implementation phases. The
review gate separates evidence and architecture readiness from runtime auth
implementation.

## Consequences

Future auth tasks must pass `./scripts/auth-prototype-review.sh` and
`./scripts/auth-no-go-regression.sh`. A later implementation ADR must define
the exact boundary change, threat model, CI gate, rollback path, and release
blockers.

## Constraints

- No production auth.
- No credentials, tokens, cookies, or sessions.
- No external identity provider.
- No privileged bypass.
- No provider SDK, package file, migration, API router, frontend dependency,
  write path, activation path, execution path, or external call.
