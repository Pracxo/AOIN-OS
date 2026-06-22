# Operator Control Tower

AION v0.1 Operator Control Tower is a backend API for local operator visibility.
It aggregates generic Brain status into one read-mostly control surface.

It does not implement a frontend, execute actions, approve requests, process
queues, change runtime configuration, or remediate issues automatically.

## Status Cards

Status cards summarize local subsystem state: kernel, health, resilience,
runtime configuration, policy, audit integrity, approvals, commands, events,
workflows, performance, backups, release, visual projection, SDK, and operator
services.

Missing optional services produce warning cards instead of API failures.

## Queue Summaries

Queue summaries expose counts only. They cover approvals, commands, outbox,
inbox, workflows, tasks, event dead letters, backup jobs, release packages,
audit verifications, resilience tests, security scans, and scenarios.

The queue API never processes or cancels queue items.

## Action Center

The Action Center converts local signals into generic recommendations such as:

- `review_pending_approval`
- `inspect_failed_command`
- `inspect_degraded_component`
- `run_audit_verification`
- `review_release_readiness`
- `run_kernel_self_test`

Recommendations are instructions for an operator. They are not executed by the
Operator Control Tower.

## Readiness Report

Readiness reports combine cards and action items into:

- `release_ready`
- `local_ops_ready`
- generic checks
- blockers
- warnings

Readiness is local and deterministic. It does not call external services.

## Snapshots

Operator snapshots persist a local metadata view of overview, actions, queues,
and readiness. Snapshots are useful before release checks or local incident
review.

## Acknowledgements

Acknowledgements record that an operator has seen an item. They do not resolve,
approve, cancel, retry, or mutate the source issue.

## Runbook Links

Runbook links point to local documentation only. Future UIs can render these
links, but v0.1 exposes them as backend contracts.

## Limitations

AION v0.1 Operator Control Tower is a backend API only. It does not implement a
frontend or automatic remediation.
