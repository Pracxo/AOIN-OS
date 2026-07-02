# v0.2 Workstream Readiness Scorecard

## Purpose

This scorecard ranks candidate v0.2 workstreams for planning intake only. Implementation allowed today: false for every row.

| Workstream | Readiness Score | Approval State | Required ADR | Required Gate | Blocker | Next Planning Action | Implementation Allowed Today |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| production auth implementation planning | 72 | approval false | production auth implementation ADR | production auth gate | auth runtime remains disabled | refine security and rollback evidence | false |
| audit/provenance hardening planning | 70 | approval false | audit/provenance hardening ADR | audit hardening gate | implementation approval absent | define evidence refresh and rollback checks | false |
| rollback/recovery planning | 68 | approval false | rollback/recovery implementation ADR | recovery gate | recovery execution not approved | define dry-run restoration evidence | false |
| external call release gate planning | 62 | approval false | external call release gate ADR | external call gate | external calls remain absent | define egress policy and release blocker matrix | false |
| connector runtime implementation planning | 55 | approval false | connector runtime implementation ADR | connector runtime gate | connector runtime remains locked | map runtime route and credential boundaries | false |
| credential store implementation planning | 52 | approval false | credential store implementation ADR | credential store gate | credential/token storage remains locked | define lifecycle and redaction evidence | false |
| sandbox runtime implementation planning | 50 | approval false | sandbox runtime implementation ADR | sandbox runtime gate | sandbox execution remains locked | define isolation and no-network evidence | false |
| operator write execution planning | 48 | approval false | operator write execution ADR | write execution gate | write execution remains locked | define dual-control and rollback evidence | false |
| module activation implementation planning | 45 | approval false | module activation implementation ADR | module activation gate | module activation remains locked | define package, code loading, and registration blockers | false |
| production UI decision planning | 40 | approval false | production UI decision ADR | production UI gate | production UI remains undecided | compare static console constraints and future runtime needs | false |

## Guardrail

Readiness scores are planning signals only. They are not approval records, runtime approvals, or release approvals.
AION-125 closes this scorecard into the final pre-implementation planning
baseline. Each listed workstream remains planning-only with implementation
allowed today: false.
