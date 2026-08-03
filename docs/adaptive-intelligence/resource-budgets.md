# Adaptive Intelligence Resource Budgets

AION-246 must fail closed if any limit is missing, renamed, or changed.

## Non-Zero Limits

- maximum provider manifests: `8`
- maximum model manifests: `32`
- maximum model capability records: `256`
- maximum routing policies: `100`
- maximum routing rules: `500`
- maximum request templates: `100`
- maximum structured output schemas: `100`
- maximum fixture sessions: `20`
- maximum fixture requests per session: `100`
- maximum total fixture requests: `1000`
- maximum messages per request: `256`
- maximum request payload bytes: `2097152`
- maximum response payload bytes: `4194304`
- maximum declared context tokens: `2000000`
- maximum declared output tokens: `262144`
- maximum concurrency: `4`
- maximum retry attempts: `3`
- maximum circuit breaker records: `100`
- maximum operator review items: `200`
- maximum evidence records: `10000`
- maximum evidence bytes: `104857600`
- maximum local fixture pilots: `20`

## Required Zero Limits

Provider calls, public network calls, external egress calls, DNS resolutions, provider credential generation/read/persistence, provider token read/persistence, authorization-header creation, raw prompt persistence, raw response persistence, hidden-reasoning records, memory writes, verified-knowledge promotions, belief mutations, connector calls, tool executions, background cycles, scheduled provider calls, source mutations, Git operations, runtime-created pull requests, automatic merges, production deployments, and model-weight changes all have maximum `0`.
