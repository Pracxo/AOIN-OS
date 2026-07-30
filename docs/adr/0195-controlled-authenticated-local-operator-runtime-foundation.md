# ADR 0195: Controlled Authenticated Local Operator Runtime Foundation

Status: Accepted
Task: `AION-231`
Program: `AION-SECURE-RUNTIME-INTEGRATION-001`
Authorization: `AION-230-SRI-0001`

## Context

AION-230 authorized one local secure-runtime foundation for AION-231 after the Cognitive Architecture, Knowledge Intelligence, Governed Learning and Memory, and governed self-improvement programs completed.

## Decision

Implement a controlled authenticated local operator runtime foundation that composes existing offline Ed25519 assertion verification, local trusted public-key registry lookup, replay protection, request identity, ActorContext, policy, risk, guardrails, approval evidence, side-effect budgets, kill-switch state, audit, observability, health, checkpoints and integrity evidence.

Capability dispatch remains simulation-only and is limited to the closed AION-231 registry.

## Consequences

AION OS can validate a bounded local operator session and produce redacted simulation evidence. It does not create a public auth endpoint, credential store, token store, model gateway, connector runtime, tool runtime, module loader, production write path, deployment path, v0.2 tag or v0.2 release. `AION-230-SRI-0001` remains active pending AION-232 evaluation and closeout.
