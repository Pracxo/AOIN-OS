# Connector Trust Model

## Purpose

This trust model treats every external connector as an untrusted integration
boundary until AION validates, normalizes, redacts, policy-gates, and tags its
data.

## Trust Rules

- connectors are untrusted by default
- metadata is untrusted
- returned data is untrusted
- connector capability claims are untrusted until validated
- connector credentials must be isolated
- connector calls must be policy-gated
- connector outputs must be redacted
- connector results must be provenance-tagged

## Metadata Trust

Connector manifests may describe capabilities, scopes, egress patterns, ingress
patterns, credential needs, rate limits, audit tags, and sandbox requirements.
Those fields are declarations only. They are not permissions and do not enable
runtime behavior.

## Result Trust

Future connector results must be treated as claims from an external source.
They need source classification, freshness labels, provenance references,
redaction state, prompt-injection scan state, and operator-visible uncertainty.

## Credential Trust

Credentials are never trusted as data records inside Brain state. Future
credentials must live outside AION Brain and be referenced by metadata-only
secret refs with rotation, revocation, and audit controls.

## Policy Trust

Connector manifests cannot grant their own permissions. Every future connector
operation must pass policy and action authorization before any egress,
ingress promotion, or controlled behavior.

## Output Trust

Connector outputs must be normalized, redacted, and provenance-tagged before
they enter Brain records. Raw responses, raw headers, provider payloads,
secrets, tokens, raw prompts, and hidden reasoning must not be persisted.
## AION-108 Disabled Prototype Relationship

The disabled connector prototype treats every mock connector declaration and
ingress preview as untrusted. A valid mock manifest is preview evidence only;
it does not become trusted runtime state, policy authority, or an activation
record.

## AION-109 Review Gate Relationship

AION-109 keeps connector trust frozen at untrusted by default. Future connector
work must satisfy the traceability matrix, ingress redaction proof,
provenance proof, and operator review before any trust elevation is considered.

## AION-110 Simulator Relationship

Synthetic simulator responses remain untrusted. A replay fixture or dry-run
result is evidence about shape readiness only; it is not external data, not
trusted connector output, not policy authority, and not runtime approval.
