# Shadow-Mode Reference Adapters

AION-178 exposes only an injected `ShadowReferenceAdapter` protocol. The
default adapter is disabled and fails closed with
`shadow_reference_adapter_disabled`.

The in-memory adapter is for tests and explicit offline operator runs only. It
uses caller-supplied immutable snapshots, exact reference kind and ID matching,
exact fingerprint matching, and no fallback lookup. It performs no filesystem
discovery, database lookup, network request, connector call, provider call,
source mutation, Git mutation, or runtime registration.

Reference snapshots contain redacted summaries, redacted metrics, source
fingerprints, a source record version, and UTC timestamps. They contain no raw
payload and cannot influence runtime response, retrieval, planning, policy, or
tool selection.
