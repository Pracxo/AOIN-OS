# Controlled Model Gateway Implementation

AION-233 implements the AION-232-SRI-0002 provider-neutral model gateway as a local deterministic simulation control plane. It composes the AION-231 authenticated local secure-runtime foundation through `brain.think.simulate`, requires parent guard outcome `allow_simulation`, and accepts only simulated parent dispatch status `simulated`.

The only provider is `deterministic-reference-provider`. The only models are `reference-text-sim-v1` and `reference-json-sim-v1`. They are not live model providers, use no provider SDK, open no network endpoint, read no credential, create no authorization header, and create no live model session.

Retained records store fingerprints, byte counts, deterministic token estimates, status, classification, provenance, audit, and integrity evidence. Raw prompt bodies, raw context, raw response bodies, hidden reasoning, provider raw payloads, credentials, tokens, tool calls, function calls, connector requests, and production actions are not retained.

AION-232-SRI-0002 remains active for AION-234 to evaluate and close. v0.2 remains unreleased.
