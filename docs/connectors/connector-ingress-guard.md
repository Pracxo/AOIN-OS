# Connector Ingress Guard

## Purpose

The connector ingress guard defines how future external connector responses
must be treated before AION can trust or store them. AION-106 adds no connector
runtime and accepts no live connector responses.

## Connector Responses Are Untrusted

Every future connector response is untrusted by default. Response content,
headers, status, source labels, timestamps, capability claims, and errors must
be normalized and validated before use.

## Response Normalization

Future ingress must normalize responses into AION-owned contracts or plain JSON
derived from them. It must not expose provider SDK objects, raw HTTP client
objects, framework objects, raw headers, or vendor payloads.

## Secret Scanning

Ingress must scan for secret-like material before storage or rendering.
Detected secrets must be redacted and routed to audit without exposing values.

## Prompt Injection Scanning

Ingress must scan connector responses for prompt injection and instruction
override attempts. Suspicious content must be labeled and routed to operator
review.

## Provenance Tagging

Ingress must tag connector reference, source class, retrieval time, normalization
hash, redaction hash, policy decision, and operator review state.

## Source Classification

Future connector data must classify source trust, source type, connector
identity, expected freshness, and scope. Unknown source classification fails
closed.

## Stale Data Flags

Future ingress must label stale or freshness-unknown data. Stale data must not
silently become authoritative.

## Operator Review

Operators must be able to review risky connector responses, stale data,
redaction findings, prompt-injection findings, and policy denials before the
data is promoted.

## No-Go Conditions

- connector response trusted by default
- raw response persisted
- raw headers persisted
- provider payload exposed
- secret scanning bypassed
- prompt-injection scanning bypassed
- provenance missing
- stale data trusted as current
- operator review bypassed
## AION-108 Disabled Prototype Relationship

AION-108 adds a mock ingress preview that always marks connector data
`trusted=false`, requires provenance, applies redaction, and requires prompt
injection scanning before future review.

## AION-109 Review Gate Relationship

AION-109 adds egress/ingress traceability evidence. Ingress remains untrusted,
redacted, provenance-bound, and preview-only until a future implementation gate
approves a stronger ingress design.

## AION-110 Simulator Relationship

Synthetic replay responses are ingress-shape evidence only. They remain
`trusted=false`, are redacted when unsafe material is detected, and cannot be
promoted into trusted connector data.
