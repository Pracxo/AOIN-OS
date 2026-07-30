# Secure Runtime Identity Composition

AION-231 may compose already implemented disabled or offline identity surfaces,
but it may not expose a production authentication endpoint or contact an
external identity provider.

## Required Order

1. Receive an explicit local operator invocation envelope.
2. Verify an offline Ed25519 identity assertion through public-key-only
   registry reads.
3. Project request identity context.
4. Bind ActorContext from verified request identity evidence.
5. Validate replay protection before session activation.
6. Correlate request trace and audit identifiers.

Identity verification precedes ActorContext construction. ActorContext must not
trust caller-controlled headers, cookies, tokens, or raw request state.

## Disabled Effects

Password authentication, credential persistence, token persistence, session
token issuance, refresh tokens, public-key network retrieval, external identity
provider calls, and production authentication remain disabled.
