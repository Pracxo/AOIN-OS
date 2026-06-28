# 0090: Disabled Production Auth Prototype

## Status

Accepted

## Context

AION-098 selected a future production auth architecture but intentionally added
no production auth implementation. AION-099 needs an operator-visible contract
surface to inspect disabled runtime posture and mock claims mapping without
crossing that boundary.

## Decision

Add a disabled auth runtime prototype with status, mock-claims preview, and
audit contracts. The runtime is disabled by default and exposes no login,
logout, callback, token, session, provider, or production identity flow.

The mock claims preview maps synthetic local claims to an actor context preview
through the existing local role matrix. It never authenticates a subject, never
issues credentials, tokens, or cookies, and never persists session state.

## Consequences

Operators can review production auth runtime shape before implementation, while
the codebase still enforces that production auth remains disabled.

Future production auth work must be a separate gated milestone.
