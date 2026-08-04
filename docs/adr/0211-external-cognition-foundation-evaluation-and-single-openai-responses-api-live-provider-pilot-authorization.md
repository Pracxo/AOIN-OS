# 0211: External-Cognition Foundation Evaluation and Single OpenAI Responses API Live-Provider Pilot Authorization

Status: Accepted

## Context

AION-246 merged a provider-neutral external-cognition gateway foundation with deterministic fixture evidence and no live-provider effects. AION-247 must evaluate that foundation before any live-provider pilot can be considered.

## Decision

AION-247 accepts the AION-ECGPE-001 PASS decision and creates AION-247-AI-0002 as the only active Adaptive Intelligence implementation authorization. The authorization permits AION-248 to implement one operator-invoked OpenAI Responses API synthetic text pilot using one explicitly selected GPT-5.6 model, one `OPENAI_API_KEY` process-environment credential, `POST https://api.openai.com/v1/responses`, `store=false`, `background=false`, `stream=false`, no provider tools, no files and no previous-response continuation.

## Consequences

AION-248 may implement the bounded pilot, but AION-247 creates no live-provider source. Provider output remains untrusted and cannot write memory, promote knowledge, execute tools, invoke connectors or trigger autonomous action. AION-249 must independently evaluate the pilot before internet research or broader adaptive-intelligence work is considered.
