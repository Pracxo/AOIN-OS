# v0.2 Workstream Intake No-Go

## Purpose

This no-go list blocks AION-124 if workstream intake readiness turns into implementation approval, runtime enablement, a tag, a release, or dependency drift.

## No-Go Checks

- implementation approval set true
- backlog implementation approval set true
- workstream marked implementation approved
- approval workflow bypassed
- approval record missing
- ADR dependency bypassed
- gate dependency bypassed
- approval expiry bypassed
- approval revocation bypassed
- dual-control bypassed
- v0.2 tag created
- v0.2 release created
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

## Enforcement

`./scripts/v02-workstream-intake-no-go-regression.sh` enforces the no-go checks using CI-safe Git reference handling and portable search.
