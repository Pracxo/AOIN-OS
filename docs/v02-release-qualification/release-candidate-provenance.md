# AION-243 Candidate Provenance

Candidate provenance is retained as an in-toto Statement v1 with a SLSA-style
predicate.

The provenance binds the candidate label, source commit, source-tree
fingerprint, source archive, frozen base image, Brain API wheel, SDK artifacts,
Operator Console bundle, Dockerfile fingerprint, build-context fingerprint,
Docker server fingerprint, Buildx fingerprint, offline Hatchling toolchain and
network-disabled build parameters.
