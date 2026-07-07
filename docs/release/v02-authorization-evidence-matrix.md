# v0.2 Authorization Evidence Matrix

| Authorization area | Required evidence | Required reviewer | Required ADR | Required gate | Approval record state | Authorization state | Runtime guard release state | Runtime enabled | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Implementation authorization preview | Preview record, no-go acknowledgement, explicit schema | Architecture reviewer | ADR 0138 | `v02-implementation-authorization-preview-check.sh` | `explicit_approval_record_approval=false` | `implementation_authorization_approved=false` | `runtime_enablement_guard_release_approved=false` | false | Yes | Preview-only. |
| Runtime enablement guard | Guard boundary and lock evidence | Security reviewer | ADR 0138 | `v02-runtime-enablement-guard-freeze.sh` | `approval_status=false` | `authorization_unapproved` | false | false | Yes | Guard release remains blocked. |
| Approval vote record dependency | Vote record closeout evidence | Review board reviewer | ADR 0137 | `v02-runtime-approval-board-final-review.sh` | false | false | false | false | Yes | Vote records do not approve implementation. |
| Go/no-go ledger dependency | Final no-go ledger lock | Operator reviewer | ADR 0137 | `v02-implementation-go-no-go-final-freeze.sh` | false | false | false | false | Yes | `implementation_go_status=false`. |
| Release boundary | No tag and no release evidence | Release reviewer | ADR 0138 | `scripts/check.sh` | false | false | false | false | Yes | No v0.2 tag or release. |
