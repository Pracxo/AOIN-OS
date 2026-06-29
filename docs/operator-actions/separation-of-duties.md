# Operator Action Separation Of Duties

## Purpose

AION-107 defines future separation of duties for the operator write path. The
current platform remains request, preview, and review only.

## Roles

| Role | Responsibility | Boundary |
| --- | --- | --- |
| requester | Drafts or requests an intent and reviews dry-run evidence. | cannot approve own high-risk intent |
| reviewer | Reviews preview, blockers, target drift, and rollback plan. | cannot execute |
| approver | Approves or denies future execution readiness. | approval does not execute |
| executor | Future system service that may attempt controlled execution after all gates. | absent today |
| auditor | Reads audit/provenance and verifies controls. | cannot execute or approve by reading |
| system service | Future constrained service that records transitions and enforces gates. | absent today |

## Role conflicts

Future policy must reject conflicting duties. A requester cannot approve their
own high-risk action. A reviewer cannot bypass an approver. An executor cannot
self-authorize. An auditor cannot turn read access into execution access.

## Dual control

Dual control is required for future high-risk and irreversible actions. It
requires two eligible approvers, independent approvals, matching scope, active
expiry windows, and complete audit/provenance.

## Break-glass future design

Break-glass is future design only. If introduced later, it must be disabled by
default, time-bound, audited, dual-controlled when possible, release-gated,
reviewed after use, and unable to bypass immutable no-go conditions such as
policy absence, audit absence, or rollback absence.

## No-go conditions

- requester approves own high-risk action
- reviewer executes an action
- executor self-authorizes
- auditor privileges mutate target systems
- break-glass bypasses policy, audit, rollback, or release gate
