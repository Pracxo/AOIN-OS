# v0.2 Implementation Request Index

## Purpose

AION-126 indexes future implementation request types as planning-only registry entries. The index gives each request a stable ID, workstream, blocker, ADR dependency, gate dependency, and next planning action while keeping implementation approved: false.

## Request Index

| request ID | workstream | request type | status | implementation approved | required ADR | required gate | required evidence | blocker | next planning action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V02-REQ-001 | production auth | production auth implementation proposal | queued_for_future_decision | false | production auth implementation ADR | production auth release gate | auth threat model, rollback plan, operator review, no-go evidence | production auth approval remains false | draft scoped ADR and gate plan |
| V02-REQ-002 | audit/provenance | audit/provenance hardening proposal | queued_for_future_decision | false | audit provenance hardening ADR | provenance integrity gate | audit impact, provenance risk, replay evidence, no-go evidence | hardening scope not approved | define audit evidence matrix |
| V02-REQ-003 | rollback/recovery | rollback/recovery proposal | queued_for_future_decision | false | rollback recovery ADR | recovery rehearsal gate | recovery model, failure modes, operator review, no-go evidence | recovery implementation not approved | draft rollback rehearsal criteria |
| V02-REQ-004 | external call controls | external call release gate proposal | queued_for_future_decision | false | external call release gate ADR | external egress no-go gate | egress risk, provider boundary, policy impact, no-go evidence | external calls remain absent | define release-gate deny list |
| V02-REQ-005 | connectors | connector runtime implementation proposal | queued_for_future_decision | false | connector runtime ADR | connector runtime release gate | connector threat model, sandbox boundary, credential boundary, no-go evidence | connector runtime remains disabled | prepare runtime activation prerequisites |
| V02-REQ-006 | credential store | credential store implementation proposal | queued_for_future_decision | false | credential store ADR | credential storage gate | secret lifecycle, redaction, audit trail, no-go evidence | credential and token storage remain absent | draft storage approval record template |
| V02-REQ-007 | sandbox runtime | sandbox runtime implementation proposal | queued_for_future_decision | false | sandbox runtime ADR | sandbox execution gate | isolation model, filesystem boundary, process boundary, no-go evidence | sandbox execution remains disabled | define sandbox capability matrix |
| V02-REQ-008 | operator actions | operator write execution proposal | queued_for_future_decision | false | operator write execution ADR | operator write release gate | dual-control model, rollback plan, audit/provenance evidence, no-go evidence | operator write execution remains disabled | draft write-path approval workflow |
| V02-REQ-009 | modules | module activation proposal | queued_for_future_decision | false | module activation ADR | module activation gate | capability binding, code loading boundary, operator review, no-go evidence | module activation remains disabled | define activation certification checklist |
| V02-REQ-010 | production UI | production UI decision proposal | queued_for_future_decision | false | production UI decision ADR | production UI release gate | UX risk, dependency plan, auth boundary, no-go evidence | production UI remains undecided | compare static console and future UI needs |

## Approval Boundary

Every indexed request has implementation approved: false. The index does not approve runtime implementation, backlog implementation items, workstream implementation items, production auth, connector implementation, operator write execution, module activation, external calls, credential storage, token storage, sandbox execution, a v0.2 tag, or a v0.2 release.
