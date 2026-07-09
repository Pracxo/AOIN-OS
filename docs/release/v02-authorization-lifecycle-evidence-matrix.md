
# v0.2 Authorization Lifecycle Evidence Matrix

| Authorization state | Required evidence | Required reviewer | Required ADR | Required gate | Explicit approval record state | Implementation authorization state | Runtime enablement guard release state | Runtime enabled | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| authorization_intake | candidate scope, owner, risk class | architecture reviewer | candidate ADR | intake gate | draft | unapproved | false | false | missing explicit approval | preview-only baseline |
| approval_record_drafted | approval fields and reviewers | security reviewer | candidate ADR | record freeze | created | unapproved | false | false | approval remains false | preview-only baseline |
| evidence_attached | evidence refs and rollback proof | operator reviewer | candidate ADR | evidence gate | created | unapproved | false | false | evidence not approved | preview-only baseline |
| guard_bound | runtime guard mapping | runtime reviewer | candidate ADR | guard gate | created | unapproved | false | false | guard release absent | preview-only baseline |
| authorization_review_preview | review notes only | review board | candidate ADR | review gate | preview | unapproved | false | false | reviewer signoff is not approval | preview-only baseline |
| authorization_pending | complete packet pending future decision | runtime board | candidate ADR | future approval gate | pending | unapproved | false | false | future decision required | preview-only baseline |
| authorization_blocked | no-go evidence | release reviewer | candidate ADR | no-go regression | blocked | unapproved | false | false | no-go condition active | preview-only baseline |
