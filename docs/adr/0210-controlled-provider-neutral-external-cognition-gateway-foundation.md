# 0210: Controlled Provider-Neutral External-Cognition Gateway Foundation

## Status

Accepted for AION-246.

## Context

AION-245 authorized a provider-neutral external-cognition gateway foundation for the AION Adaptive Intelligence Programme. The authorization allows deterministic contracts, manifests, envelopes, budgets, routing, trust, redaction, replay, audit, observability, integrity and fixture evidence only.

## Decision

AION-246 implements the external-cognition layer as a governed control and evidence plane that composes the existing secure runtime and `ControlledModelGatewayService`. The implementation remains deterministic fixture only and disabled for live providers.

## Consequences

The gateway exposes machine-verifiable contracts and redacted evidence for AION-247 evaluation. It does not authorize live provider calls, network egress, DNS, credential or token access, persistent prompt or response storage, memory writes, tool execution, autonomous loops, deployment, source mutation or model-weight changes.
