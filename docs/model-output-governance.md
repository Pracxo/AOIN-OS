# Model Output Governance

AION Model Output Governance receives provider-neutral model outputs, stores a
hash of the raw output, persists redacted output, parses generic output
segments, validates structured JSON, creates local response candidates, and
captures tool intents for review.

The layer is deterministic in v0.1. It does not call model providers, execute
tools, deliver messages, or add domain-specific rules.

## Contracts

- `ModelOutputCreateRequest`
- `ModelOutputRecord`
- `ModelOutputSegment`
- `StructuredOutputValidation`
- `ResponseCandidate`
- `ToolIntentCandidate`
- `OutputGovernanceRequest`
- `OutputGovernanceRun`
- `ModelOutputQuery`
- `ModelOutputQueryResult`

## Safety Rules

- Raw model output is hashed and not stored by default.
- Redacted output must not contain hidden reasoning, chain-of-thought, raw
  prompt echoes, raw headers, or secrets.
- Tool intents are captured and blocked by default.
- Response candidates are local proposals only until promoted through policy
  and response verification.
- Structured validation is deterministic and generic.

## API

- `POST /brain/model-outputs`
- `GET /brain/model-outputs/{model_output_id}`
- `POST /brain/model-outputs/query`
- `DELETE /brain/model-outputs/{model_output_id}`
- `POST /brain/model-outputs/{model_output_id}/govern`
- `GET /brain/model-outputs/governance/{output_governance_id}`
- `GET /brain/model-outputs/{model_output_id}/segments`
- `POST /brain/model-outputs/{model_output_id}/validate-structured`
- `GET /brain/model-outputs/response-candidates`
- `POST /brain/model-outputs/response-candidates/{response_candidate_id}/promote`
- `GET /brain/model-outputs/tool-intents`
- `POST /brain/model-outputs/tool-intents/{tool_intent_id}/reject`

## Visual Telemetry

Generic events include `model_output_received`, `model_output_parsed`,
`model_output_governed`, `model_output_blocked`,
`structured_output_validated`, `response_candidate_created`,
`response_candidate_promoted`, `tool_intent_captured`, and
`tool_intent_blocked`.

Generic visual nodes include `model_output`, `output_segment`,
`structured_validation`, `response_candidate`, `tool_intent`, and
`output_governance`.
