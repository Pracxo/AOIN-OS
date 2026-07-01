# v0.2 No-Go Planning Boundary

## Purpose

This boundary defines planning failures for AION-119 and future v0.2 planning
branches. It keeps planning distinct from implementation.

## No-Go Conditions

Planning fails if any branch creates or approves:

- v0.2 tag created
- v0.2 release created
- implementation approval set true
- production auth enabled
- connector runtime enabled
- operator write execution enabled
- module activation enabled
- external calls enabled
- credential/token storage enabled
- sandbox execution enabled
- package files added
- migrations added
- runtime API execution routes added

## Blocked Work Types

Blocked work includes network clients, provider SDKs, connector SDK
dependencies, OAuth/OIDC/SAML runtime, login/logout runtime, session
persistence, dynamic route registration, SDK resource implementations, CLI
command implementations, code loading, package installation, hard delete,
policy bypass, audit bypass, privileged bypass, and release creation.

## Allowed Planning Evidence

Planning may add docs, synthetic JSON examples, static read-only demo data,
tests, and repository-local verification scripts. The evidence must state that
implementation remains unapproved.

## Failure Handling

If a no-go condition is detected, remove the implementation drift, restore the
planning-only boundary, rerun `./scripts/v02-planning-no-go-regression.sh`, and
rerun `./scripts/v02-planning-charter-check.sh`.

## AION-120 Stabilization No-Go Additions

AION-120 adds backlog implementation approval set true as an explicit no-go
condition and adds `./scripts/v02-planning-stabilization-no-go-regression.sh`
as the stabilization regression check. Backlog implementation approval remains
false until a future scoped ADR and gate explicitly approve a narrower change.
