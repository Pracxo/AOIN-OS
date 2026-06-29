# Operator Action Approval Boundary Design

## Purpose

AION-107 defines approval as a future write-path control without making
approval executable. Approval records can support governance, but they do not
execute, activate, call tools, call external systems, or bypass policy.

## Approval request

A future approval request must reference an action intent, dry-run preview,
scope, target boundary, policy decision, action authorization result, rollback
plan, requester, reviewer constraints, expiry, and audit/provenance references.

The current system can record review context only. It does not create an
executable approval request.

## Approval decision

A future approval decision may allow, deny, request changes, revoke, or expire
an approval. The decision must be append-only and must preserve actor,
workspace, role, policy input, policy output, review evidence, and rationale.

Approval decisions in the current system are review evidence only.

## Reviewer separation

The requester and reviewer must be different human-control roles for any future
write path. Reviewer separation prevents a requester from approving their own
intent.

## Dual-control option

High-risk future actions may require dual control. Dual control means two
eligible approvers, independent decisions, explicit scope match, and a shared
expiry window before any future execution gate can proceed.

## Expiry

Approvals must expire. A future execution attempt after expiry must fail
closed and require a fresh preview, policy decision, and approval decision.

## Revocation

Approvals must be revocable before future execution. Revocation must be
audited and must block subsequent execution readiness.

## Approval does not execute

Approval does not execute. Approval cannot run tools, call connectors, mutate
targets, dispatch notifications, invoke capabilities, register modules, load
code, or start a controlled handoff.

## Approval cannot bypass policy

Approval cannot bypass policy. A future execution attempt must obtain a current
allow decision from policy and action authorization even when a prior approval
exists.

## Approval audit record

An approval audit record must include requester, reviewer, approver, workspace,
intent reference, preview reference, policy decision, authorization decision,
expiry, revocation state, no-go checks, and redacted provenance references.

## No-go conditions

- approval directly executes an action
- approval bypasses policy
- approval bypasses action authorization
- requester approves their own high-risk action
- approval lacks expiry
- revoked approval remains executable
- approval lacks audit/provenance
- approval hides stale preview or target drift
