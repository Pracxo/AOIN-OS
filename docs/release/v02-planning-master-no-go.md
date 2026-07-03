# v0.2 Planning Master No-Go

The planning master checkpoint fails if any master no-go condition appears:

- v0.2 tag created
- v0.2 release created
- runtime implementation approval true
- backlog implementation approval true
- workstream implementation approval true
- proposal implementation approval true
- approval queue item approved true
- approval workflow bypassed
- approval record missing
- ADR dependency bypassed
- gate dependency bypassed
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

Allowed planning files may describe denied, disabled, no-go, future, planning, unapproved, template, or preview states only. They must not create runtime behavior or implementation approval.

## AION-129 Final Planning Extension

The final planning no-go regression in
`docs/release/v02-final-planning-no-go.md` inherits these no-go checks and adds
final release-gate evidence. The same implementation, queue, proposal,
bypass, external-call, credential/token, sandbox, package, migration, API
route, v0.2 tag, and v0.2 release blockers remain active.
