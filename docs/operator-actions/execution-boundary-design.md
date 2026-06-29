# Operator Action Execution Boundary Design

## Purpose

AION-107 defines the future execution boundary without implementing execution.
Execution is future-only and is unreachable in the current operator action
platform.

## Execution is future-only

Execution is future-only. AION-107 adds no execution service, no write API, no
tool runner, no connector runtime, no queue consumer, no worker, no SDK command,
no CLI command, no frontend control, and no migration.

## Execution requires approved intent

Future execution requires an approved action intent. The intent must reference
a current dry-run preview, non-expired approval, target boundary, and rollback
plan.

## Execution requires policy decision

Future execution requires a current policy decision. A stale policy decision or
unavailable policy adapter must fail closed.

## Execution requires action authorization

Future execution requires action authorization. Role filtering and local
session previews cannot self-authorize execution.

## Execution requires connector/target boundary

Future execution requires a connector or target boundary that identifies the
target class, target identity, egress posture, ingress posture, credential
reference posture, stale-state protection, and target drift controls.

## Execution requires rollback plan

Future execution requires a rollback plan or an irreversible action
classification with explicit confirmation and compensating action design.

## Execution requires audit/provenance

Future execution requires append-only audit/provenance before, during, and
after the attempt. Missing audit evidence is a no-go condition.

## Execution requires release gate

Future execution requires a green release/freeze gate, threat model approval,
rollback test evidence, policy enforcement test evidence, audit/provenance test
evidence, dry-run parity evidence, and no-go regression pass.

## No direct tool execution

AION-107 adds no direct tool execution. Future tool execution must not be
reachable from model output, preview records, review records, or approval
records without a later explicit implementation gate.

## No model-generated execution

Model-generated execution is not allowed. Future model output may propose an
intent for review, but it cannot execute, call tools, call connectors, mutate
targets, or bypass approval and policy.
