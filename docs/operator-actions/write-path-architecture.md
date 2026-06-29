# Operator Action Write-Path Architecture

## Purpose

AION-107 defines the future operator action write path before any write
execution exists. The goal is to make approval, policy, connector, audit,
rollback, and operator review boundaries explicit while preserving the current
dry-run-only platform.

This document is design only. It adds no write execution, tool execution,
action proposal execution, controlled handoff execution, external call, module
activation, capability activation, connector runtime, API router, SDK resource,
CLI command, migration, production auth runtime, session persistence, or
frontend dependency.

## Current dry-run state

AION currently supports governed operator action request records, dry-run
previews, blockers, review records, dry-run action authorization, local role
filtering, local session previews, audit/provenance records, static console
rendering, and platform freeze gates.

The current platform can describe intended effects, blocked effects, review
context, and evidence references. It cannot mutate target systems and cannot
turn a preview or review into an executable command.

## Why write execution is not implemented

Write execution is intentionally not implemented because it would cross
multiple unresolved control boundaries at once: production identity, role
mapping, approval workflow, policy enforcement, connector and target boundary,
sandbox controls, audit/provenance, rollback/undo planning, stale-preview
protection, target drift protection, and release gating.

AION needs the architecture and no-go checks first so future work cannot
accidentally treat dry-run review evidence as permission to execute.

## Future write-path components

Future write-path work must be split into gated components:

- action intent record
- dry-run preview and expected effects
- approval request and approval decision
- policy decision and action authorization
- connector or target boundary
- sandbox or constrained executor boundary
- execution plan with rollback plan
- audit/provenance record
- stale-preview and target-drift check
- release/freeze gate and no-go regression

Every component must fail closed. No component may self-authorize or bypass
policy, approval, audit, rollback, or connector boundaries.

## Action intent lifecycle

The future lifecycle is documented in
`docs/operator-actions/action-intent-lifecycle.md`.

Today the lifecycle stops at previewed, reviewed, or blocked. The
future_execution_ready and future_executed states are not reachable today.

## Approval boundary

Approval is a review control, not an execution trigger. A future approval
decision may mark an intent as approved_for_future_execution only after policy,
authorization, reviewer separation, expiry, revocation, audit, and release-gate
requirements are satisfied.

Approval cannot bypass policy, cannot bypass connector boundaries, cannot
bypass audit/provenance, cannot bypass rollback requirements, and cannot
directly execute an action.

## Execution boundary

Execution is future-only. A future execution boundary must require an approved
intent, current policy decision, dry-run parity, action authorization, target
boundary, rollback plan, audit/provenance, release gate, and operator-visible
evidence.

AION-107 adds no direct tool execution and no model-generated execution.

## Policy boundary

Policy remains authoritative. Future write-path actions must use generic policy
actions, fail closed, and preserve deny-wins behavior. Role filters, local
session previews, connector metadata, model output, and approval records cannot
create policy permissions.

## Connector boundary

External connectors are untrusted and remain disabled for runtime use. Future
write execution must not call a connector unless the connector boundary,
credential boundary, egress guard, ingress guard, action authorization, audit,
and release gates are complete.

## Audit/provenance boundary

Every future write-path transition must produce append-only audit/provenance
evidence. Required references include actor, workspace, intent, preview,
policy decision, authorization decision, approval decision, target boundary,
rollback plan, execution attempt, result, and rollback result when applicable.

Audit evidence must not store raw prompts, hidden reasoning, credentials,
tokens, raw headers, provider payloads, or unredacted secrets.

## Rollback/undo model

Every future executable intent must include an undo feasibility assessment,
rollback plan, compensating action plan when direct undo is unavailable,
irreversible action classification, and confirmation model.

Hard delete is not allowed. Silent rollback is not allowed.

## Operator review model

Operators must be able to review the request, preview, stale-preview status,
target state, approval requirement, policy result, connector boundary, rollback
plan, audit references, and no-go conditions before any later execution phase.

Review records remain record-only in the current system.

## No-go conditions

- write action execution added in AION-107
- tool execution added in AION-107
- model-generated tool execution added in AION-107
- controlled handoff execution added in AION-107
- external calls enabled
- module activation enabled
- capability activation enabled
- connector runtime added
- production auth runtime added
- approval bypass
- policy bypass
- audit bypass
- rollback absent
- hard delete enabled
- current lifecycle reaches future_execution_ready or future_executed
## AION-108 Connector Boundary Relationship

The disabled connector prototype does not add write execution targets. Future
operator write paths still require connector runtime gates, action
authorization, approval, audit/provenance, rollback, and release readiness
before any external target can be considered.
