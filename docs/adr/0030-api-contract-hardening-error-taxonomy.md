# ADR 0030: API Contract Hardening and Error Taxonomy

## Status

Accepted.

## Decision

AION Brain adds a standard API error taxonomy and `AIONErrorResponse` for
public errors.

AION Brain adds request context middleware that creates request IDs, propagates
trace IDs and correlation IDs, extracts idempotency keys, and sets standard
response headers.

AION Brain preserves existing success responses where changing them would
break compatibility.

AION Brain adds request audit records without storing request bodies or raw
headers.

AION Brain adds OpenAPI hygiene checks for route metadata, schema safety, and
domain-neutral API boundaries.

## Reason

AION needs a stable API surface before SDK generation and external modules.
Clients must receive predictable errors and traceable request metadata without
seeing adapter internals.

## Consequences

Future routes must return AION contracts or `AIONErrorResponse`.

API support can evolve without forcing old successful response contracts into a
new envelope.

Request audit can support debugging and trace correlation without becoming a
secret store.

## Constraints

Public responses must not expose stack traces or secrets.

Public responses must not expose raw exceptions, provider SDK objects,
SQLAlchemy rows, raw SQL, raw headers, or adapter internals.

API contracts must stay domain-neutral and must not introduce vertical
business logic.
