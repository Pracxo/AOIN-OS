# ADR 0212: Single OpenAI Responses API Synthetic Live-Provider Pilot

## Status

Accepted for AION-248 implementation under `AION-247-AI-0002`.

## Decision

AION OS implements one controlled live-provider pilot using OpenAI Responses API only. The provider is `openai`, the API family is `responses`, the endpoint is `POST https://api.openai.com/v1/responses`, and the selected model is `gpt-5.6-terra`.

Installed Brain API source contains contracts and local validation only. The uninstalled runner owns the live boundary and may read `OPENAI_API_KEY` from the process environment only at execution time.

## Consequences

The pilot can prove real external inference while preserving AION decision authority. Provider output remains untrusted, is never promoted to memory or knowledge, and cannot execute tools, connectors, source mutation, Git mutation or production effects.

The implementation adds no provider dependency, no API route, no migration, no workflow and no persistent runtime. AION-249 remains required for closeout and successor authorization decisions.
