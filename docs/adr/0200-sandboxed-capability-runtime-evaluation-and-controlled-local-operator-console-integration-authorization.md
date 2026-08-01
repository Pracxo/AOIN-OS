# ADR 0200: Sandboxed Capability-Runtime Evaluation and Controlled Local Operator-Console Integration Authorization

## Status
Accepted for AION-236 closeout and AION-237 authorization.

## Context
AION-235 implemented the sandboxed deterministic capability runtime under AION-234-SRI-0003. AION-236 evaluated that implementation through AION-SRIPE-003.

## Decision
AION-SRIPE-003 passed all 28 hard-gated scenarios. Close AION-234-SRI-0003 as consumed by AION-235 and create AION-236-SRI-0004 as the sole active Secure Runtime Integration implementation authorization for AION-237.

AION-237 may implement only a controlled local Operator Console bridge using loopback, same-origin validation, exact routes, ephemeral mutation nonces, redacted projections, explicit operator confirmations and zero external or production effects.

## Consequences
AION-236 creates no AION-237 runtime source. AION-238 remains the final formal evaluation and v0.2 remains unreleased.
