# v0.2 Backlog Intake Criteria

## Purpose

This document defines the planning-only intake format for v0.2 backlog items.
It does not approve implementation.

## Planning-Only Intake Format

Each backlog candidate must include:

- title
- owner
- workstream
- problem statement
- risk statement
- ADR dependency
- gate dependency
- no-go statement
- rollback/audit consideration
- security review requirement
- current approval state
- implementation approval boundary

## Required Problem Statement

The problem statement must describe the operator or platform capability gap
without proposing runtime code, dependencies, API routes, migrations, or
external calls.

## Required Risk Statement

The risk statement must name safety, security, rollback, audit/provenance,
operator review, policy enforcement, and release-blocking risks.

## Required ADR Dependency

Every backlog item must identify the future ADR required before
implementation.

## Required Gate Dependency

Every backlog item must identify required prior gates and the new gate that
would be required before implementation.

## Required No-Go Statement

Every backlog item must state that implementation approval remains false until
the ADR and gates pass.

## Required Rollback/Audit Consideration

Every backlog item must describe how rollback, disablement, audit records, and
provenance would be planned before runtime approval.

## Required Security Review

Every backlog item must require a future security review before implementation,
especially for auth, credentials, tokens, external calls, sandbox execution,
operator writes, and module activation.

## Required Owner

Every backlog item must name an accountable owner for planning evidence and
future gate closure.

## Rejection Conditions

Reject backlog items that approve implementation, create a v0.2 tag or release,
enable runtime behavior, add package or migration drift, add runtime API
execution routes, store protected material, call external services, omit ADR or
gate dependencies, omit rollback/audit considerations, omit security review, or
lack an owner.
