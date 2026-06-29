# Future Auth Implementation Plan

No production auth may be implemented before AION-098.

AION-099 does not start production auth implementation. It only adds disabled
auth runtime status, mock claims preview, and audit proof for future review.

## AION-094

Local auth contract and dev-only identity simulation.

## AION-095

Read-only local session prototype.

## AION-096

Role-aware console view filtering.

## AION-097

Dry-run action authorization enforcement.

## AION-098

Production auth architecture decision.

The decision selects OIDC-compatible production auth as the future primary path
and reverse proxy auth as an optional later deployment pattern. No production
auth is implemented in AION-098. No provider integration is added in AION-098.
No credentials, tokens, sessions, or cookies are created, stored, issued, or
accepted. `production_auth_enabled` remains false.

## AION-099

Production auth prototype behind disabled flag.

The AION-099 prototype may be mock-only and disabled by default. It must use
synthetic claims only, make no external provider call, issue no real token,
create no real login, and pass the AION-098 release gates before any future
enablement.

## Gates

Every stage must preserve ActorContext, policy, audit, approval, autonomy, and
redaction boundaries. Any implementation that stores credentials, creates
production sessions, integrates an external identity provider, or exposes
login endpoints before its designated stage is blocked.

## AION-101 Operator Platform Checkpoint

AION-101 is not an auth implementation stage. It adds a checkpoint evidence
pack proving the static Operator Platform remains read-only and that production
auth, auth runtime enablement, login/logout, token issuance, cookie issuance,
credential storage, persisted sessions, and external identity provider runtime
remain blocked before AION-102 planning begins.

## AION-102 Operator Platform Stabilization

AION-102 is also not an auth implementation stage. It adds long-running
regression and freeze gates that rerun `production-auth-architecture-check.sh`,
`auth-runtime-check.sh`, `local-auth-check.sh`, and `local-session-check.sh`.
Production auth, auth runtime enablement, login/logout, token issuance, cookie
issuance, credential storage, persisted sessions, and external identity
provider runtime remain blocked.

## AION-094 Completed Scope

AION-094 completes the safe local contract and simulation step only. It does
not move production auth forward. Production authentication remains blocked
until the later architecture decision and gated prototype milestones.

## AION-095 Future Session Prerequisites

Read-only local session previews do not unlock production auth. Any future
production session implementation still requires a separate ADR, threat model,
policy update, credential and token handling decision, browser-state security
review, and migration approval.

## AION-096 Future Role Filtering Prerequisites

Role-aware filtering is still not production authorization. Future auth work
must decide how real identities map into the proof matrix without bypassing
policy, audit, redaction, or the forbidden-action guarantees.

## AION-097 Future Write Authorization Prerequisite

Future production or write authorization must extend the AION-097 dry-run model
instead of bypassing it. Real identity, session, and policy decisions must keep
denied decisions visible and must not weaken no-execution, no-activation,
no-external-call, and no-credential-storage guarantees.
