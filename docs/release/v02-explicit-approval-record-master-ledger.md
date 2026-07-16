# v0.2 Explicit Approval Record Master Ledger

| approval_record_id placeholder | candidate_id | workstream | requested runtime capability | approval_status | implementation_authorization_status | runtime_guard_release_status | implementation_go_status | required ADR | required gate | required evidence | required reviewers | rollback plan requirement | audit/provenance requirement | expiry requirement | revocation path | blocker | next governed action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APR-PROD-AUTH-TBD | AUTH-IMPL | production auth implementation | OAuth/OIDC/SAML runtime | false | false | false | false | ADR-PROD-AUTH | production-auth-release-gate | threat model and token/session storage decision | security, platform | required before approval | audit trail and auth provenance | required | revoke approval record | production auth disabled | draft explicit approval record only |
| APR-AUDIT-HARDEN-TBD | AUDIT-HARDEN | audit/provenance hardening | audit persistence hardening | false | false | false | false | ADR-AUDIT-HARDEN | audit-provenance-hardening-gate | audit schema and retention proof | platform, security | required before approval | provenance chain proof | required | revoke approval record | implementation approval absent | collect evidence |
| APR-ROLLBACK-TBD | ROLLBACK-RECOVERY | rollback/recovery | recovery workflow runtime | false | false | false | false | ADR-ROLLBACK | rollback-recovery-gate | recovery drill and scenario matrix | operations, platform | required before approval | rollback audit proof | required | revoke approval record | runtime guard locked | prepare drill plan |
| APR-EXTERNAL-CALL-TBD | EXTERNAL-CALL-GATE | external call release gate | provider/network egress | false | false | false | false | ADR-EXTERNAL-CALL | external-call-release-gate | network boundary and no-secret proof | security, platform | required before approval | egress audit proof | required | revoke approval record | external calls absent | define release gate |
| APR-CONNECTOR-TBD | CONNECTOR-RUNTIME | connector runtime implementation | connector runtime execution | false | false | false | false | ADR-CONNECTOR-RUNTIME | connector-runtime-implementation-gate | policy, sandbox, and disabled runtime proof | connector, security | required before approval | connector audit proof | required | revoke approval record | connector runtime disabled | keep queued |
| APR-CREDENTIAL-TBD | CREDENTIAL-STORE | credential store implementation | credential/token storage | false | false | false | false | ADR-CREDENTIAL-STORE | credential-store-implementation-gate | secret lifecycle and redaction proof | security | required before approval | credential provenance proof | required | revoke approval record | credential storage absent | draft threat model |
| APR-SANDBOX-TBD | SANDBOX-RUNTIME | sandbox runtime implementation | sandbox execution | false | false | false | false | ADR-SANDBOX-RUNTIME | sandbox-runtime-implementation-gate | isolation and process-spawn review | security, runtime | required before approval | sandbox audit proof | required | revoke approval record | sandbox execution disabled | draft capability matrix |
| APR-OPERATOR-WRITE-TBD | OPERATOR-WRITE | operator write execution | write-path execution | false | false | false | false | ADR-OPERATOR-WRITE | operator-write-execution-gate | dual-control and rollback proof | operations, security | required before approval | write audit proof | required | revoke approval record | operator writes disabled | collect dual-control evidence |
| APR-MODULE-ACTIVATION-TBD | MODULE-ACTIVATION | module activation | module/capability activation | false | false | false | false | ADR-MODULE-ACTIVATION | module-activation-gate | manifest and code-loading denial proof | module, security | required before approval | activation audit proof | required | revoke approval record | module activation disabled | prepare readiness proof |
| APR-PROD-UI-TBD | PROD-UI | production UI decision | production UI runtime | false | false | false | false | ADR-PROD-UI | production-ui-decision-gate | static-console safety and auth boundary proof | product, security | required before approval | UI action audit proof | required | revoke approval record | production UI unimplemented | prepare boundary packet |

## AION-151 Scoped Production Auth Authorization

AION-151 adds the canonical scoped authorization transaction `AION-151-PA-0001` for `production-auth-core` and future task `AION-152`. The authorization is limited to the `disabled-production-auth-core` implementation scope. Production-auth runtime remains disabled, runtime guard releases remain false, endpoint/storage/provider/external-call approvals remain false, package and migration changes remain false, and no v0.2 tag or release is created.

## AION-155 Scoped Request Boundary Authorization

AION-155 closes consumed `AION-153-PA-0002` evidence and creates
`AION-155-PA-0003` for future AION-156 disabled request identity boundary work.
The approval permits only disabled request identity contracts, verifier
interfaces, observe-only anonymous context attachment, audit/provenance
correlation, tests, docs, and read-only evidence. Runtime authentication,
identity verification, authenticated requests, protected-material handling,
provider integration, external calls, endpoints, package files, migrations,
SDK/CLI runtime surfaces, v0.2 tags, and v0.2 releases remain blocked.
