# ADR 0055: Grounding Citation Source Attribution

## Decision

AION Brain adds a Grounding Manager, Citation Mapper, and Source Attribution
Control Plane. They produce `GroundingSource`, `CitationRecord`,
`ResponseCitationMap`, `UnsupportedStatement`, `GroundingVerificationRun`, and
`SourceCoverageReport` records from local AION contracts.

Memory recall is weak support unless backed by evidence or a supported belief.
Citation mapping is deterministic in v0.1. This layer does not use LLM
citation extraction and does not call web search.

## Reason

AION needs response-level source attribution before broader dialogue and
decision use. Response, Explanation, Dialogue, and Operator surfaces need
grounded support without treating memory as truth.

## Consequences

Responses and explanations can expose citation maps, unsupported statements,
source coverage, and verification status. Operator views can surface failed
grounding and low source coverage.

## Constraints

- No invented citations.
- No hidden reasoning.
- No raw prompts.
- No external search.
- No LLM citation extraction.
- No domain-specific citation rules.
