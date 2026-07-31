# Model Gateway Model Registry

The model registry is an immutable copy-on-write in-memory registry. It contains exactly two model manifests: `reference-text-sim-v1` and `reference-json-sim-v1`.

`reference-text-sim-v1` supports text simulation. `reference-json-sim-v1` supports text simulation and structured JSON simulation. Both are local deterministic simulation components with no provider call, network effect, credential effect, tool calling, function calling, connector effect, or production effect.
