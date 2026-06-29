# Operator Action Intent Lifecycle

## Purpose

AION-107 defines the future action intent lifecycle while keeping the current
system dry-run and review only.

## States

| State | Meaning | Current reachability |
| --- | --- | --- |
| drafted | Intent draft captured before request submission. | future only |
| requested | Operator requested a governed action record. | reachable |
| dry_run_authorized | Dry-run action authorization allowed preview or review flow. | reachable |
| previewed | Dry-run preview exists with expected and blocked effects. | reachable |
| reviewed | Reviewer recorded review evidence. | reachable |
| approval_required | Policy or risk requires future approval. | descriptive only |
| approved_for_future_execution | Future approval boundary has approved an intent. | not reachable today |
| blocked | Policy, role, session, connector, rollback, or no-go control blocked the intent. | reachable |
| expired | Time-bound approval or preview is no longer current. | future only |
| cancelled | Requester or reviewer cancelled the intent. | future only |
| future_execution_ready | All future execution gates are satisfied. | not reachable today |
| future_executed | Future execution attempt completed. | not reachable today |
| rollback_requested | Future rollback or compensating action was requested. | not reachable today |
| rollback_completed | Future rollback or compensating action completed. | not reachable today |
| archived | Intent retained as historical audit evidence. | future only |

## Current lifecycle stop

The current lifecycle stops at previewed/reviewed/blocked. AION can create
request records, dry-run previews, blockers, and review evidence. It cannot
advance an intent into execution readiness.

future_execution_ready and future_executed are not reachable today.

## Future transition requirements

Future transitions beyond reviewed require production auth, role mapping,
approval workflow, policy decision, action authorization, connector/target
boundary, rollback design, audit/provenance, dry-run parity, stale-preview
checks, target drift checks, operator training, and release/freeze gate
approval.

## No-go conditions

- current code reaches future_execution_ready
- current code reaches future_executed
- review record becomes execution permission
- approval record bypasses policy
- stale preview becomes executable
- missing rollback plan becomes executable
