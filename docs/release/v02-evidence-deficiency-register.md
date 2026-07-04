# v0.2 Evidence Deficiency Register

| Deficiency | Consequence | Required correction | Release blocker | Approval blocker |
| --- | --- | --- | --- | --- |
| missing problem statement | Review cannot establish scope. | Add a complete problem statement. | yes | yes |
| missing risk statement | Review cannot assess implementation risk. | Add security, operational, data, and rollback risk. | yes | yes |
| missing security impact | Security review cannot proceed. | Add auth, external-call, protected-material, sandbox, write, module, code-loading, and bypass impact. | yes | yes |
| missing architecture impact | Architecture review cannot proceed. | Add service, API, SDK, CLI, config, data, audit, failure, rollback, and drift impact. | yes | yes |
| missing policy impact | Policy review cannot proceed. | Add policy impact, denial states, approval dependencies, and no-go enforcement. | yes | yes |
| missing audit/provenance impact | Evidence traceability is incomplete. | Add audit, provenance, redaction, retained evidence, and effect verification. | yes | yes |
| missing rollback plan | Recovery cannot be reviewed. | Add rollback steps, recovery, revocation, and verification evidence. | yes | yes |
| missing ADR dependency | Architecture decision path is incomplete. | Add required ADR dependency. | yes | yes |
| missing gate dependency | Verification path is incomplete. | Add required local gate dependency. | yes | yes |
| missing test evidence | Scope and safety cannot be verified. | Add required test evidence. | yes | yes |
| missing no-go acknowledgement | The request does not accept blocker conditions. | Add explicit no-go acknowledgement. | yes | yes |
| approval status not false | The request attempts approval without authority. | Reset all approval states to false. | yes | yes |

## AION-133 Final Review Dependency

AION-133 uses this deficiency register as inherited evidence. Any missing final
review evidence, pre-approval submission evidence, request approval guard
evidence, ADR dependency, gate dependency, or no-go acknowledgement remains a
release blocker and approval blocker.
