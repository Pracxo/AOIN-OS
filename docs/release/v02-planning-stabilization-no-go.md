# v0.2 Planning Stabilization No-Go

## Purpose

This no-go list freezes the AION-120 planning stabilization boundary. It is
planning-only and does not approve implementation.

## No-Go Checks

The stabilization no-go regression fails if any of these are present:

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
- backlog item marked implementation-approved

## Enforcement

The no-go script scans docs, examples, static console data, changed files, and
runtime-sensitive paths. It allows planning evidence only when the evidence is
disabled, denied, no-go, future, planning-only, or unapproved.

## Failure Handling

On failure, remove the unsafe drift, restore all approval booleans to false,
rerun `./scripts/v02-planning-stabilization-no-go-regression.sh`, rerun
`./scripts/v02-planning-stabilization-gate.sh`, and rerun the full repository
check before asking for review.
