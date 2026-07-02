# v0.2 Workstream Sequencing Plan

## Purpose

This plan records candidate sequencing for future v0.2 implementation planning.
It does not approve any implementation workstream.

## Candidate Sequence

1. Production auth implementation planning
   - Status: implementation-unapproved.
2. Audit/provenance hardening
   - Status: implementation-unapproved.
3. Rollback/recovery design
   - Status: implementation-unapproved.
4. External call release gate design
   - Status: implementation-unapproved.
5. Connector runtime implementation planning
   - Status: implementation-unapproved.
6. Credential store implementation planning
   - Status: implementation-unapproved.
7. Sandbox runtime implementation planning
   - Status: implementation-unapproved.
8. Operator write execution planning
   - Status: implementation-unapproved.
9. Module activation planning
   - Status: implementation-unapproved.
10. Production UI decision
    - Status: implementation-unapproved.

## Sequencing Constraints

No workstream can move from planning to implementation until it has a scoped
ADR, approval decision record, gate evidence, security review, architecture
review, operator review, rollback evidence, and no-go regression.

## AION-123 Sequencing Stabilization

AION-123 adds intake validation, approval decision evidence, expiry and
revocation evidence, and dual-control review to the sequencing requirements.
Workstreams remain `implementation-unapproved` until those checks pass in a
future scoped implementation task.

## AION-124 Sequencing Freeze

AION-124 freezes sequencing as planning-only. Production auth remains the first
candidate planning dependency, audit/provenance hardening and rollback/recovery
remain planning-only, connector runtime remains locked, credential store
remains locked, sandbox runtime remains locked, operator write execution
remains locked, module activation remains locked, and production UI remains
undecided.
