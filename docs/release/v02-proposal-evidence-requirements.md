# v0.2 Proposal Evidence Requirements

## Purpose

AION-126 defines the evidence required before a workstream proposal can be queued for a future decision. Evidence completeness does not approve implementation.

## Problem Statement

Each proposal must explain the problem, affected operator workflow, and why the request belongs in v0.2 planning.

## Risk Statement

Each proposal must state implementation, security, reliability, release, and operator risks.

## Security Impact

Each proposal must describe authentication, authorization, credential, token, external-call, sandbox, and privileged-bypass impact. Missing security impact keeps the proposal unapproved.

## Architecture Impact

Each proposal must describe API, SDK, CLI, runtime registration, code loading, data model, and static console impact. Missing architecture impact keeps the proposal unapproved.

## Policy Impact

Each proposal must describe policy checks, approval gates, role boundaries, dual-control needs, expiry behavior, and revocation behavior.

## Audit/Provenance Impact

Each proposal must describe audit events, provenance records, evidence retention, and traceability.

## Rollback Plan

Each proposal must define rollback, recovery, compensation, and operator verification steps before implementation can be considered.

## ADR Dependency

Each proposal must cite a future ADR dependency. ADR dependency bypass is a no-go condition.

## Gate Dependency

Each proposal must cite a future gate dependency. Gate dependency bypass is a no-go condition.

## Test Evidence

Each proposal must define focused tests, no-go regression tests, full-check expectations, and static evidence validation.

## No-Go Acknowledgement

Each proposal must acknowledge that implementation approval, workstream implementation approval, approval queue item approval, approval workflow bypass, missing approval records, ADR dependency bypass, gate dependency bypass, v0.2 tag creation, v0.2 release creation, runtime enablement, external calls, credential or token storage, sandbox execution, package files, migrations, and runtime API execution routes are blocked until a later scoped approval task.

## AION-127 Stabilized Evidence Baseline

AION-127 requires candidate workstream evidence, lifecycle evidence, queue
freeze evidence, expiry evidence, revocation evidence, dual-control evidence,
and closeout evidence before any later approval discussion. Proposal
implementation approval, approval queue item approval, runtime implementation
approval, workstream implementation approval, v0.2 tag creation, and v0.2
release creation remain false.
