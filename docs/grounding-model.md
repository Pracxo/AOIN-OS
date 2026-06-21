# Grounding Manager and Source Attribution

AION Brain v0.1 grounding is deterministic. It maps public response and
explanation statements to local AION source records, citations, unsupported
statements, verification runs, and source coverage reports.

Grounding validates support. It does not create truth. Evidence Vault owns
primary evidence, Belief State owns claim status, Memory owns recall,
Retrieval Router selects context, Response Composer writes drafts, and
Grounding Manager maps statements to sources.

Memory recall is weak support unless backed by evidence or supported belief.
Contradicted belief claims cannot strongly ground a response. Citation mapping
does not invent evidence references, call web search, call model providers, or
extract citations with an LLM.

## Contracts

- `GroundingSource`
- `GroundingSourceCreateRequest`
- `CitationRecord`
- `CitationCreateRequest`
- `UnsupportedStatement`
- `ResponseCitationMap`
- `GroundingVerificationRequest`
- `GroundingVerificationRun`
- `SourceCoverageReport`
- `GroundingQuery`
- `GroundingQueryResult`

## Rules

- Do not invent citations.
- Do not treat memory recall as primary evidence.
- Do not expose hidden reasoning, chain-of-thought, raw prompts, raw headers,
  provider payloads, or secrets.
- Keep citation rules generic and deterministic.
- Keep source attribution separate from evidence, memory, and belief ownership.

## Endpoints

- `POST /brain/grounding/sources`
- `GET /brain/grounding/sources/{grounding_source_id}`
- `POST /brain/grounding/citations`
- `GET /brain/grounding/citations`
- `POST /brain/grounding/map-response/{response_id}`
- `POST /brain/grounding/map-text`
- `POST /brain/grounding/verify`
- `GET /brain/grounding/verifications/{grounding_verification_id}`
- `POST /brain/grounding/coverage`
- `POST /brain/grounding/query`
- `GET /brain/grounding/unsupported`
