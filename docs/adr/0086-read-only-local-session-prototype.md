# 0086: Read-Only Local Session Prototype

## Status

Accepted.

## Decision

AION-095 adds a read-only local session prototype for the Operator Console.
Local sessions are dev-only previews. They do not authenticate real users and
are not production authentication.

The prototype does not store credentials, passwords, bearer material, browser
state, or persistent session state. It does not add login or logout routes. It
does not issue tokens or cookies. It does not add production session tables.

Local session context may carry synthetic local identity and role information
for read-only console filtering. It cannot grant writes, execution, activation,
provider enablement, external calls, code loading, runtime registration, hard
delete, or controlled handoffs.

## Reason

Future console authentication needs explicit session semantics before real auth
implementation. Capturing those semantics now makes the no-go conditions
visible in contracts, policy, telemetry, SDK/CLI, static console data, and
operator documentation.

## Consequences

Later auth work can build from explicit local session boundaries. Any future
credential storage, token issuance, cookie handling, external identity provider,
browser session, or persistent production session work requires a separate ADR,
policy review, migration decision, and security review.

The AION v0.1.0 release baseline remains untouched.
