# ADR 0053: Explanation Engine and Trace Narratives

## Status

Accepted for AION Brain v0.1.

## Decision

AION Brain adds a deterministic Explanation Engine, Why-Not service, Trace
Narrative Builder, Explanation Verifier, and Explanation Feedback service.

Explanations are public records derived from observable AION contracts. They
include summaries, public steps, references, confidence, grounding status,
constraints, redaction metadata, and feedback. Trace narratives provide an
ordered public timeline for a trace.

## Reasons

AION needs explainability before higher autonomy. Operators and SDK clients
must be able to ask why a result happened, why an action did not continue, and
what public records formed a trace.

## Constraints

- No chain-of-thought or hidden reasoning is exposed.
- No raw prompts, raw headers, provider payloads, or secrets are exposed.
- No external services or model calls are required.
- No domain-specific explanation logic lives in Brain core.
- Public contracts remain independent of database rows and vendor SDKs.

## Consequences

Future UI, SDK, and operator tools can consume stable explanation records,
why-not answers, feedback, and trace narratives. The explanation engine can
later gain optional adapters, but AION public contracts remain the boundary.
