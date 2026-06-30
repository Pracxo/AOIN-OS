# Connector Pre-Implementation Gate

## Purpose

The pre-implementation gate defines the evidence required before any future connector runtime implementation can begin.

## Required Gate Evidence

| Gate | Required state |
| --- | --- |
| threat model approved | required before implementation |
| credential storage design approved | required before implementation |
| egress allowlist approved | required before implementation |
| ingress redaction approved | required before implementation |
| provenance design approved | required before implementation |
| policy actions approved | required before implementation |
| operator review approved | required before implementation |
| sandbox design approved | required before implementation |
| dry-run simulator green | required before implementation |
| disabled prototype green | required before implementation |
| release gate green | required before implementation |

## No-Go Conditions

- connector runtime enabled before release gate approval
- external call path added before egress allowlist approval
- credential or token storage added before approved storage design
- dynamic route registration added
- connector activation enabled
- raw prompt egress allowed
- hidden reasoning egress allowed
- secret egress allowed
- policy bypass
- audit bypass
- package dependency added
- migration added

## Decision

No connector implementation phase can start until this gate is complete and the no-external-call regression remains passed.

## AION-110 Gate Evidence

The dry-run simulator row is satisfied only when simulator contracts, replay
fixtures, policy readiness, no-go regression, SDK/CLI wrappers, docs, examples,
and static console evidence remain synthetic-only and runtime-disabled.

## AION-111 Gate Evidence

The policy actions row is satisfied only when the connector policy action
catalog, authorization matrix, dry-run gate, denial rules, traceability
records, SDK/CLI preview commands, docs, examples, and static console policy
preview remain read-only and fail closed for runtime, external calls,
credentials, tokens, activation, route registration, tool execution, and write
execution.
