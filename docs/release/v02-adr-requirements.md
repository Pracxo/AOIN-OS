# v0.2 ADR Requirements

## Purpose

This document defines the ADRs required before any v0.2 implementation work
can begin. AION-119 records requirements only and does not approve
implementation.

## Required ADRs Before Implementation

- production auth implementation ADR
- connector runtime implementation ADR
- credential store implementation ADR
- sandbox runtime implementation ADR
- operator write execution ADR
- module activation ADR
- external calls release ADR
- rollback/audit ADR
- production UI decision ADR

## Required ADR Content

Each ADR must include:

- current approval state
- proposed approval state change
- allowed behavior
- denied behavior
- required prior gates
- required new gates
- required evidence
- rollback model
- audit/provenance model
- operator review model
- policy enforcement model
- security review summary
- no-go regression criteria

## ADR Rejection Conditions

An ADR remains rejected if it enables runtime behavior without scoped gates,
omits rollback or audit/provenance, omits operator review, weakens policy
enforcement, permits external calls without a release gate, permits protected
material storage without lifecycle controls, permits sandbox execution without
isolation evidence, or creates a v0.2 tag or release before release approval.

## Current State

All v0.2 implementation ADRs are required in the future and none is approved by
AION-119.

## AION-120 ADR Stabilization Requirement

AION-120 adds ADR 0111 for the planning stabilization gate. Future
implementation ADRs must reference the stabilization gate, backlog governance
freeze, blocked work register, readiness scorecard, security review,
rollback/audit requirements, operator review, and no-go regression evidence
before any approval field can change.
