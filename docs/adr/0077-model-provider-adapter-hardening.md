# 0077: Model Provider Adapter Hardening

## Status

Accepted

## Context

AION Brain v0.1 has a model gateway, prompt governance, model input manifests,
model output governance, tool intent guard, grounding, audit/provenance, and
operator review. Real model provider calls remain disabled.

## Decision

AION adds Model Provider Adapter Hardening and Prompt Egress Guard as a local
provider-readiness layer.

Provider profiles are metadata only. Prompt egress preview does not transmit
prompts. Provider simulation does not invoke models. Provider readiness does not
enable providers.

## Reason

AION needs a safe provider-readiness form before any future provider activation
or credential design work.

## Consequences

Future model provider work must pass prompt, output, grounding, audit, policy,
and operator gates. Provider SDKs, credentials, external calls, prompt
transmission, and tool execution stay out of AION-086.

## Constraints

- no credentials
- no provider SDKs
- no external calls
- no tool execution
- no raw prompt persistence
- no provider enablement
