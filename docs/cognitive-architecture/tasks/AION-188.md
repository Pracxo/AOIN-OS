# AION-188 Global Cognitive Workspace

## Task Purpose

AION-188 implements the global cognitive workspace core authorized by
AION-187-CA-0003. The work adds immutable contracts and pure local services for
specialist bids, salience scoring, bounded attention selection, workspace
broadcast, specialist response records, cycle state, snapshots, and sanitized
audit events.

## Authorization

- Authorization ID: AION-187-CA-0003
- Program ID: AION-COGNITIVE-ARCHITECTURE-001
- Candidate ID: global-cognitive-workspace-core
- Scope: global-cognitive-workspace-attention-salience-broadcast-core
- Workstream: global-cognitive-workspace
- Formal closeout task: AION-189

## Source Boundaries

Allowed source paths are limited to the workspace contracts, the
`aion_brain.workspace` package, focused tests, examples, documentation, and
governance scripts named by AION-187-CA-0003.

The task does not add API routes, kernel runtime registration, migrations,
workflow files, package files, connector code, deployment code, credential
handling, provider calls, network calls, model calls by default, source rewrite
operations, or direct action execution.

## Required Contracts

- WorkspaceItem
- SpecialistBid
- SalienceVector
- AttentionDecision
- WorkspaceBroadcast
- SpecialistResponse
- CognitiveCycleState
- WorkspaceSnapshot
- WorkspaceAuditEvent

## Required Services

- CognitiveSpecialist protocol
- AttentionArbiter
- WorkspaceCapacityController
- WorkspaceBroadcastService
- AntiStarvationController
- CognitiveCycleCoordinator

## Algorithm

Specialists submit immutable bids with bounded salience vectors. The attention
arbiter deduplicates by item ID, ranks critical safety bids ahead of ordinary
bids, applies deterministic salience ordering with stable tie breaking, and
selects only the bids that fit the configured item and capacity-unit limits.

The anti-starvation controller adds a deterministic boost for specialists whose
ordinary bids have been deferred across cycles. Broadcast records include only
selected workspace items and approved specialist IDs. The coordinator invokes
only in-process specialists explicitly supplied by the caller and returns
sanitized cycle, snapshot, response, and audit records.

## Required Tests

Focused tests cover immutable contracts, fingerprint stability, bounded salience
dimensions, duplicate-bid rejection, deterministic tie breaking, critical safety
preemption, capacity limits, anti-starvation boost, approved-specialist
broadcast, cycle provenance, runtime-boundary validation, import safety, and
script gates.

## Required Gates

- `scripts/cognitive-global-workspace-check.sh`
- `scripts/cognitive-global-workspace-no-go-regression.sh`
- focused Brain API pytest for global workspace tests
- inherited documentation, domain, boundary, and repository hygiene checks
  outside nested gate contexts

## Security Invariants

- Production cognitive runtime remains disabled.
- Runtime action execution remains disabled.
- Network, connector, and model-provider calls remain zero.
- Model calls by default remain zero.
- API route and kernel registration are absent.
- Package files, migrations, and workflow files are unchanged.
- `aion-v0.1.0` remains untouched.
- No v0.2 tag or release is created.
- No affect, persona, survival-score, raw prompt, hidden reasoning, credential,
  or unredacted personal-data fields are introduced.

## Completion Conditions

AION-188 is complete when the implementation is merged, focused gates pass, CI
passes, the branch is cleaned up, and the program remains in
`global_workspace_implemented_pending_evaluation` for AION-189.

## Next Task

AION-189 evaluates the global workspace under AION-GWE-001, closes
AION-187-CA-0003 on PASS, and may authorize AION-190 for memory consolidation.
