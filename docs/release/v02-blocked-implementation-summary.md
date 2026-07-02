# v0.2 Blocked Implementation Summary

| Blocked area | Blocked reason | Required ADR | Required gate | Required security evidence | Unblock condition |
| --- | --- | --- | --- | --- | --- |
| production auth implementation | production auth, credentials, sessions, and external identity runtime remain unapproved | production auth implementation ADR | production auth implementation gate | auth threat model, credential lifecycle, session controls, rollback, audit/provenance | scoped ADR and gate pass with approval update |
| connector runtime implementation | connector runtime, route registration, external calls, and connector dependencies remain disabled | connector runtime implementation ADR | connector runtime implementation gate | trust model, egress/ingress controls, policy denial, rollback, audit/provenance | scoped ADR and gate pass with approval update |
| credential store implementation | credential and token storage are absent by design | credential store implementation ADR | credential store implementation gate | protected-material lifecycle, redaction, rotation, revocation, rollback | scoped ADR and gate pass with approval update |
| sandbox runtime implementation | sandbox execution, filesystem, network, process, import, and package execution remain disabled | sandbox runtime implementation ADR | sandbox runtime gate | isolation model, denial model, resource limits, rollback, audit/provenance | scoped ADR and gate pass with approval update |
| operator write execution | write execution, tool execution, hard delete, and bypass remain blocked | operator write execution ADR | operator write execution gate | policy enforcement, separation of duties, rollback, audit/provenance | scoped ADR and gate pass with approval update |
| module activation | code loading, runtime registration, package installation, and capability activation remain disabled | module activation ADR | module activation implementation gate | package trust, activation lifecycle, sandbox dependency, rollback, audit/provenance | scoped ADR and gate pass with approval update |
| external calls | network clients, provider SDKs, endpoints, egress, and notifications remain absent | external calls release ADR | external call release gate | egress policy, redaction, allowlist model, rollback, audit/provenance | scoped ADR and gate pass with approval update |
| runtime route registration | API runtime execution routes, SDK resources, and CLI implementations remain blocked | runtime route registration ADR | runtime route registration gate | route ownership, exposure review, authz review, rollback, audit/provenance | scoped ADR and gate pass with approval update |
| package dependency additions | frontend dependencies, provider SDKs, connector SDKs, and package manager files remain blocked | dependency approval ADR | dependency drift gate | dependency risk review, license/security review, rollback | scoped ADR and gate pass with approval update |
| migrations | schema changes remain blocked during readiness closeout | migration ADR | migration readiness gate | migration plan, rollback plan, data safety review | scoped ADR and gate pass with approval update |
| production UI implementation | static console remains dependency-free and read-only | production UI decision ADR | production UI gate | UI threat model, build posture, authz review, rollback | scoped ADR and gate pass with approval update |

## AION-122 Kickoff Boundary

AION-122 keeps every blocked implementation area blocked. It adds request,
approval, ADR, gate, security, rollback, audit/provenance, and operator review
requirements that future tasks must satisfy before any unblock condition can be
considered.

## AION-123 Approval Workflow Stabilization

AION-123 keeps every blocked implementation area blocked. It adds stabilized
intake validation, approval decision evidence, expiry and revocation rules,
dual-control review, and approval workflow no-go regression before any future
implementation can be considered.
