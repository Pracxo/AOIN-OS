# ADR 0197: Controlled Provider-Neutral Model Gateway and Deterministic Reference Provider

## Status

Accepted for AION-233 implementation pending AION-234 formal closeout.

## Context

AION-232 authorized a bounded model-gateway implementation after the AION-231
authenticated local secure-runtime foundation passed operator evaluation. The
gateway must compose the secure runtime without creating a live provider
integration, credentials, network egress, production runtime, tool execution,
connector execution, prompt persistence, response persistence, memory writes,
belief changes, deployment, or model training.

## Decision

AION OS implements a provider-neutral model-gateway control plane with exactly
one local deterministic simulation provider:
`deterministic-reference-provider`. The only model identifiers are
`reference-text-sim-v1` and `reference-json-sim-v1`.

The gateway binds to AION-231 through `brain.think.simulate`, parent guard
outcome `allow_simulation`, and parent dispatch status `simulated`. It validates
immutable provider and model manifests, closed allowlists, bounded request
envelopes, message and context normalization, protected-material rejection,
redaction, context and token budgets, deterministic fingerprints, exact replay,
changed-replay rejection, route planning, fallback planning, retry planning,
circuit-breaker state, cost and latency estimates, structured-output schemas,
response validation, untrusted-output classification, provenance, audit,
observability, health, integrity, diagnostics, and operator-review evidence.

## Consequences

The gateway can simulate text and structured JSON responses for local evidence
only. A deterministic reference-provider output remains untrusted and cannot
become fact, approval, memory, belief, policy, action, deployment decision, or
successor authorization.

AION-232-SRI-0002 remains active and non-reusable until AION-234 independently
evaluates AION-233 and closes the authorization. AION-235 remains unauthorized
and v0.2 remains unreleased.
