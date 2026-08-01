# ADR 0201: Controlled Same-Origin Loopback Operator Console and Integrated Local Runtime

Status: Accepted for AION-237 implementation pending AION-238 final evaluation.

## Decision

Implement the AION-236-authorized Operator Console integration as a local-only same-origin bridge bound to numeric IPv4 loopback. The bridge serves only the five injected static assets and ten authorized `/aion/local/v1/` routes. State-changing routes require exact Host, Origin, JSON content type, explicit operator confirmation and current mutation nonce checks.

## Consequences

AION OS now has a working local human-control plane for pre-authenticated operators. The runtime remains local, deterministic and redacted. Model output is untrusted, connector operations are synthetic, write operations are preview-only and every prohibited external or production effect remains disabled. AION-236-SRI-0004 remains active until AION-238 closes the program and v0.2 remains unreleased.
