# Local Auth Prototype Review

## Purpose

AION-104 reviews the local auth, local session, role filtering, dry-run action
authorization, production auth architecture, and disabled auth runtime work
before any future auth implementation phase. The review creates a stable auth
safety baseline and freezes the current disabled/mock-only posture.

## Scope Reviewed

- Local auth design.
- Local auth contract and dev identity simulation.
- Read-only local session preview.
- Role-aware static console filtering.
- Dry-run action authorization.
- Production auth architecture decision.
- Disabled auth runtime status and mock claims preview.
- Static console auth panels.
- Auth safety scripts and docs checks.

## AION-093 Through AION-099 Summary

AION-093 documented local auth design without adding production auth. AION-094
added dev-only local auth contracts and identity simulation. AION-095 added a
read-only local session preview. AION-096 added role-aware visibility filtering.
AION-097 added dry-run authorization for previews and review records. AION-098
selected future production auth architecture while keeping runtime auth off.
AION-099 added a disabled auth runtime and mock claims preview.

## Current Safe State

The current path is local, read-only, disabled, and mock-only where applicable.
Policy remains authoritative. Static console role/session/auth displays are
preview evidence only. Action authorization grants preview/review records only
and cannot execute.

## What Remains Disabled

Production auth, auth runtime enablement, login/logout routes, credentials,
token issuance, cookie issuance, session persistence, external identity
provider runtime, provider SDK dependencies, writes, activation, execution,
runtime registration, code loading, and external calls remain disabled.

## What Remains Mock-Only

Mock claims preview and actor mapping preview remain synthetic. They do not
authenticate users, trust browser-provided material, issue protected material,
persist state, or authorize execution.

## Known Gaps

- No production auth threat implementation is approved.
- No provider integration is configured.
- No credential lifecycle exists.
- No browser session lifecycle exists.
- No migration exists for auth records.
- No user-facing login/logout flow exists.

## Review Decision

The prototype review passes when `./scripts/auth-prototype-review.sh` and
`./scripts/auth-no-go-regression.sh` pass. The review decision for AION-104 is
to keep auth disabled/mock-only and require this evidence pack before future
auth work.

## Next Phase Recommendation

AION-105 and later work may proceed only as design, boundary, or
pre-implementation planning unless the pre-implementation gate is explicitly
satisfied by a new ADR and green CI. Runtime auth implementation remains out of
scope after AION-104.
