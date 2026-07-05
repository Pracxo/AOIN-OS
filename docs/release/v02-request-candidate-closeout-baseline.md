# v0.2 Request Candidate Closeout Baseline

## Purpose

Close out the request candidate set as planning evidence for the stabilized
submission registry. These rows do not approve submissions, implementations, or
runtime behavior.

| Candidate ID | Candidate | Workstream | Submission status | Pre-approval queue status | Submission approval | Implementation approval | Required ADR | Required gate | Required evidence | Blocker | Next planning action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V02-CAND-PROD-AUTH | production auth implementation candidate | production_auth | closeout_recorded | queued_preview_only | false | false | future production auth ADR | production auth implementation gate | auth threat model and session boundary evidence | production auth approval absent | draft approval request record |
| V02-CAND-AUDIT-PROV | audit/provenance hardening candidate | audit_provenance | closeout_recorded | queued_preview_only | false | false | future audit hardening ADR | audit provenance hardening gate | audit chain and provenance verification evidence | provenance gate absent | define evidence owner |
| V02-CAND-ROLLBACK | rollback/recovery candidate | rollback_recovery | closeout_recorded | queued_preview_only | false | false | future rollback ADR | rollback recovery gate | rollback scenario matrix and recovery evidence | rollback rehearsal absent | write recovery acceptance criteria |
| V02-CAND-EXT-CALL-GATE | external call release gate candidate | external_call_release_gate | closeout_recorded | queued_preview_only | false | false | future external call ADR | external call release gate | egress policy and no-external-call evidence | external call approval absent | define egress review template |
| V02-CAND-CONN-RUNTIME | connector runtime implementation candidate | connector_runtime | closeout_recorded | queued_preview_only | false | false | future connector runtime ADR | connector runtime implementation gate | disabled runtime and policy evidence | connector implementation approval absent | draft connector implementation request |
| V02-CAND-CRED-STORE | credential store implementation candidate | credential_store | closeout_recorded | queued_preview_only | false | false | future credential store ADR | credential storage gate | redaction, lifecycle, and storage design evidence | credential storage approval absent | define secret handling evidence |
| V02-CAND-SANDBOX | sandbox runtime implementation candidate | sandbox_runtime | closeout_recorded | queued_preview_only | false | false | future sandbox runtime ADR | sandbox execution gate | isolation, filesystem, network, and process evidence | sandbox execution approval absent | define isolation proof checklist |
| V02-CAND-OP-WRITE | operator write execution candidate | operator_write_execution | closeout_recorded | queued_preview_only | false | false | future operator write ADR | operator write execution gate | approval, rollback, audit, and policy evidence | write execution approval absent | draft write-path approval record |
| V02-CAND-MODULE-ACT | module activation candidate | module_activation | closeout_recorded | queued_preview_only | false | false | future module activation ADR | module activation implementation gate | module safety and activation boundary evidence | module activation approval absent | define capability activation review |
| V02-CAND-PROD-UI | production UI decision candidate | production_ui_decision | closeout_recorded | queued_preview_only | false | false | future production UI ADR | production UI release gate | dependency, safety, and release readiness evidence | production UI approval absent | draft UI decision packet |

## AION-136 Review Board Handoff

These candidates now have review-board routing paths in
`docs/release/v02-submission-review-routing.md`. The routing paths do not
approve implementation and do not enable runtime.
