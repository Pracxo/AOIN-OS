# ADR 0058: Action Proposal Broker and Execution Handoff Gate

## Status

Accepted

## Decision

AION Brain adds an Action Proposal Broker and Execution Handoff Gate.

Model tool intents are not actions. They are captured candidates that may be
reviewed into an `ActionProposal` only through explicit policy-gated review.

Action proposals do not execute themselves. They are metadata records that
describe a proposed action, required permissions, approvals, blockers, risk,
scope, references, and target type.

Execution handoff is explicit and dry-run by default. A handoff record builds a
target request for a governed AION system without dispatching it unless
controlled handoff is explicitly enabled and all gates pass.

Controlled handoff remains disabled by default in v0.1.

## Reason

AION needs a safe conversion path from model, user, operator, decision, and
planner intent into governed execution systems without bypassing policy, risk,
approval, autonomy, runtime configuration, sandbox, capability, audit, and
provenance controls.

## Consequences

Future UI and modules can review, block, approve, and hand off actions through
Brain-owned public contracts. Command Bus, Workflow Engine, Capability Runtime,
MCP Adapter, Cognitive Cycle, and Sandbox remain the governed target systems.

Approved proposals are still not execution. They require a separate handoff API
call, and target systems continue to enforce their own gates.

## Constraints

- No model-generated tool execution.
- No external target systems.
- No automatic proposal execution.
- No automatic approval.
- No controlled handoff unless runtime configuration explicitly enables it.
- No domain-specific action logic.
