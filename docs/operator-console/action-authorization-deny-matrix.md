# Action Authorization Deny Matrix

The deny matrix is a proof artifact for fail-closed dry-run authorization.

Denied cases include:

- viewer requesting a dry-run operator action
- auditor requesting a dry-run operator action
- operator request with a denied local session boundary
- unsupported action type
- policy denial
- unsafe payload findings

Denied decisions are not hidden. They are returned as decision payloads,
operator action blockers, or blocked preview metadata. The matrix does not
create execution permission.
