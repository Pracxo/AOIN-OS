
# v0.2 Runtime Enablement Guard Evidence Baseline

AION-148 records the candidate runtime areas that remain blocked by the runtime
enablement guard. Every candidate keeps guard release approval false,
implementation authorization approval false, and implementation go status false.

| Candidate ID | Candidate area | Explicit approval record state | Authorization state | Runtime enablement guard state | Guard release approved | Implementation authorization approved | Implementation go status | Required ADR | Required gate | Required evidence | Blocker | Next planning action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-IMPL | production auth implementation candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-PROD-AUTH | production-auth-release-gate | identity threat model, token/session storage decision, credential handling review | production auth remains disabled | prepare explicit approval record draft only |
| AUDIT-HARDEN | audit/provenance hardening candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-AUDIT-HARDEN | audit-provenance-hardening-gate | audit schema review, provenance retention plan, rollback proof | implementation approval absent | collect reviewer evidence |
| ROLLBACK-RECOVERY | rollback/recovery candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-ROLLBACK | rollback-recovery-gate | rollback scenario matrix, recovery drill proof, operator review | runtime guard release absent | draft rollback evidence packet |
| EXTERNAL-CALL-GATE | external call release gate candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-EXTERNAL-CALL | external-call-release-gate | network boundary proof, provider review, no-secret evidence | external calls remain absent | define provider-neutral no-go gate |
| CONNECTOR-RUNTIME | connector runtime implementation candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-CONNECTOR-RUNTIME | connector-runtime-implementation-gate | connector policy proof, disabled runtime review, sandbox no-go evidence | connector runtime remains disabled | keep runtime implementation queued |
| CREDENTIAL-STORE | credential store implementation candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-CREDENTIAL-STORE | credential-store-implementation-gate | secret lifecycle design, redaction proof, revocation plan | credential and token storage remain absent | prepare storage threat model |
| SANDBOX-RUNTIME | sandbox runtime implementation candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-SANDBOX-RUNTIME | sandbox-runtime-implementation-gate | isolation proof, filesystem/network denial evidence, process-spawn review | sandbox execution remains disabled | draft sandbox capability matrix |
| OPERATOR-WRITE | operator write execution candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-OPERATOR-WRITE | operator-write-execution-gate | approval chain, rollback proof, separation-of-duties evidence | operator write execution remains disabled | collect dual-control evidence |
| MODULE-ACTIVATION | module activation candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-MODULE-ACTIVATION | module-activation-gate | capability manifest review, code-loading denial proof, audit trail | module activation remains disabled | draft activation readiness proof |
| PROD-UI | production UI decision candidate | explicit_approval_record_approval=false | authorization_unapproved | runtime_enablement_guard_release_approved=false | false | false | false | ADR-PROD-UI | production-ui-decision-gate | static-console safety proof, auth boundary, runtime route denial evidence | production UI remains unimplemented | prepare UI boundary decision packet |

## AION-149 final lock handoff

AION-149 promotes this evidence baseline into a runtime enablement guard final
lock without releasing the guard. `runtime_enablement_guard_final_lock_created=true`
and `runtime_enablement_guard_final_lock_release_approved=false`.
