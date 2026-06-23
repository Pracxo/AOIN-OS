# ADR 0080: Static Local Operator Console Prototype

## Status

Accepted.

## Context

AION-087 defined the Operator Console strategy as CLI/API-first. AION-088 added
read-only view-model contracts. AION now needs a local operator experience
preview that proves layout and redaction behavior before real UI investment.

## Decision

Create a static local Operator Console prototype.

Use no frontend framework or build system.

Keep the prototype read-only and local.

Consume existing view-model APIs when available or local demo JSON when the API
is unavailable.

Do not add write actions, activation, or external calls.

## Reason

AION needs operator experience validation before real UI investment. A static
prototype can exercise the existing view-model shape, unavailable-state
behavior, redaction list, and local API guard without introducing production UI
risk.

## Consequences

Future UI can reuse view-model contracts and safety rules.

The static prototype cannot claim production auth, production readiness, or
privileged control behavior.

The static console remains replaceable because it owns no backend contracts and
adds no runtime state.

## Constraints

- no frontend dependencies
- no production auth claim
- no privileged bypass
- no raw prompt, hidden reasoning, or secret exposure
- no module or capability activation
- no provider enablement
- no runtime config mutation
- no external network calls
