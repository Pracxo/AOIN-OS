# v0.2 Approval Workflow No-Go

The approval workflow is blocked when any of the following are detected:

- implementation approval set true
- backlog implementation approval set true
- approval workflow bypassed
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

No-go findings fail closed. They must be resolved through a future scoped
request, ADR, gate, no-go regression, reviewer evidence, and explicit approval
record before implementation can be considered.
