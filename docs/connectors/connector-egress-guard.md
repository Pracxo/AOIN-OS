# Connector Egress Guard

## Purpose

The connector egress guard defines the controls required before AION can send
anything to an external connector. AION-106 keeps all external calls disabled.

## External Calls Disabled By Default

No connector runtime exists in AION-106. No network client is added. No
external connector call is made. Future connector egress must remain disabled
by default until a later ADR explicitly changes that boundary.

## Egress Preview Before Call

Future connector work must create an egress preview before any call. The preview
must include destination class, connector reference, action name, scope,
payload classification, redaction state, blocked fields, policy decision,
operator approval requirement, rate-limit state, and audit/provenance refs.

## Egress Policy

Every egress attempt must pass policy. Policy failure must deny egress. A
connector cannot self-authorize or convert metadata declarations into active
permissions.

## Allowlist Model

Future egress destinations must be allowlisted by connector reference and
destination class. Raw URLs or unreviewed endpoints must not be accepted from
untrusted connector metadata.

## Rate-Limit Model

Future egress must define per-connector and per-scope rate limits before
runtime calls. Rate-limit exhaustion must fail closed and produce audit
evidence.

## Payload Redaction

Payloads must be redacted before egress. Redaction must block protected values,
raw headers, raw provider payloads, secret-like material, tokens, cookies, and
credentials.

## Raw Prompt Blocking

Raw prompts must not leave through connector egress. Future egress may use
redacted, governed, provider-neutral summaries only after policy and operator
review.

## Hidden Reasoning Blocking

Hidden reasoning and chain-of-thought must never be sent through connector
egress, stored in egress previews, or rendered in operator surfaces.

## Secret Blocking

Secrets, tokens, credentials, cookies, API keys, private keys, and raw
credential references must be blocked before egress.

## Operator Approval Requirements

High-risk or sensitive egress must require operator review. Approval must be
scoped, revocable, audit-backed, and subordinate to policy.

## No-Go Conditions

- external calls enabled by default
- raw prompt egress allowed
- hidden reasoning egress allowed
- secret egress allowed
- unreviewed destination accepted
- rate limits absent
- policy bypass
- operator review bypass
## AION-108 Disabled Prototype Relationship

AION-108 adds a mock egress preview that always returns `egress_allowed=false`
and `external_call_allowed=false`. It is evidence for a future guard, not a
network path.

## AION-109 Review Gate Relationship

AION-109 adds the no-external-call evidence pack and regression script. The
egress guard remains blocked, no network client is added, and no external
endpoint is introduced.
