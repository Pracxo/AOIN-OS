# v0.2 Runtime Implementation Decision Framework

## Purpose

This framework defines the decision criteria for future v0.2 runtime
implementation proposals. It is planning-only and does not approve runtime
implementation.

## Decision Criteria

| Area | Current Approval State | Required ADR | Required Gate | Required Evidence | No-Go Conditions |
| --- | --- | --- | --- | --- | --- |
| production auth | unapproved | production auth implementation ADR | production auth implementation gate | threat model, session lifecycle, credential handling, rollback, audit/provenance, operator review | login/runtime enabled, credentials or tokens stored, external identity runtime enabled, migrations added before approval |
| operator write execution | unapproved | operator write execution ADR | operator write execution gate | dry-run to write transition model, policy enforcement, separation of duties, rollback, audit/provenance, operator review | write execution enabled, tool execution enabled, hard delete enabled, approval bypass |
| connector runtime | unapproved | connector runtime implementation ADR | connector runtime implementation gate | connector trust model, egress/ingress guards, policy enforcement, rollback, audit/provenance, operator review | runtime enabled, external calls enabled, route registration enabled, connector SDK dependency added |
| connector credential store | unapproved | credential store implementation ADR | credential store implementation gate | protected-material lifecycle, redaction, rotation, revocation, audit/provenance, operator review | credentials stored, tokens stored, secret values exposed, credential access allowed before approval |
| sandbox execution | unapproved | sandbox runtime implementation ADR | sandbox runtime implementation gate | isolation model, file and network posture, process limits, deterministic failures, rollback, audit/provenance | sandbox execution enabled, filesystem/network/process access enabled, package installation enabled |
| module activation | unapproved | module activation ADR | module activation implementation gate | package trust, code loading boundary, capability activation model, rollback, audit/provenance, operator review | code loading enabled, runtime registration enabled, capability activation enabled, package files added |
| external calls | unapproved | external calls release ADR | external call release gate | egress allowlist, request/response redaction, policy enforcement, rollback, audit/provenance, operator review | external calls enabled, network client added, provider SDK dependency added, endpoint stored |
| runtime route registration | unapproved | runtime route registration ADR | runtime route registration gate | route ownership, policy action model, SDK/CLI exposure review, rollback, audit/provenance | API runtime execution route added, dynamic route registration enabled, SDK/CLI implementation added |
| audit/provenance | planning-only | rollback and audit ADR | audit/provenance hardening gate | append-only events, redaction evidence, correlation IDs, operator-visible review records | privileged bypass, audit bypass, raw secret exposure, hard delete |
| rollback | planning-only | rollback and audit ADR | rollback readiness gate | disable path, compensation plan, restore boundary, operator review | rollback-free execution, destructive remediation, hard delete |
| operator review | planning-only | production UI decision ADR or workstream ADR | operator review gate | reviewer roles, approval expiry, denial behavior, evidence links | automatic approval, approval bypass, unreviewed write execution |
| policy enforcement | planning-only | workstream ADR plus policy enforcement section | policy enforcement gate | policy actions, deny defaults, audit linkage, no-go tests | policy bypass, broad allow path, unaudited runtime permission |

## Framework Rules

Every future implementation proposal must state the area being changed, the
current approval state, the ADR that changes that state, the gate that proves
the change, and the rollback path if the gate fails.

If a proposal cannot provide ADR, gate, evidence, rollback, operator review,
and policy enforcement details, it remains backlog planning only.

## Approval Boundary

AION-119 keeps `runtime_implementation_approved=false` and keeps all scoped
implementation approvals false. This framework is not implementation approval.

## AION-120 Stabilization Requirement

After AION-120, implementation proposals must also pass the v0.2 planning
stabilization gate and backlog governance freeze. Readiness scores remain
planning evidence only until a scoped ADR, scoped implementation gate,
security review, rollback evidence, audit/provenance evidence, operator review,
and no-go regression pass.
