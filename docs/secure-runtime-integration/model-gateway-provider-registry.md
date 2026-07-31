# Model Gateway Provider Registry

The provider registry is an immutable copy-on-write in-memory registry. It contains exactly one provider manifest: `deterministic-reference-provider`.

The provider manifest is credential-free, endpoint-free, SDK-free, streaming-disabled, network-disabled, and simulation-only. Unknown providers, credential fields, endpoint fields, SDK configuration, provider-network state, and substitution attempts fail closed.
