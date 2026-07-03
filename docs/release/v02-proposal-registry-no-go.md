# v0.2 Proposal Registry No-Go

## Purpose

The AION-126 no-go list keeps the workstream proposal registry as planning-only preview evidence. The registry fails closed if any proposal, queue item, example, static data file, or script suggests implementation approval or runtime enablement.

## No-Go Checks

- implementation approval set true
- workstream implementation approval set true
- proposal state implies implementation approved
- approval queue item marked approved
- approval workflow bypassed
- approval record missing
- ADR dependency bypassed
- gate dependency bypassed
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

## Expected Result

Every proposal registry no-go check remains false, disabled, absent, or blocked. The regression passes only when the registry exists, the queue remains preview-only, and implementation remains unapproved.

## AION-127 Stabilization Additions

AION-127 adds no-go checks for proposal implementation approval true, approval
expiry bypassed, approval revocation bypassed, and dual-control bypassed. It
also preserves the existing checks for approval queue item approval,
implementation approval, workstream implementation approval, backlog
implementation approval, approval workflow bypass, approval record missing,
ADR dependency bypass, gate dependency bypass, v0.2 tag creation, v0.2 release
creation, runtime enablement, external calls, credential/token storage,
sandbox execution, package files, migrations, and runtime API execution routes.
