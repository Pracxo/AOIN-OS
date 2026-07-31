# ADR 0196: Secure Runtime Foundation Evaluation And Controlled Model-Gateway Authorization

Status: Accepted

## Context

AION-231 implemented the controlled authenticated local operator runtime foundation under `AION-230-SRI-0001`. AION-232 evaluated that implementation through `AION-SRIPE-001` and all 28 deterministic hard-gated scenarios passed.

## Decision

Close `AION-230-SRI-0001` as consumed by AION-231. Create `AION-232-SRI-0002` as the sole active Secure Runtime Integration implementation authorization for AION-233. AION-233 may implement a controlled provider-neutral model gateway, but it may not call a live model provider, access a network, read or persist provider credentials, execute connectors or tools, write memory, mutate policy, create beliefs, rewrite source, deploy, or train model weights.

## Consequences

AION-233 is authorized but not implemented. AION-234 is the next formal evaluation. v0.2 remains unreleased.
