# v0.2 Implementation Kickoff Boundary

## Purpose

AION-122 defines the boundary for future v0.2 implementation requests after
the AION-121 readiness final review. It explains how runtime work may be
requested, reviewed, sequenced, approved, or blocked in later tasks.

## Scope

In scope:

- implementation request boundaries
- approval workflow requirements
- ADR dependency requirements
- gate evidence requirements
- runtime workstream locks
- no-go conditions for future work
- static read-only console evidence

Out of scope:

- v0.2 implementation
- v0.2 tag creation
- v0.2 release creation
- runtime approval changes
- connector runtime enablement
- operator write execution
- production auth runtime
- module activation
- external calls
- credential or token storage
- sandbox execution
- package files, lockfiles, migrations, API runtime routes, SDK resources, or
  CLI command implementations

## Current Readiness State

AION-119 created the v0.2 planning charter. AION-120 stabilized planning and
backlog governance. AION-121 completed the final readiness review. AION-122
adds the kickoff boundary for future implementation requests, but the current
state remains planning-only and unapproved.

## Implementation Remains Unapproved

Implementation remains unapproved after AION-122. The approval workflow
described here is a future control process, not an approval decision.

Required safe values:

- `runtime_implementation_approved=false`
- `backlog_implementation_items_approved=false`
- `operator_write_execution_approved=false`
- `connector_implementation_approved=false`
- `production_auth_approved=false`
- `module_activation_approved=false`
- `external_calls_approved=false`
- `credential_storage_approved=false`
- `token_storage_approved=false`
- `sandbox_execution_approved=false`

## Required Approval Workflow

Each future implementation request must include a requester, reviewer,
approver, security reviewer, architecture reviewer, operator reviewer, evidence
links, expiry, revocation path, and explicit no-go acknowledgement. Approval
does not execute work and does not enable runtime by itself.

## Required ADR Workflow

Each implementation workstream requires a scoped ADR before code changes. The
ADR must name the requested runtime capability, blocked behavior, safety
evidence, rollback plan, audit/provenance evidence, operator review impact, and
the gates that must pass before implementation can start.

## Required Gate Evidence

Future implementation requests must provide gate evidence from the scoped
workstream gate, no-go regression, docs audit, boundary check, and full
repository check. Evidence must remain local, synthetic where applicable, and
free of secrets, tokens, endpoints, raw prompts, and hidden reasoning.

## Blocked Runtime Areas

These runtime areas remain blocked:

- production auth implementation
- connector runtime implementation
- credential store implementation
- sandbox runtime implementation
- operator write execution
- module activation
- external calls
- runtime route registration
- package dependency additions
- migrations
- production UI implementation

## Kickoff Criteria

A future task may request implementation kickoff only when it includes:

- a single named workstream
- a scoped ADR dependency
- a scoped gate dependency
- security evidence
- rollback evidence
- audit/provenance evidence
- operator review evidence
- explicit no-go acknowledgement
- default approval status set to false

## No-Go Conditions

The request is blocked if it creates a v0.2 tag, creates a release, sets any
implementation approval true, bypasses approval workflow, bypasses ADR
dependency, bypasses gate dependency, enables runtime behavior, adds package
files, adds migrations, adds runtime API routes, stores credentials or tokens,
or introduces external calls.

## No v0.2 Tag Or Release

AION-122 explicitly creates no v0.2 tag and no release. It does not mutate,
move, delete, or recreate `aion-v0.1.0`.
