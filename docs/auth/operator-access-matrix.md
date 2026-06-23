# Operator Access Matrix

## Views

| View | viewer | operator | reviewer | admin | auditor |
| --- | --- | --- | --- | --- | --- |
| Overview | read | read | read | read | read |
| Readiness | read | read | read | read | read |
| Release Candidate | read | read | read | read | read |
| Module Lifecycle | read | read | read | read | read |
| Module Activation | read | read | read | read | read |
| Module Mock Runtime | read | read | read | read | read |
| Model Provider Hardening | read | read | read | read | read |
| Operator Actions | read | dry-run request, preview | review | read | read |
| Notifications | read | dismiss finding | review | read | read |
| Incidents | read | dismiss finding | review | read | read |
| Registry Integrity | read | dry-run request | review | read | read |
| Lifecycle Review | read | dry-run request | review | read | read |
| Audit/Provenance | read | read | read | read | read |
| Settings Safety | read | read | review | read | read |

## Actions

| Action | viewer | operator | reviewer | admin | auditor |
| --- | --- | --- | --- | --- | --- |
| read | yes | yes | yes | yes | yes |
| dry-run request | no | yes | yes | yes | no |
| preview | no | yes | yes | yes | no |
| review | no | no | yes | yes | no |
| dismiss finding | no | yes | yes | yes | no |
| export redacted summary | yes | yes | yes | yes | yes |

## Forbidden For All Roles In This Phase

- execute
- activate
- load code
- register route
- enable provider
- store credentials
- hard delete
- bypass policy

Every allowed action remains subject to policy, audit, approval, autonomy, and
redaction gates.
