# v0.2 Approval Decision Evidence Matrix

| Workstream | Required ADR | Required Gate | Required Evidence | Required Reviewers | Approval Status | Runtime Approval Status | Release Blocker If Violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Production auth | future scoped ADR | future auth implementation gate | auth threat model, rollback, policy, audit evidence | requester, reviewer, security, architecture, operator, approver | false | false | production auth enabled before approval | No login, token, cookie, or external identity runtime is approved. |
| Connector runtime | future scoped ADR | future connector implementation gate | egress, ingress, credential, token, sandbox, rollback evidence | requester, reviewer, security, architecture, operator, approver | false | false | connector runtime enabled before approval | Connector runtime remains disabled. |
| Credential store | future scoped ADR | future credential store gate | redaction, lifecycle, audit, rollback evidence | requester, reviewer, security, architecture, auditor, approver | false | false | credential or token storage enabled before approval | No protected material is stored. |
| Sandbox runtime | future scoped ADR | future sandbox runtime gate | isolation, filesystem, network, process, package evidence | requester, reviewer, security, architecture, operator, approver | false | false | sandbox execution enabled before approval | Sandbox execution remains absent. |
| Operator write execution | future scoped ADR | future operator write gate | dry-run parity, rollback, audit, approval evidence | requester, reviewer, security, architecture, operator, approver | false | false | operator write execution enabled before approval | Dry-run previews remain non-executing. |
| Module activation | future scoped ADR | future module activation gate | capability, code loading, route registration, policy evidence | requester, reviewer, security, architecture, operator, approver | false | false | module activation enabled before approval | Activation remains blocked. |
| External calls | future scoped ADR | future external call gate | provider, network, egress, audit, rollback evidence | requester, reviewer, security, architecture, operator, approver | false | false | external calls enabled before approval | No external service call path is approved. |

All rows require expiry, revocation, ADR dependency, gate dependency, no-go
acknowledgement, and refreshed evidence before approval can be considered.
