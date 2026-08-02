# AION-243 Candidate Security Review

The candidate build remains local and offline after the pinned Hatchling
toolchain bootstrap. Docker builds use no network, no registry login, no pull,
no push, no BuildKit secrets and no SSH forwarding.

Committed evidence is redacted and must not contain absolute candidate paths,
private keys, credentials, tokens, raw artifact bytes, raw source contents,
image layers or production endpoints.
