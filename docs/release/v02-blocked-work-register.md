# v0.2 Blocked Work Register

| Blocked Work | Reason Blocked | Required ADR | Required Gate | Required Evidence | Owner Placeholder | Unblock Condition |
| --- | --- | --- | --- | --- | --- | --- |
| production auth implementation | production runtime, credentials, sessions, and external identity remain unapproved | production auth implementation ADR | production auth implementation gate | threat model, credential lifecycle, rollback, audit/provenance, operator review | auth owner | scoped ADR and gate pass with approval update |
| connector runtime implementation | connector runtime, external calls, route registration, and connector SDK dependencies remain disabled | connector runtime implementation ADR | connector runtime implementation gate | trust model, egress/ingress guards, policy, rollback, audit/provenance | connector owner | scoped ADR and gate pass with approval update |
| credential store implementation | credential and token storage are absent by design | credential store implementation ADR | credential store implementation gate | protected-material lifecycle, redaction, rotation, revocation, rollback, audit | security owner | scoped ADR and gate pass with approval update |
| sandbox runtime implementation | sandbox execution, filesystem, network, process, import, and package installation remain disabled | sandbox runtime implementation ADR | sandbox runtime gate | isolation model, deterministic denial, rollback, audit/provenance | sandbox owner | scoped ADR and gate pass with approval update |
| operator write execution | write execution, tool execution, hard delete, and approval bypass remain blocked | operator write execution ADR | operator write execution gate | policy enforcement, separation of duties, rollback, audit/provenance | operator owner | scoped ADR and gate pass with approval update |
| module activation | code loading, runtime registration, package installation, and capability activation remain disabled | module activation ADR | module activation implementation gate | package trust, activation lifecycle, rollback, audit/provenance | module owner | scoped ADR and gate pass with approval update |
| external calls | network clients, endpoints, provider SDKs, and external model calls are absent | external calls release ADR | external call release gate | egress policy, redaction, audit/provenance, rollback | platform owner | scoped ADR and gate pass with approval update |
| runtime route registration | API runtime execution routes, SDK resources, and CLI commands are blocked | runtime route registration ADR | runtime route registration gate | route ownership, exposure review, rollback, audit/provenance | API owner | scoped ADR and gate pass with approval update |
| package dependency additions | frontend dependencies, provider SDKs, connector SDKs, and package manager files are blocked | dependency approval ADR | dependency drift gate | dependency risk review, rollback, license/security review | platform owner | scoped ADR and gate pass with approval update |
| migrations | schema changes are blocked during planning stabilization | migration ADR | migration readiness gate | migration plan, rollback plan, data safety review | data owner | scoped ADR and gate pass with approval update |
| production UI implementation | static console remains dependency-free and read-only | production UI decision ADR | production UI gate | UI boundary, build posture, security review, rollback | UI owner | scoped ADR and gate pass with approval update |

## AION-121 Final Review

AION-121 keeps every blocked work item blocked during planning closeout. The
blocked implementation summary in `docs/release/v02-blocked-implementation-summary.md`
is the final planning review snapshot and does not approve any unblock
condition.
