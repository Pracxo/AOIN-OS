# v0.2 Submission Review Matrix

| Submission field | Required evidence | Reviewer | Gate dependency | Approval state | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Problem statement | Complete scope and problem description | Product/governance reviewer | Evidence completeness gate | false | yes | Required before review starts |
| Risk statement | Security, operational, data, and rollback risk | Security reviewer | Evidence completeness gate | false | yes | Risk evidence does not approve implementation |
| Security impact | Auth, external-call, protected-material, sandbox, write, module, code-loading, and bypass impact | Security reviewer | Security review gate | false | yes | External calls and protected-material persistence remain blocked |
| Architecture impact | Service, API, SDK, CLI, config, data, audit, failure, rollback, and drift impact | Architecture reviewer | Architecture review gate | false | yes | No runtime route or SDK/CLI implementation is added |
| Policy impact | Policy, denial, approval, and no-go impact | Policy reviewer | Policy review gate | false | yes | No policy bypass is allowed |
| Audit/provenance impact | Audit records, provenance records, redaction, retained evidence, and effect verification | Audit reviewer | Audit/provenance gate | false | yes | Evidence remains review-only |
| Rollback plan | Rollback steps, recovery, revocation, and verification evidence | Operator reviewer | Rollback/recovery gate | false | yes | Rollback plan does not approve execution |
| ADR dependency | Required ADR reference | Architecture reviewer | ADR review gate | false | yes | ADR review does not enable runtime |
| Gate dependency | Required local gate reference | Release reviewer | Local release gate | false | yes | Gate success does not approve implementation |
| Test evidence | Scope, safety, denial, and rollback tests | Release reviewer | Test evidence gate | false | yes | Tests must pass before approval consideration |
| No-go acknowledgement | Explicit blocker acknowledgement | Governance reviewer | Request-pack no-go regression | false | yes | Any no-go violation blocks release and approval |
| Approval status false | All approval fields false | Governance reviewer | Submission freeze | false | yes | Approval records must remain explicit and separate |

## AION-133 Final Review Dependency

AION-133 adds a final submission evidence matrix on top of this review matrix.
The final matrix keeps approval state false, implementation state false, and
release blocker if violated true for request pack final state, evidence
boundary closeout, pre-approval submission, request approval guard, and
submission no-go review.
