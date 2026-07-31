# Model Gateway Contracts

The AION-233 contracts live in `services/brain-api/src/aion_brain/contracts/model_gateway.py`. Every new retained contract uses strict Pydantic v2 validation with forbidden extras, hidden validation inputs, UTC timestamps, bounded identifiers, canonical SHA-256 fingerprints, deterministic sorting, and no retained raw prompt or raw response content.

The contract set covers component binding, authorization envelopes, provider manifests, model manifests, capability profiles, sessions, message and context normalization, budgets, request envelopes, idempotency, routing, fallback, retry, circuit breaker state, guards, reference-provider requests and responses, structured-output schemas, response validation, untrusted classification, provenance, audit, observability, health, integrity, diagnostics, incidents, operator review, and evidence bundles.

No contract authorizes provider calls, network egress, credentials, tokens, tool calls, function calls, connector execution, production writes, memory writes, policy mutation, belief mutation, source rewrite, deployment, or model training.
