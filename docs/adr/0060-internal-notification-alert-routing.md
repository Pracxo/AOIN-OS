# 0060: Internal Notification and Alert Routing

## Status

Accepted

## Context

AION Brain needs a local way to surface important internal signals to operators
without coupling Brain core to external notification services or source-system
remediation behavior.

## Decision

AION Brain adds an Internal Notification Center with local notification topics,
subscriptions, delivered notifications, alert records, escalation records, and
deterministic digests.

The notification center is local-only in v0.1. It supports local channels such
as operator inbox, actor inbox, workspace feed, audit feed, visual feed, and
local digest. It does not send email, SMS, webhook, Slack, Teams, push, or any
other external delivery.

Alerts and escalations are review signals only. They do not execute
remediation, mutate source records, auto-resolve source records, retry work,
cancel work, resume work, or bypass policy.

## Consequences

Operators and future UI layers can query local notifications, alerts,
escalations, and digests through Brain-owned contracts. Future external
delivery adapters can be designed later without changing the core contracts or
weakening policy boundaries.

## Constraints

- Notification and alert APIs return AION-owned contracts only.
- Every create, read, update, publish, evaluate, and digest path is policy-gated.
- Payloads and display text must redact hidden reasoning, raw prompts, raw
  headers, provider payload markers, and secret-like keys.
- Visual telemetry may project notification activity, but no frontend code is
  added by this decision.
- No domain-specific notification topics, alert rules, escalation rules, or
  digest logic belong in Brain core.
