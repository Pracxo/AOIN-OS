# AION-243 Operator Console Bundle

The Operator Console candidate bundle is a deterministic archive of the current
static console assets from the immutable source snapshot.

The runner builds the archive twice with fixed metadata and requires matching
SHA-256 values. The retained artifact is
`operator-console/aion-operator-console-0.2.0-rc.1.tar.gz`.

No frontend dependencies, package files, build tools or runtime UI publication
are introduced.
